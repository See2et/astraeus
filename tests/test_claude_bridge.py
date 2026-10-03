"""Handoff boundaries verified locally; no Claude inference runs in these tests."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/astraeus/scripts"
sys.path.insert(0, str(SCRIPTS))
import claude_bridge as b


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.repo, self.wt = self.base / "repo", self.base / "worktree"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        self.git(self.repo, "config", "user.name", "Test")
        (self.repo / "ui").mkdir()
        (self.repo / "ui/index.html").write_text("before\n")
        (self.repo / "other.txt").write_text("before\n")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-qm", "base")
        self.git(self.repo, "worktree", "add", "-qb", "design", str(self.wt))
        self.control = self.base / "control"
        self.control.mkdir()
        self.req = self.control / "request.json"
        self.state = self.control / "state.json"
        self.data = dict(task_id="design-1", scope="ui-implementation", model="sonnet",
                         owned_paths=["ui"], goal="Improve UI", constraints=["No publication"],
                         checks=["python -m unittest"])
        self.req.write_text(json.dumps(self.data))
        self.real_run = b.a.run
        self.calls = []
        self.records = []
        self.mock = patch.object(b.a, "run", side_effect=self.cli_run)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def git(self, root, *args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def cli_run(self, argv, cwd=None):
        if argv[0] != "claude":
            return self.real_run(argv, cwd=cwd)
        self.calls.append(argv)
        if argv == ["claude", "--help"]:
            return "--bg --safe-mode --session-id --settings --setting-sources --permission-mode --allowedTools --disallowedTools --tools --add-dir --strict-mcp-config --mcp-config"
        if argv == ["claude", "agents", "--help"]:
            return "--json --all"
        if argv == ["claude", "stop", "--help"]:
            return "Usage: claude stop <id>"
        if argv == ["claude", "agents", "--json", "--all"]:
            return json.dumps(self.records)
        if "--bg" in argv or argv[:2] == ["claude", "stop"]:
            return "started"
        raise AssertionError(argv)

    def start(self):
        output = b.start(self.req, self.wt, self.state, True, True)
        self.metadata = output["state"]
        self.records = [dict(sessionId=self.metadata["session_id"], id="abcd1234", cwd=str(self.wt), state="done", status="idle")]
        return output

    def report(self, **updates):
        data = dict(schema_version=1, kind="implementation", task_id="design-1",
                    target_id=self.metadata["target_id"], status="complete", summary="UI improved",
                    changed_files=["ui/index.html"], checks=[dict(command="python -m unittest",
                    outcome="passed", evidence="Suite passed")], remaining=[])
        data.update(updates)
        report = Path(self.metadata["report"])
        report.write_text(json.dumps(data))
        now = self.state.stat().st_mtime_ns + 1_000_000
        os.utime(report, ns=(now, now))
        return report

    def test_explicit_authorization_and_clean_linked_worktree_required(self):
        with self.assertRaisesRegex(ValueError, "user-requested"):
            b.start(self.req, self.wt, self.state)
        with self.assertRaisesRegex(ValueError, "linked"):
            b.start(self.req, self.repo, self.state, True)
        (self.wt / "dirty").write_text("dirty")
        with self.assertRaisesRegex(ValueError, "clean"):
            b.start(self.req, self.wt, self.state, True)
        self.assertFalse(any("--bg" in c for c in self.calls))

    def test_preview_does_not_dispatch_or_create_metadata(self):
        output = b.start(self.req, self.wt, self.state, True)
        self.assertFalse(output["applied"])
        self.assertFalse(self.state.exists())
        self.assertFalse(any("--bg" in c for c in self.calls))
        argv = output["argv"]
        self.assertNotIn("--worktree", argv)
        self.assertNotIn("--print", argv)
        self.assertIn("dontAsk", argv)
        self.assertIn("Bash(git push *)", argv)
        self.assertIn("Agent", argv)
        self.assertIn("Bash(python -m unittest)", argv)

    def test_only_exact_full_session_and_bound_cwd_are_used(self):
        self.start()
        self.records.append(dict(sessionId="unrelated", cwd="/other", status="running", secret="unrelated"))
        self.assertNotIn("secret", json.dumps(b.status(self.state)))
        self.records[0]["cwd"] = str(self.repo)
        with self.assertRaisesRegex(ValueError, "cwd"):
            b.status(self.state)
        self.records = []
        with self.assertRaisesRegex(ValueError, "missing"):
            b.status(self.state)

    def test_missing_unknown_and_modified_handoff_are_rejected(self):
        with self.assertRaises(OSError):
            b.status(self.state)
        self.state.write_text('{"version":99}')
        with self.assertRaisesRegex(ValueError, "unknown"):
            b.status(self.state)
        self.state.unlink()
        self.start()
        self.data["goal"] = "Changed goal"
        self.req.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "changed"):
            b.status(self.state)

    def test_result_binds_schema_status_checks_and_actual_git_delta(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        report = self.report()
        output = b.result(self.state)
        self.assertFalse(output["final_acceptance"])
        self.assertNotEqual(output["review_target_id"], output["dispatch_target_id"])
        self.records[0]["state"] = "working"
        with self.assertRaisesRegex(ValueError, "not completed"):
            b.result(self.state)
        self.records[0]["state"] = "done"
        report.write_text('{"task_id":')
        with self.assertRaises(ValueError):
            b.result(self.state)
        self.report(target_id="other")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            b.result(self.state)
        self.report(checks=[dict(command="python -m unittest", outcome="failed", evidence="Failed")])
        with self.assertRaisesRegex(ValueError, "checks"):
            b.result(self.state)
        self.report(changed_files=[])
        with self.assertRaisesRegex(ValueError, "changed_files"):
            b.result(self.state)
        self.report(remaining=["Visual review pending"])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            b.result(self.state)

    def test_scope_escape_in_untracked_committed_and_reverted_changes_rejected(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        self.report()
        (self.wt / "other.txt").write_text("escaped\n")
        self.git(self.wt, "add", "other.txt")
        self.git(self.wt, "commit", "-qm", "escape")
        with self.assertRaisesRegex(ValueError, "out-of-ownership"):
            b.result(self.state)
        self.git(self.wt, "revert", "--no-edit", "HEAD")
        with self.assertRaisesRegex(ValueError, "out-of-ownership"):
            b.result(self.state)

    def test_owned_commit_is_included_and_symlink_escape_is_refused(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        self.git(self.wt, "add", "ui/index.html")
        self.git(self.wt, "commit", "-qm", "design")
        self.report()
        self.assertEqual(b.result(self.state)["changed_files"], ["ui/index.html"])
        (self.wt / "ui/escape").symlink_to(self.base / "outside")
        self.report(changed_files=["ui/index.html", "ui/escape"])
        with self.assertRaisesRegex(ValueError, "scope escape"):
            b.result(self.state)

    def test_missing_stale_report_and_untracked_escape(self):
        self.start()
        with self.assertRaisesRegex(ValueError, "missing"):
            b.result(self.state)
        (self.wt / "ui/index.html").write_text("after\n")
        report = self.report()
        os.utime(report, ns=(1, 1))
        with self.assertRaisesRegex(ValueError, "stale"):
            b.result(self.state)
        self.report()
        (self.wt / "unowned").write_text("escape")
        with self.assertRaisesRegex(ValueError, "out-of-ownership"):
            b.result(self.state)

    def test_staged_only_and_ignored_scope_escape_is_refused(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        self.report()
        (self.wt / "other.txt").write_text("staged escape\n")
        self.git(self.wt, "add", "other.txt")
        (self.wt / "other.txt").write_text("before\n")
        with self.assertRaisesRegex(ValueError, "out-of-ownership"):
            b.result(self.state)
        self.git(self.wt, "reset", "-q", "HEAD", "other.txt")
        exclude = Path(self.real_run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=self.wt).strip())
        if not exclude.is_absolute():
            exclude = self.wt / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("ignored-build\n")
        (self.wt / "ignored-build").write_text("escape")
        with self.assertRaisesRegex(ValueError, "out-of-ownership"):
            b.result(self.state)

    def test_cancel_never_stops_global_or_unrelated_sessions(self):
        self.start()
        preview = b.cancel(self.state)
        self.assertEqual(preview["argv"], ["claude", "stop", "abcd1234"])
        self.assertFalse(any(c[:2] == ["claude", "stop"] and "--help" not in c for c in self.calls))
        b.cancel(self.state, True)
        self.assertEqual(self.calls[-1], preview["argv"])


if __name__ == "__main__":
    unittest.main()
