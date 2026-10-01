#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.23,<5"]
# ///
"""Local policy/result validation and narrowly scoped Codex plugin maintenance.

No inference, auth, telemetry scraping, or independent session management.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

PLUGIN = Path(__file__).resolve().parents[1]
DEFAULTS = {
    "schema_version": 1,
    "allowed_models": ["gpt-6.1-sol", "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"],
    "review_limit": 2,
    "require_review_globs": [],
    "assurance": "reported",
}
BEGIN = "<!-- astraeus:begin -->"
END = "<!-- astraeus:end -->"
BLOCK = f"""{BEGIN}
Apply the installed Astraeus orchestration policy autonomously to project work in
every project: use $astraeus:orchestrate. Simple tasks should remain solo; delegate
only useful bounded work, and require independent review for consequential changes.
Keep implementation and ordinary verification with the same owner. Prioritize Astra
for design judgment and visual acceptance. Root owns routing and final acceptance.
If Astraeus is unavailable, disclose that once when relevant; do not invent its tools
or install anything automatically. Explicit user instructions remain authoritative.
{END}"""


def parse_json(content):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(content, object_pairs_hook=unique)


def read_json(path):
    return parse_json(Path(path).read_bytes())


def run(args, *, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"command failed ({result.returncode}): {args!r}\n{result.stderr.strip()}")
    return result.stdout


def policy(path=None):
    data = {} if path is None else tomllib.loads(Path(path).read_text())
    unknown = data.keys() - DEFAULTS.keys()
    if unknown:
        raise ValueError(f"unknown policy keys: {sorted(unknown)}")
    result = DEFAULTS | data
    if type(result["schema_version"]) is not int or result["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if type(result["review_limit"]) is not int or not 1 <= result["review_limit"] <= 2:
        raise ValueError("review_limit must be 1 or 2; two total reviewer dispatches is the maximum")
    if result["assurance"] not in ("reported", "strict"):
        raise ValueError("assurance must be reported or strict")
    for key in ("allowed_models", "require_review_globs"):
        values = result[key]
        if not isinstance(values, list) or any(not isinstance(x, str) or not x.strip() for x in values):
            raise ValueError(f"{key} must be a list of nonempty strings")
        if len(set(values)) != len(values):
            raise ValueError(f"{key} contains duplicates")
    if not result["allowed_models"]:
        raise ValueError("allowed_models must not be empty")
    return result


def validate_receipt(receipt, assurance, option="--receipt"):
    if receipt:
        r = read_json(receipt)
        if not isinstance(r, dict) or set(r) != {"requested", "observed", "source"}:
            raise ValueError(f"{option} requires requested, observed, source")
        requested, observed = r["requested"], r["observed"]
        if not isinstance(requested, dict) or set(requested) != {"model", "effort"}:
            raise ValueError(f"{option} requested must contain model and effort")
        if not isinstance(observed, dict) or set(observed) != {"model", "effort", "sandbox"}:
            raise ValueError(f"{option} observed must contain model, effort, sandbox")
        if any(not isinstance(v, str) or not v.strip() for v in requested.values()):
            raise ValueError(f"{option} requested model/effort must be nonempty strings")
        if any(v is not None and (not isinstance(v, str) or not v.strip()) for v in observed.values()):
            raise ValueError(f"{option} observed fields must be nonempty strings or null")
        if not isinstance(r["source"], str) or not r["source"].strip():
            raise ValueError(f"{option} needs a host evidence source")
        for key in ("model", "effort"):
            if observed[key] is not None and observed[key] != requested[key]:
                raise ValueError(f"{option} host-observed {key} differs from request")
        if assurance == "strict" and (
            any(observed[k] is None for k in ("model", "effort"))
            or observed["sandbox"] != "read-only"
        ):
            raise ValueError(f"strict assurance needs observed model/effort and read-only sandbox in {option}")
    elif assurance == "strict":
        raise ValueError(f"strict assurance requires {option} with host evidence")


def load_result(path, kind, task_id, target_id, content=None):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise ValueError("jsonschema is required; run this script with uv run or install jsonschema") from exc
    data = read_json(path) if content is None else parse_json(content)
    schema = read_json(PLUGIN / "schemas" / f"{kind}.json")
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
    if errors:
        raise ValueError("invalid contract: " + "; ".join(e.message for e in errors[:5]))
    if data["task_id"] != task_id or data["target_id"] != target_id:
        raise ValueError("task or target mismatch: result is not for the expected current work")
    if kind == "review":
        blocking = data["violations"] or data["bugs"]
        if data["verdict"] == "pass" and (
            data["status"] != "complete" or blocking or data["unresolved"]
            or not data["evidence"] or not data["checked_scope"]
        ):
            raise ValueError("pass requires complete status, evidence, coverage, and no blocking/unresolved issues")
        if data["verdict"] == "changes_required" and not blocking:
            raise ValueError("changes_required needs a concrete violation or bug")
    return data


def validate_adjudication(data, source):
    expected_refs = [
        f"{field}/{index}"
        for field in ("violations", "bugs", "suggestions", "unresolved")
        for index in range(len(source[field]))
    ]
    actual_refs = [decision["ref"] for decision in data["decisions"]]
    duplicates = sorted({ref for ref in actual_refs if actual_refs.count(ref) > 1})
    if duplicates:
        raise ValueError(f"duplicate source finding dispositions: {duplicates}")
    missing = sorted(set(expected_refs) - set(actual_refs))
    unknown = sorted(set(actual_refs) - set(expected_refs))
    if missing or unknown:
        raise ValueError(f"source finding dispositions mismatch; missing={missing}, unknown={unknown}")

    actions = [decision["action"] for decision in data["decisions"]]
    source_incomplete = (
        source["status"] != "complete"
        or source["verdict"] == "inconclusive"
        or bool(source["unresolved"])
        or not source["evidence"]
        or not source["checked_scope"]
    )
    adjudication_incomplete = (
        data["status"] != "complete"
        or bool(data["unresolved"])
        or not data["evidence"]
        or not data["checked_scope"]
    )
    pending = source_incomplete or adjudication_incomplete or any(
        action in ("investigate", "human_decision") for action in actions
    )

    if pending and data["verdict"] != "inconclusive":
        raise ValueError("pending or incomplete adjudication requires an inconclusive verdict")
    if data["verdict"] == "accept" and any(action != "reject" for action in actions):
        raise ValueError("accept requires every source finding to be rejected with justification")
    if data["verdict"] == "changes_required" and "fix" not in actions:
        raise ValueError("changes_required requires at least one fix decision")


def validate_result(path, kind, task_id, target_id, accept=False, assurance="reported", receipt=None,
                    review_result=None, review_receipt=None):
    if accept and kind != "adjudication":
        raise ValueError("--accept is only for adjudication; validate review input without --accept")
    if kind != "adjudication" and (review_result is not None or review_receipt is not None):
        raise ValueError("--review-result and --review-receipt are only for adjudication")
    if kind == "adjudication" and review_result is None:
        raise ValueError("adjudication requires --review-result")

    data = load_result(path, kind, task_id, target_id)
    if kind == "adjudication":
        source_bytes = Path(review_result).read_bytes()
        source = load_result(review_result, "review", task_id, target_id, source_bytes)
        expected_hash = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
        if data["review_sha256"] != expected_hash:
            raise ValueError("review hash mismatch: adjudication is not bound to the supplied review bytes")
        validate_adjudication(data, source)

    if accept and data["verdict"] != "accept":
        raise ValueError("adjudication does not accept; do not accept")
    validate_receipt(receipt, assurance)
    if kind == "adjudication":
        validate_receipt(review_receipt, assurance, "--review-receipt")
    return {"valid": True, "acceptance_checks_passed": bool(accept), "result": data}


def target_id(repo):
    repo = Path(repo).resolve()
    actual = Path(run(["git", "rev-parse", "--show-toplevel"], cwd=repo).strip()).resolve()
    if actual != repo:
        raise ValueError("--repo must identify the Git repository root")
    def git(*args, optional=False):
        p = subprocess.run(["git", *args], cwd=repo, capture_output=True)
        if p.returncode and not optional:
            raise ValueError(p.stderr.decode(errors="replace"))
        return p.stdout if p.returncode == 0 else b"unborn"
    digest = hashlib.sha256()
    def add(label, value):
        digest.update(label + b"\0" + str(len(value)).encode() + b"\0" + value)
    add(b"head", git("rev-parse", "--verify", "HEAD", optional=True))
    for label, args in ((b"index", ["--cached"]), (b"worktree", [])):
        add(label, git("diff", "--binary", "--no-ext-diff", "--no-textconv", *args))
    for raw in sorted(filter(None, git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"))):
        path = repo / os.fsdecode(raw)
        add(b"path", raw)
        if path.is_symlink():
            add(b"symlink", os.fsencode(os.readlink(path)))
        else:
            add(b"mode", str(path.stat().st_mode & 0o777).encode())
            add(b"file", path.read_bytes())
    return "sha256:" + digest.hexdigest()


def atomic_write(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"refusing symlink destination: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        if path.exists():
            os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def activation(path, action, apply=False):
    path = Path(path).expanduser()
    if path.is_symlink():
        raise ValueError("refusing to modify symlinked global instructions")
    old = path.read_bytes().decode("utf-8") if path.exists() else ""
    if old.count(BEGIN) != old.count(END) or old.count(BEGIN) > 1:
        raise ValueError("ambiguous Astraeus markers; inspect manually")
    if BEGIN in old:
        start, end = old.index(BEGIN), old.index(END) + len(END)
        if end < start:
            raise ValueError("out-of-order Astraeus markers")
        owned = old[start:end]
        separator = re.match(re.escape(BEGIN) + r"\n<!-- astraeus:separator-newlines=([012]) -->\n", owned)
        if not separator:
            raise ValueError("managed block lacks separator ownership; inspect manually")
        count = int(separator.group(1))
        expected = BLOCK.replace(BEGIN, BEGIN + f"\n<!-- astraeus:separator-newlines={count} -->", 1)
        if owned != expected or (count and old[max(0, start-count):start] != "\n" * count):
            raise ValueError("managed block was edited or belongs to another version; inspect manually")
        # The embedded count records exactly which leading separator bytes we own.
        new = old if action == "enable" else old[:start-count] + old[end:]
    else:
        count = 0 if not old or old.endswith("\n\n") else (1 if old.endswith("\n") else 2)
        owned = BLOCK.replace(BEGIN, BEGIN + f"\n<!-- astraeus:separator-newlines={count} -->", 1)
        new = old + "\n" * count + owned if action == "enable" else old
    if apply and new != old:
        if old:
            backup = path.with_name(path.name + ".astraeus-backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
            # Never overwrite an earlier backup.
            with backup.open("xb") as f:
                f.write(old.encode("utf-8"))
            os.chmod(backup, 0o600)
        atomic_write(path, new)
    return {"action": action, "path": str(path), "changed": new != old, "applied": apply,
            "instruction": "Start a fresh Codex session. Check AGENTS.override.md and project precedence."}


def marketplace(repo):
    repo = Path(repo).expanduser().resolve()
    data = read_json(repo / ".agents/plugins/marketplace.json")
    name = data.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("invalid marketplace identifier")
    entries = [p for p in data.get("plugins", []) if p.get("name") == "astraeus"]
    if len(entries) != 1 or entries[0].get("source") != {"source": "local", "path": "./plugins/astraeus"}:
        raise ValueError("expected exactly one local Astraeus source at ./plugins/astraeus")
    manifest = repo / "plugins/astraeus/.codex-plugin/plugin.json"
    if manifest.resolve().is_relative_to(repo) is False:
        raise ValueError("plugin source escapes marketplace root")
    m = read_json(manifest)
    if m.get("name") != "astraeus" or not isinstance(m.get("version"), str):
        raise ValueError("invalid Astraeus manifest")
    return repo, name, manifest


def plugin_action(repo, action, apply=False):
    repo, name, manifest = marketplace(repo)
    selector = f"astraeus@{name}"
    listed = json.loads(run(["codex", "plugin", "marketplace", "list", "--json"]))
    sources = [s for s in listed.get("marketplaces", []) if s.get("name") == name]
    if len(sources) > 1:
        raise ValueError("ambiguous marketplace name")
    if action != "install" and not sources:
        raise ValueError("marketplace not installed; run plugin install first")
    if sources:
        s = sources[0]
        if s.get("marketplaceSource", {}).get("sourceType") != "local" or Path(s["root"]).resolve() != repo:
            raise ValueError("installed source is not this local checkout; do not refresh/reset a different source")
    commands = []
    if action == "install" and not sources:
        commands.append(["codex", "plugin", "marketplace", "add", str(repo)])
    if action in ("reset", "remove"):
        commands.append(["codex", "plugin", "remove", selector, "--json"])
    if action != "remove":
        commands.append(["codex", "plugin", "add", selector, "--json"])
    outputs = []
    if apply:
        if action == "refresh":
            data = read_json(manifest)
            base = data["version"].split("+", 1)[0]
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            data["version"] = base + "+codex." + stamp
            atomic_write(manifest, json.dumps(data, indent=2) + "\n")
        for command in commands:
            outputs.append(run(command))
    return {"action": action, "source": str(repo), "selector": selector, "commands": commands,
            "cachebuster": action == "refresh", "applied": apply, "outputs": outputs,
            "next": "Start a fresh session; existing sessions do not hot-reload. For Git sources use official marketplace upgrade, then plugin add."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Read-only local capabilities and policy; no model calls")
    doctor.add_argument("--config", type=Path)
    target = sub.add_parser("target", help="Hash current Git source state; freeze writers first")
    target.add_argument("--repo", type=Path, default=Path.cwd())
    val = sub.add_parser("validate-result")
    val.add_argument("result", type=Path)
    val.add_argument("--kind", choices=["exploration", "research", "implementation", "review", "adjudication"], required=True)
    val.add_argument("--task-id", required=True)
    val.add_argument("--target-id", required=True)
    val.add_argument("--accept", action="store_true")
    val.add_argument("--assurance", choices=["reported", "strict"], default="reported")
    val.add_argument("--receipt", type=Path)
    val.add_argument("--review-result", type=Path)
    val.add_argument("--review-receipt", type=Path)
    act = sub.add_parser("activation", help="Preview/apply only the Astraeus block in global instructions")
    act.add_argument("action", choices=["enable", "disable"])
    act.add_argument("--file", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "AGENTS.md")
    act.add_argument("--apply", action="store_true")
    plug = sub.add_parser("plugin", help="Local checkout operations through official Codex commands")
    plug.add_argument("action", choices=["install", "refresh", "reset", "remove"])
    plug.add_argument("--repo", type=Path, required=True)
    plug.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = {"policy": policy(args.config), "codex_version": run(["codex", "--version"]).strip(),
                      "plugin_path": str(PLUGIN), "runtime_model": "unknown", "runtime_effort": "unknown",
                      "note": "Local CLI presence is not evidence of model access or active-session plugin loading."}
        elif args.command == "target":
            print(target_id(args.repo))
            return 0
        elif args.command == "validate-result":
            result = validate_result(args.result, args.kind, args.task_id, args.target_id, args.accept,
                                     args.assurance, args.receipt, args.review_result, args.review_receipt)
        elif args.command == "activation":
            result = activation(args.file, args.action, args.apply)
        else:
            result = plugin_action(args.repo, args.action, args.apply)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"astraeus: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
