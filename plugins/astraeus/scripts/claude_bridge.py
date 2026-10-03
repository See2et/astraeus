#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.23,<5"]
# ///
"""Explicit design-only handoff to the installed Claude background lifecycle.

This is a permission-constrained CLI handoff, not a filesystem sandbox or final
acceptance. Metadata belongs to root; Claude owns only the declared work paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import re
import sys
import os
import subprocess
import uuid

import astraeus as a


SCOPES = {"design-direction", "ui-implementation"}
DENY = ["Agent", "Task", "Bash(git push *)", "Bash(git -C * push *)",
        "Bash(gh *)", "Bash(glab *)", "Bash(curl *)", "Bash(wget *)"]


def dispatch_call(argv, root):
    return subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)


def launch_id(output):
    # Documented --bg output, not a cwd/time heuristic or a private session database.
    plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
    matches = re.findall(r"^backgrounded · ([a-f0-9]{8})(?: · [^\r\n]*)?\s*$", plain, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("unknown or ambiguous background launch output; inspect launch.json, do not relaunch")
    return matches[0]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(worktree, *args):
    return a.run(["git", *args], cwd=worktree).strip()


def paths(values):
    if not isinstance(values, list) or not values:
        raise ValueError("owned_paths must be a nonempty list")
    for value in values:
        if not isinstance(value, str) or not value or value != str(PurePosixPath(value)):
            raise ValueError("owned_paths must be normalized relative paths")
        if PurePosixPath(value).is_absolute() or any(p in ("..", ".git") for p in PurePosixPath(value).parts):
            raise ValueError("owned_paths cannot escape the worktree or own Git metadata")
        if any(c in value for c in "*?[]()\\\n\r") or value == ".":
            raise ValueError("owned_paths must be literal paths, not patterns")
    if len(set(values)) != len(values):
        raise ValueError("duplicate owned_paths")
    return values


def request(path):
    data = a.read_json(path)
    required = {"task_id", "scope", "model", "owned_paths", "goal", "constraints", "checks"}
    if not isinstance(data, dict) or not required <= data.keys() or data.keys() - required - {"effort"}:
        raise ValueError("request requires task_id, scope, model, owned_paths, goal, constraints, checks; optional effort")
    for key in ("task_id", "scope", "model", "goal"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if data["scope"] not in SCOPES:
        raise ValueError("Claude is limited to explicit design-direction or ui-implementation requests")
    if "effort" in data and data["effort"] not in ("low", "medium", "high", "xhigh", "max"):
        raise ValueError("unsupported effort")
    for key in ("constraints", "checks"):
        if not isinstance(data[key], list) or any(not isinstance(x, str) or not x.strip() for x in data[key]):
            raise ValueError(f"{key} must be an array of nonempty strings")
    if len(set(data["checks"])) != len(data["checks"]):
        raise ValueError("duplicate checks")
    for command in data["checks"]:
        if any(c in command for c in "*?[]();&|$`<>\n\r"):
            raise ValueError("checks must be exact simple commands, without shell operators or permission globs")
        if shlex.split(command)[0] in ("gh", "glab", "curl", "wget", "rm") or re.search(r"\bgit\s+.*\b(push|commit)\b", command):
            raise ValueError("publication, deletion and commit commands cannot be verification checks")
    paths(data["owned_paths"])
    return data


def worktree(path):
    root = Path(path).resolve(strict=True)
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("worktree must be its Git root")
    if not (root / ".git").is_file():
        raise ValueError("a dedicated linked Git worktree is required; main worktree is disallowed")
    entries = git(root, "worktree", "list", "--porcelain").split("\n\n")
    registered = [Path(line[9:]).resolve() for entry in entries for line in entry.splitlines() if line.startswith("worktree ")]
    if root not in registered or not registered or root == registered[0]:
        raise ValueError("worktree must be a registered linked worktree")
    return root


def contained(root, name):
    resolved = (root / name).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"scope escape through symlink: {name}")
    return resolved


def capabilities(cancel=False, effort=False):
    if cancel:
        if "stop <id>" not in a.run(["claude", "stop", "--help"]):
            raise ValueError("installed Claude has no supported exact-session stop command")
        return
    help_text = a.run(["claude", "--help"])
    required = ["--bg", "--session-id", "--settings", "--setting-sources", "--permission-mode",
                "--allowedTools", "--disallowedTools", "--tools", "--add-dir", "--strict-mcp-config", "--mcp-config", "--safe-mode"]
    if effort:
        required.append("--effort")
    if any(flag not in help_text for flag in required):
        raise ValueError("installed Claude lacks required safe background CLI capabilities")
    agents = a.run(["claude", "agents", "--help"])
    if "--json" not in agents or "--all" not in agents:
        raise ValueError("installed Claude lacks agents --json --all")


def start(request_path, worktree_path, state_path, user_requested=False, apply=False):
    if not user_requested:
        raise ValueError("--user-requested is required: Claude must be explicitly requested by the user")
    reqpath, statepath = Path(request_path).resolve(strict=True), Path(state_path).absolute()
    if statepath.is_symlink() or statepath.exists():
        raise ValueError("state must be a new non-symlink handoff file")
    statepath = statepath.resolve()
    root = worktree(worktree_path)
    req = request(reqpath)
    if any(c in str(root) + str(reqpath) + str(statepath) for c in "*?[]()\n\r"):
        raise ValueError("worktree/control paths cannot contain permission-rule metacharacters")
    if statepath.parent != reqpath.parent or reqpath.parent.is_relative_to(root):
        raise ValueError("request and state must share a dedicated control directory outside the worktree")
    if set(reqpath.parent.iterdir()) != {reqpath}:
        raise ValueError("control directory must initially contain only the request file")
    for name in req["owned_paths"]:
        contained(root, name)
    if git(root, "status", "--porcelain", "--untracked-files=all", "--ignored"):
        raise ValueError("dedicated worktree must start clean, including ignored files")
    capabilities(effort="effort" in req)
    session_id = str(uuid.uuid4())
    report = statepath.parent / "result.json"
    if reqpath in (report, Path(str(report) + ".tmp")) or statepath in (report, Path(str(report) + ".tmp")) or statepath == reqpath:
        raise ValueError("request, state and result.json must be distinct")
    target = a.target_id(root)
    launchpath = statepath.parent / "launch.json"
    stoppath = statepath.parent / "stop.json"
    if any(p in (reqpath, statepath) for p in (launchpath, stoppath)):
        raise ValueError("launch.json and stop.json are reserved for lifecycle evidence")
    metadata = dict(version=2, report_finalizer="root", request=str(reqpath), request_sha256=digest(reqpath),
                    worktree=str(root), base_head=git(root, "rev-parse", "HEAD"),
                    target_id=target, task_id=req["task_id"], session_id=session_id, report=str(report))
    allows = ["Read", "Glob", "Grep"]
    for name in req["owned_paths"]:
        absolute = contained(root, name)
        allows += [f"Edit(/{absolute})", f"Edit(/{absolute}/**)"]
    allows += [f"Edit(/{report}.tmp)"]
    allows += [f"Bash({command})" for command in req["checks"]]
    denies = DENY + [f"Edit(/{reqpath})", f"Edit(/{statepath})", f"Edit(/{launchpath})", f"Edit(/{stoppath})", f"Edit(/{report})"]
    settings = {"permissions": {"defaultMode": "dontAsk", "allow": allows, "deny": denies}}
    schema = a.read_json(a.PLUGIN / "schemas" / "implementation.json")
    prompt = ("Implement only this explicitly authorized design task in the current existing linked worktree. "
              "Do not create another worktree, commit, push, open a PR, publish, or dispatch additional agents. "
              "Do not edit the request/state or anything outside owned_paths, except the report. "
              "Run the declared checks; failed or denied checks must be reported truthfully. "
              "Finish by writing the implementation JSON report to " + str(report) + ".tmp. "
              "Root owns validation and atomic publication to result.json; do not rename or write result.json. "
              "Report complete only when the authorized work and required checks are complete, with no remaining work. "
              "An empty checks request needs checks: []; do not invent a not_run check. "
              "Use task_id=" + json.dumps(req["task_id"]) + " and dispatch target_id=" + json.dumps(target) +
              "; this is a dispatch binding, not final acceptance. changed_files must list every actual change. "
              "Report schema: " + json.dumps(schema) + "\nRequest: " + json.dumps(req))
    argv = ["claude", "--bg", "--safe-mode", "--session-id", session_id, "--model", req["model"],
            "--permission-mode", "dontAsk", "--setting-sources", "", "--settings", json.dumps(settings),
            "--tools", "Read,Edit,Write,Glob,Grep,Bash", "--allowedTools", *allows,
            "--disallowedTools", *denies, "--add-dir", str(statepath.parent),
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    if "effort" in req:
        argv += ["--effort", req["effort"]]
    argv += ["--", prompt]
    if apply:
        # Keep the binding even if dispatch fails; root must inspect, never retry blindly.
        a.atomic_write(statepath, json.dumps(metadata, indent=2) + "\n")
        launched = dispatch_call(argv, root)
        evidence = dict(version=1, requested_session_id=session_id, returncode=launched.returncode,
                        stdout=launched.stdout, stderr=launched.stderr)
        a.atomic_write(launchpath, json.dumps(evidence, indent=2) + "\n")
        if launched.returncode:
            raise ValueError(f"background launch failed ({launched.returncode}); see {launchpath}\n{launched.stderr.strip()}")
        launch_id(launched.stdout)
    return {"applied": apply, "state": metadata, "argv": argv, "final_acceptance": False}


def load_state(path):
    state = a.read_json(path)
    keys = {"version", "request", "request_sha256", "worktree", "base_head", "target_id", "task_id", "session_id", "report"}
    if isinstance(state, dict) and state.get("version") == 2:
        keys.add("report_finalizer")
    if not isinstance(state, dict) or set(state) != keys or state["version"] not in (1, 2):
        raise ValueError("unknown or malformed handoff state")
    if state["version"] == 2 and state["report_finalizer"] != "root":
        raise ValueError("unknown report finalizer")
    if any(not isinstance(state[key], str) or not state[key] for key in keys - {"version"}):
        raise ValueError("malformed handoff state fields")
    if str(uuid.UUID(state["session_id"])) != state["session_id"]:
        raise ValueError("state needs a full session UUID")
    statepath = Path(path).resolve(strict=True)
    reqpath, report = Path(state["request"]), Path(state["report"])
    root = worktree(state["worktree"])
    if reqpath.parent != statepath.parent or report != statepath.parent / "result.json" or statepath.parent.is_relative_to(root):
        raise ValueError("invalid control-directory binding")
    req = request(reqpath)
    if digest(reqpath) != state["request_sha256"] or req["task_id"] != state["task_id"]:
        raise ValueError("request changed since dispatch")
    for name in req["owned_paths"]:
        contained(root, name)
    if git(root, "merge-base", state["base_head"], "HEAD") != state["base_head"]:
        raise ValueError("worktree history no longer descends from dispatch base")
    return state, req, root


def session(state, root):
    capabilities()
    records = a.parse_json(a.run(["claude", "agents", "--json", "--all"], cwd=root))
    if not isinstance(records, list):
        raise ValueError("unknown agents JSON format")
    if state["version"] == 2:
        launchpath = Path(state["report"]).parent / "launch.json"
        if launchpath.is_symlink():
            raise ValueError("symlinked launch evidence")
        evidence = a.read_json(launchpath)
        if (not isinstance(evidence, dict) or set(evidence) != {"version", "requested_session_id", "returncode", "stdout", "stderr"}
                or evidence["version"] != 1 or type(evidence["returncode"]) is not int or evidence["returncode"] != 0
                or evidence["requested_session_id"] != state["session_id"]
                or not all(isinstance(evidence[k], str) for k in ("stdout", "stderr"))):
            raise ValueError("failed or mismatched launch evidence")
        exact_id = launch_id(evidence["stdout"])
        matches = [r for r in records if isinstance(r, dict) and r.get("id") == exact_id]
    else:
        matches = [r for r in records if isinstance(r, dict) and
                   (r.get("sessionId", r.get("session_id", r.get("id"))) == state["session_id"])]
    if len(matches) != 1:
        raise ValueError("exact session is missing or ambiguous; no unrelated sessions returned")
    found = matches[0]
    cwd = found.get("cwd")
    if not isinstance(cwd, str) or Path(cwd).resolve() != root:
        raise ValueError("session cwd does not match dedicated worktree")
    stop_id = found.get("id")
    if not isinstance(stop_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", stop_id):
        raise ValueError("unknown exact-session stop ID")
    if sum(isinstance(r, dict) and r.get("id") == stop_id for r in records) != 1:
        raise ValueError("ambiguous exact-session stop ID")
    actual_id = found.get("sessionId", found.get("session_id")) if state["version"] == 2 else state["session_id"]
    if state["version"] == 2:
        if not isinstance(actual_id, str) or str(uuid.UUID(actual_id)) != actual_id or not actual_id.startswith(stop_id + "-"):
            raise ValueError("launch short ID does not bind a full session UUID")
    return {"session_id": actual_id, "requested_session_id": state["session_id"], "id": stop_id, "cwd": str(root),
            "state": found.get("state"), "status": found.get("status"), "pid": found.get("pid"), "waitingFor": found.get("waitingFor")}


def status(state_path):
    state, _, root = load_state(state_path)
    return session(state, root)


def acknowledged_stop(state, observed):
    """Affirmative root-captured stop evidence for CLI records without live status."""
    if observed["state"] != "stopped" or observed["status"] is not None or observed["pid"] is not None:
        return False
    path = Path(state["report"]).parent / "stop.json"
    if path.is_symlink() or not path.is_file():
        return False
    receipt = a.read_json(path)
    keys = {"version", "requested_session_id", "session_id", "id", "returncode", "stdout", "stderr"}
    return (isinstance(receipt, dict) and set(receipt) == keys and receipt["version"] == 1
            and receipt["requested_session_id"] == state["session_id"]
            and receipt["session_id"] == observed["session_id"] and receipt["id"] == observed["id"]
            and type(receipt["returncode"]) is int and receipt["returncode"] == 0
            and isinstance(receipt["stderr"], str) and isinstance(receipt["stdout"], str)
            and receipt["stdout"].strip() == f"stopped {observed['id']}")


def result(state_path, apply=False):
    state, req, root = load_state(state_path)
    observed = session(state, root)
    completed = ((observed["state"] in ("done", "stopped") and observed["status"] == "idle")
                 or acknowledged_stop(state, observed)) if state["version"] == 2 else observed["state"] == "done"
    if not completed:
        raise ValueError("session is not completed (or its status format is unknown)")
    report = Path(state["report"])
    pending = state["version"] == 2 and not report.exists() and not report.is_symlink()
    candidate = Path(str(report) + ".tmp") if pending else report
    if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_mtime_ns <= Path(state_path).stat().st_mtime_ns:
        raise ValueError("missing, symlinked or stale report")
    original = candidate.read_bytes()
    data = a.load_result(candidate, "implementation", state["task_id"], state["target_id"])
    if data["status"] != "complete" or data["remaining"]:
        raise ValueError("implementation report is incomplete")
    checks = {c["command"]: c for c in data["checks"]}
    if len(checks) != len(data["checks"]) or any(c["outcome"] != "passed" for c in data["checks"]) or any(c not in checks for c in req["checks"]):
        raise ValueError("required checks missing, failed or not run")
    delta = set(filter(None, git(root, "diff", "--name-only", "--no-renames", "-z", state["base_head"]).split("\0")))
    delta.update(filter(None, git(root, "diff", "--cached", "--name-only", "--no-renames", "-z", state["base_head"]).split("\0")))
    delta.update(filter(None, git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    delta.update(filter(None, git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split("\0")))
    # Include committed changes even if subsequently reverted: ownership applies to
    # the entire branch handed back, not only its current checkout.
    history = git(root, "log", "--format=", "--name-only", "--no-renames", "-z", f'{state["base_head"]}..HEAD')
    delta.update(p.lstrip("\n") for p in history.split("\0") if p.lstrip("\n"))
    for changed in delta:
        contained(root, changed)
        if not any(changed == own or changed.startswith(own + "/") for own in req["owned_paths"]):
            raise ValueError(f"out-of-ownership Git delta: {changed}")
    if set(data["changed_files"]) != delta or len(data["changed_files"]) != len(delta):
        raise ValueError("report changed_files does not match actual committed/unstaged/untracked delta")
    target = a.target_id(root)
    if apply and pending:
        # Publish exactly the validated bytes; never upgrade blocked/incomplete reports.
        if session(state, root) != observed or a.target_id(root) != target or candidate.is_symlink() or candidate.read_bytes() != original:
            raise ValueError("session, source target or report changed during collection")
        # Exclusive creation avoids overwriting another final report, including a symlink.
        os.link(candidate, report, follow_symlinks=False)
        candidate.unlink()
    return {"valid": True, "final_acceptance": False, "dispatch_target_id": state["target_id"],
            "review_target_id": target, "changed_files": sorted(delta), "result": data,
            "report_finalized": not pending or apply, "applied": apply and pending}


def cancel(state_path, apply=False):
    state, _, root = load_state(state_path)
    observed = session(state, root)
    capabilities(cancel=True)
    argv = ["claude", "stop", observed["id"]]
    if apply:
        if state["version"] == 2:
            path = Path(state["report"]).parent / "stop.json"
            if path.is_symlink():
                raise ValueError("symlinked stop evidence")
            stopped = dispatch_call(argv, root)
            receipt = dict(version=1, requested_session_id=state["session_id"], session_id=observed["session_id"],
                           id=observed["id"], returncode=stopped.returncode, stdout=stopped.stdout, stderr=stopped.stderr)
            a.atomic_write(path, json.dumps(receipt, indent=2) + "\n")
            if stopped.returncode or stopped.stdout.strip() != f"stopped {observed['id']}":
                raise ValueError(f"exact-session stop was not acknowledged; see {path}\n{stopped.stderr.strip()}")
        else:
            a.run(argv, cwd=root)
    return {"applied": apply, "argv": argv, "session": observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    launch = sub.add_parser("start")
    launch.add_argument("--request", required=True)
    launch.add_argument("--worktree", required=True)
    launch.add_argument("--state", required=True)
    launch.add_argument("--user-requested", action="store_true")
    launch.add_argument("--apply", action="store_true")
    for command in ("status", "result", "cancel"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--state", required=True)
        if command in ("cancel", "result"):
            cmd.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "start":
            output = start(args.request, args.worktree, args.state, args.user_requested, args.apply)
        elif args.command in ("cancel", "result"):
            output = globals()[args.command](args.state, args.apply)
        else:
            output = globals()[args.command](args.state)
        print(json.dumps(output, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
