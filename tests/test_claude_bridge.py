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
        self.launch = patch.object(b, "dispatch_call", side_effect=self.dispatch_call)
        self.launch.start()
        self.addCleanup(self.launch.stop)

    def dispatch_call(self, argv, root):
        self.calls.append(argv)
        if argv[:2] == ["claude", "stop"]:
            return subprocess.CompletedProcess(argv, 0, "stopped " + argv[2] + "\n", "")
        return subprocess.CompletedProcess(argv, 0, "Starting background service…\nbackgrounded · abcd1234\n  claude attach abcd1234\n", "")

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
        self.records = [dict(sessionId="abcd1234-0000-4000-8000-000000000000", id="abcd1234", cwd=str(self.wt), state="done", status="idle")]
        return output

    def report(self, **updates):
        data = dict(schema_version=1, kind="implementation", task_id="design-1",
                    target_id=self.metadata["target_id"], status="complete", summary="UI improved",
                    changed_files=["ui/index.html"], checks=[dict(command="python -m unittest",
                    outcome="passed", evidence="Suite passed")], remaining=[])
        data.update(updates)
        report = Path(self.metadata["report"] + ".tmp")
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

    def test_launch_evidence_binds_actual_id_without_rewriting_requested_uuid(self):
        self.start()
        evidence = self.control / "launch.json"
        self.assertEqual(json.loads(evidence.read_text())["returncode"], 0)
        observed = b.status(self.state)
        self.assertNotEqual(observed["session_id"], self.metadata["session_id"])
        self.assertEqual(observed["requested_session_id"], self.metadata["session_id"])
        self.assertEqual(json.loads(self.state.read_text())["session_id"], self.metadata["session_id"])
        self.records.append(dict(self.records[0]))
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            b.status(self.state)
        self.records = [dict(self.records[0], sessionId="ffffffff-0000-4000-8000-000000000000")]
        with self.assertRaisesRegex(ValueError, "does not bind"):
            b.status(self.state)

    def test_failed_launch_retains_stdout_stderr_state_and_exit_code(self):
        self.launch.stop()
        with patch.object(b, "dispatch_call", return_value=subprocess.CompletedProcess([], 17, "partial", "Workspace not trusted")):
            with self.assertRaisesRegex(ValueError, "Workspace not trusted"):
                b.start(self.req, self.wt, self.state, True, True)
        evidence = json.loads((self.control / "launch.json").read_text())
        self.assertEqual((evidence["returncode"], evidence["stdout"], evidence["stderr"]), (17, "partial", "Workspace not trusted"))
        self.assertTrue(self.state.exists())
        with self.assertRaisesRegex(ValueError, "failed or mismatched"):
            b.status(self.state)

    def test_unknown_launch_output_never_binds_by_cwd(self):
        self.launch.stop()
        with patch.object(b, "dispatch_call", return_value=subprocess.CompletedProcess([], 0, "unknown format", "warning")):
            with self.assertRaisesRegex(ValueError, "launch output"):
                b.start(self.req, self.wt, self.state, True, True)
        self.assertEqual(json.loads((self.control / "launch.json").read_text())["stderr"], "warning")

    def test_launch_parser_refuses_ambiguity_and_accepts_documented_named_output(self):
        self.assertEqual(b.launch_id("\x1b[32mbackgrounded · abcd1234 · design\x1b[0m\n"), "abcd1234")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            b.launch_id("backgrounded · abcd1234\nbackgrounded · abcd1234\n")

    def test_root_finalizes_only_valid_complete_frozen_report_without_changing_bytes(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        candidate = self.report()
        original = candidate.read_bytes()
        final = Path(self.metadata["report"])
        self.assertFalse(b.result(self.state)["report_finalized"])
        self.assertFalse(final.exists())
        self.records[0]["state"] = "blocked"
        with self.assertRaisesRegex(ValueError, "not completed"):
            b.result(self.state, True)
        self.records[0]["state"] = "stopped"
        self.report(status="blocked")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            b.result(self.state, True)
        self.report()
        self.assertTrue(b.result(self.state, True)["report_finalized"])
        self.assertEqual(final.read_bytes(), original)
        self.assertFalse(candidate.exists())

    def test_finalization_refuses_writer_state_change_and_report_symlink(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        candidate = self.report()
        observed = b.status(self.state)
        with patch.object(b, "session", side_effect=[observed, dict(observed, state="working", status="busy")]):
            with self.assertRaisesRegex(ValueError, "changed during"):
                b.result(self.state, True)
        self.assertFalse(Path(self.metadata["report"]).exists())
        outside = self.base / "outside-report.json"
        candidate.rename(outside)
        candidate.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlinked"):
            b.result(self.state, True)

    def test_v2_finalization_requires_supported_affirmative_nonbusy_status(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        candidate = self.report()
        final = Path(self.metadata["report"])
        self.records[0]["state"] = "stopped"
        for value in (None, "unknown", "busy", "waiting"):
            with self.subTest(status=value):
                if value is None:
                    self.records[0].pop("status", None)
                else:
                    self.records[0]["status"] = value
                with self.assertRaisesRegex(ValueError, "not completed"):
                    b.result(self.state, True)
                self.assertTrue(candidate.exists())
                self.assertFalse(final.exists())
        self.records[0]["status"] = "idle"
        self.assertTrue(b.result(self.state, True)["report_finalized"])

    def test_new_dispatch_keeps_metadata_and_final_report_root_owned(self):
        self.start()
        argv = next(c for c in self.calls if "--bg" in c)
        settings = json.loads(argv[argv.index("--settings") + 1])["permissions"]
        self.assertIn(f"Edit(/{self.control / 'launch.json'})", settings["deny"])
        self.assertIn(f"Edit(/{self.control / 'stop.json'})", settings["deny"])
        self.assertIn(f"Edit(/{self.metadata['report']})", settings["deny"])
        self.assertIn(f"Edit(/{self.metadata['report']}.tmp)", settings["allow"])
        self.assertFalse(any(rule.startswith("Bash(mv ") for rule in settings["allow"]))

    def test_legacy_state_still_requires_requested_uuid_and_final_report(self):
        self.start()
        legacy = dict(self.metadata, version=1)
        legacy.pop("report_finalizer")
        self.state.write_text(json.dumps(legacy))
        with self.assertRaisesRegex(ValueError, "missing"):
            b.status(self.state)
        self.records[0]["sessionId"] = legacy["session_id"]
        self.assertEqual(b.status(self.state)["session_id"], legacy["session_id"])
        (self.wt / "ui/index.html").write_text("after\n")
        self.report()
        with self.assertRaisesRegex(ValueError, "missing"):
            b.result(self.state, True)
        Path(self.metadata["report"] + ".tmp").rename(self.metadata["report"])
        self.records[0].pop("status")
        self.assertTrue(b.result(self.state)["report_finalized"])

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

    def test_exact_successful_stop_receipt_allows_cli_stopped_record_without_status(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        candidate = self.report()
        self.records[0]["state"] = "stopped"
        self.records[0].pop("status")
        with self.assertRaisesRegex(ValueError, "not completed"):
            b.result(self.state, True)
        b.cancel(self.state, True)
        receipt = self.control / "stop.json"
        captured = json.loads(receipt.read_text())
        self.assertEqual(captured["stdout"], "stopped abcd1234\n")
        for updates in ({"status": "unknown"}, {"pid": 123}, {"state": "done"}):
            original = dict(self.records[0])
            self.records[0].update(updates)
            with self.assertRaisesRegex(ValueError, "not completed"):
                b.result(self.state, True)
            self.records[0] = original
        for updates in ({"returncode": 1}, {"stdout": "stopped unrelated"}, {"session_id": "ffffffff-0000-4000-8000-000000000000"}):
            receipt.write_text(json.dumps(captured | updates))
            with self.assertRaisesRegex(ValueError, "not completed"):
                b.result(self.state, True)
        receipt.write_text(json.dumps(captured))
        original_bytes = candidate.read_bytes()
        self.assertTrue(b.result(self.state, True)["report_finalized"])
        self.assertEqual(Path(self.metadata["report"]).read_bytes(), original_bytes)

    def test_failed_or_unknown_stop_ack_is_captured_but_never_authorizes_publication(self):
        self.start()
        (self.wt / "ui/index.html").write_text("after\n")
        self.report()
        self.records[0]["state"] = "stopped"
        self.records[0].pop("status")
        for returncode, stdout in ((1, "stopped abcd1234"), (0, "unrecognized output")):
            with patch.object(b, "dispatch_call", return_value=subprocess.CompletedProcess([], returncode, stdout, "diagnostic")):
                with self.assertRaisesRegex(ValueError, "not acknowledged"):
                    b.cancel(self.state, True)
            receipt = json.loads((self.control / "stop.json").read_text())
            self.assertEqual((receipt["returncode"], receipt["stdout"], receipt["stderr"]), (returncode, stdout, "diagnostic"))
            with self.assertRaisesRegex(ValueError, "not completed"):
                b.result(self.state, True)


if __name__ == "__main__":
    unittest.main()
