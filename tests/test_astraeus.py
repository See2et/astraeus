import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("astraeus", ROOT / "plugins/astraeus/scripts/astraeus.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def review():
    return dict(schema_version=1, kind="review", task_id="t1", target_id="state1",
                status="complete", summary="Checked parser boundary.", verdict="pass",
                violations=[], bugs=[], suggestions=[], checked_scope=["parse.py:parse"],
                evidence=["Empty input is rejected at parse.py:12; regression check passed."], unresolved=[])


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "result.json"

    def check(self, data, **kw):
        self.path.write_text(json.dumps(data))
        return a.validate_result(self.path, "review", "t1", "state1", **kw)

    def test_pass_with_optional_suggestions(self):
        data = review()
        data["suggestions"] = ["Optional: shorten the helper name."]
        self.assertTrue(self.check(data, accept=True)["acceptance_checks_passed"])

    def test_inconclusive_is_valid_but_not_acceptable(self):
        data = review()
        data.update(verdict="inconclusive", unresolved=["Database was unavailable."])
        self.assertFalse(self.check(data)["acceptance_checks_passed"])
        with self.assertRaises(ValueError):
            self.check(data, accept=True)

    def test_false_passes_rejected(self):
        modifications = [dict(status="blocked"), dict(evidence=[]), dict(checked_scope=[]),
                         dict(unresolved=["Missing evidence"]), dict(extra="ignored?"),
                         dict(target_id="stale"), dict(task_id="other"),
                         dict(bugs=[dict(location="p:1", claim="crashes", evidence="repro")])]
        for change in modifications:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(review() | change, accept=True)

    def test_duplicate_json_keys_rejected(self):
        self.path.write_text('{"verdict":"pass","verdict":"inconclusive"}')
        with self.assertRaises(ValueError):
            a.read_json(self.path)

    def test_changes_required_needs_concrete_finding(self):
        with self.assertRaises(ValueError):
            self.check(review() | dict(verdict="changes_required"))

    def test_strict_requires_matching_host_evidence(self):
        with self.assertRaises(ValueError):
            self.check(review(), accept=True, assurance="strict")
        receipt = Path(self.tmp.name) / "host.json"
        data = dict(requested=dict(model="gpt-6-astra", effort="high"),
                    observed=dict(model="gpt-6-astra", effort="high", sandbox="read-only"),
                    source="host response thread 123")
        receipt.write_text(json.dumps(data))
        self.check(review(), accept=True, assurance="strict", receipt=receipt)
        for change in (dict(model=None), dict(model="gpt-5.6-sol"), dict(sandbox="workspace-write")):
            bad = copy.deepcopy(data)
            bad["observed"].update(change)
            receipt.write_text(json.dumps(bad))
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(review(), accept=True, assurance="strict", receipt=receipt)

    def test_all_schemas_and_examples(self):
        from jsonschema import Draft202012Validator, FormatChecker
        for kind in ("review", "exploration", "research", "implementation"):
            schema = a.read_json(a.PLUGIN / "schemas" / f"{kind}.json")
            Draft202012Validator.check_schema(schema)
            example = a.read_json(ROOT / "examples" / f"{kind}.json")
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)


class PolicyTests(unittest.TestCase):
    def test_example_matches_defaults(self):
        self.assertEqual(a.policy(ROOT / "astraeus.example.toml"), a.DEFAULTS)

    def test_invalid_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "config.toml"
            for text in ('review_limit = 0', 'review_limit = true', 'review_limit = 11',
                         'review_limit = 3', 'review_limit = 10',
                         'allowed_models = []', 'unknown = 1', 'assurance = "magic"',
                         'allowed_models = ["x", "x"]', 'schema_version = true'):
                p.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    a.policy(p)


class ActivationTests(unittest.TestCase):
    def test_idempotent_preserves_existing_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "AGENTS.md"
            original = "# Personal\r\nKeep this line.\r\n"
            p.write_bytes(original.encode())
            a.activation(p, "enable")
            self.assertEqual(p.read_bytes(), original.encode())
            a.activation(p, "enable", True)
            first = p.read_bytes()
            self.assertTrue(first.startswith(original.encode()))
            a.activation(p, "enable", True)
            self.assertEqual(p.read_bytes(), first)
            a.activation(p, "disable", True)
            self.assertEqual(p.read_bytes(), original.encode())
            self.assertNotIn(a.BEGIN.encode(), p.read_bytes())
            self.assertEqual(len(list(Path(tmp).glob("*.astraeus-backup-*"))), 2)

    def test_exact_roundtrip_for_each_separator_and_preserves_later_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "AGENTS.md"
            for original in (b"", b"text", b"text\n", b"text\n\n", b"text\r\n", b"text\r\n\r\n"):
                p.write_bytes(original)
                a.activation(p, "enable", True)
                a.activation(p, "disable", True)
                self.assertEqual(p.read_bytes(), original)
            p.write_text("existing")
            a.activation(p, "enable", True)
            with p.open("a") as f:
                f.write("\nUser added later.\n")
            a.activation(p, "disable", True)
            self.assertEqual(p.read_text(), "existing\nUser added later.\n")

    def test_ambiguous_or_edited_blocks_and_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "AGENTS.md"
            for bad in (a.BEGIN, a.END + a.BEGIN, a.BLOCK + a.BLOCK, a.BLOCK.replace("Simple", "Complex")):
                p.write_text(bad)
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    a.activation(p, "disable", True)
                self.assertEqual(p.read_text(), bad)
            link = Path(tmp) / "link"
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                a.activation(link, "enable", True)


class TargetTests(unittest.TestCase):
    def test_tracks_staged_untracked_and_unstaged_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text(".astraeus/\n")
            initial = a.target_id(root)
            (root / "file.txt").write_text("one")
            untracked = a.target_id(root)
            self.assertNotEqual(initial, untracked)
            subprocess.run(["git", "add", "file.txt"], cwd=root, check=True)
            staged = a.target_id(root)
            self.assertNotEqual(untracked, staged)
            (root / "file.txt").write_text("two")
            edited = a.target_id(root)
            self.assertNotEqual(staged, edited)
            (root / ".astraeus").mkdir()
            (root / ".astraeus/result.json").write_text("{}")
            self.assertEqual(edited, a.target_id(root))
            (root / "sub").mkdir()
            with self.assertRaises(ValueError):
                a.target_id(root / "sub")


class PluginTests(unittest.TestCase):
    def test_source_mismatch_rejected_even_in_preview(self):
        other = dict(marketplaces=[dict(name="astraeus", root="/tmp/other",
                                       marketplaceSource=dict(sourceType="local"))])
        with patch.object(a, "run", return_value=json.dumps(other)):
            with self.assertRaises(ValueError):
                a.plugin_action(ROOT, "reset")

    def test_git_source_not_silently_changed_to_local(self):
        other = dict(marketplaces=[dict(name="astraeus", root=str(ROOT),
                                       marketplaceSource=dict(sourceType="git"))])
        with patch.object(a, "run", return_value=json.dumps(other)):
            with self.assertRaises(ValueError):
                a.plugin_action(ROOT, "install")

    def test_preview_only_produces_narrow_commands(self):
        source = dict(marketplaces=[dict(name="astraeus", root=str(ROOT),
                                        marketplaceSource=dict(sourceType="local"))])
        with patch.object(a, "run", return_value=json.dumps(source)) as mocked:
            result = a.plugin_action(ROOT, "reset")
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(result["commands"], [["codex", "plugin", "remove", "astraeus@astraeus", "--json"],
                                               ["codex", "plugin", "add", "astraeus@astraeus", "--json"]])


if __name__ == "__main__":
    unittest.main()
