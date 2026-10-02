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


def decision(ref, action="reject"):
    return dict(ref=ref, action=action,
                basis="The user request and repository contract determine whether this finding is required.",
                evidence="The cited requirement and implementation were checked directly.",
                rationale="This disposition follows from the checked authority and evidence.")


def adjudication(review_path, decisions=None, **changes):
    data = dict(schema_version=1, kind="adjudication", task_id="t1", target_id="state1",
                status="complete", summary="Adjudicated every source finding.", verdict="accept",
                review_sha256="sha256:" + a.hashlib.sha256(review_path.read_bytes()).hexdigest(),
                decisions=[] if decisions is None else decisions,
                checked_scope=["Original request and review findings"],
                evidence=["Compared every finding with the controlling requirement."], unresolved=[])
    data.update(changes)
    return data


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "result.json"
        self.review_path = Path(self.tmp.name) / "review.json"

    def check_review(self, data, **kw):
        self.path.write_text(json.dumps(data))
        return a.validate_result(self.path, "review", "t1", "state1", **kw)

    def check_adjudication(self, data, source, **kw):
        self.review_path.write_text(json.dumps(source))
        if data is None:
            data = adjudication(self.review_path)
        self.path.write_text(json.dumps(data))
        return a.validate_result(self.path, "adjudication", "t1", "state1",
                                 review_result=self.review_path, **kw)

    def test_review_pass_with_optional_suggestions_is_valid_input(self):
        data = review()
        data["suggestions"] = ["Optional: shorten the helper name."]
        self.assertFalse(self.check_review(data)["acceptance_checks_passed"])
        self.assertTrue(self.check_review(data, accept=True)["acceptance_checks_passed"])

    def test_review_inconclusive_is_valid_input(self):
        data = review()
        data.update(verdict="inconclusive", unresolved=["Database was unavailable."])
        self.assertFalse(self.check_review(data)["acceptance_checks_passed"])

    def test_false_review_passes_rejected(self):
        modifications = [dict(status="blocked"), dict(evidence=[]), dict(checked_scope=[]),
                         dict(unresolved=["Missing evidence"]), dict(extra="ignored?"),
                         dict(target_id="stale"), dict(task_id="other"),
                         dict(bugs=[dict(location="p:1", claim="crashes", evidence="repro")])]
        for change in modifications:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check_review(review() | change, accept=True)

    def test_duplicate_json_keys_rejected(self):
        self.path.write_text('{"verdict":"pass","verdict":"inconclusive"}')
        with self.assertRaises(ValueError):
            a.read_json(self.path)

    def test_changes_required_needs_concrete_finding(self):
        with self.assertRaises(ValueError):
            self.check_review(review() | dict(verdict="changes_required"))

    def test_rejected_invented_requirement_permits_acceptance(self):
        source = review() | dict(
            verdict="changes_required",
            violations=[dict(location="README.md:1", claim="Add an unrequested badge.",
                             evidence="The badge is absent.")])
        self.review_path.write_text(json.dumps(source))
        data = adjudication(self.review_path, [decision("violations/0")])
        result = self.check_adjudication(data, source, accept=True)
        self.assertTrue(result["acceptance_checks_passed"])

    def test_fix_decision_requires_changes_even_without_accept_flag(self):
        source = review() | dict(
            verdict="changes_required",
            bugs=[dict(location="parse.py:12", claim="Empty input crashes.", evidence="Reproduced.")])
        self.review_path.write_text(json.dumps(source))
        contradictory = adjudication(self.review_path, [decision("bugs/0", "fix")])
        with self.assertRaisesRegex(ValueError, "accept requires"):
            self.check_adjudication(contradictory, source)
        required = contradictory | dict(verdict="changes_required")
        self.assertFalse(self.check_adjudication(required, source)["acceptance_checks_passed"])
        with self.assertRaisesRegex(ValueError, "does not accept"):
            self.check_adjudication(required, source, accept=True)

    def test_every_source_item_has_exactly_one_disposition(self):
        source = review() | dict(
            verdict="changes_required",
            violations=[dict(location="a:1", claim="v", evidence="e")],
            bugs=[dict(location="b:2", claim="b", evidence="e")],
            suggestions=["s"], unresolved=["u"])
        self.review_path.write_text(json.dumps(source))
        complete = [decision("violations/0"), decision("bugs/0"),
                    decision("suggestions/0"), decision("unresolved/0")]
        cases = {
            "omitted": complete[:-1],
            "duplicate": complete + [decision("bugs/0")],
            "unknown": complete[:-1] + [decision("unresolved/1")],
        }
        for name, decisions in cases.items():
            data = adjudication(self.review_path, decisions, verdict="inconclusive",
                                unresolved=["Source review remains unresolved."])
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check_adjudication(data, source)

    def test_source_hash_task_and_target_are_bound(self):
        source = review()
        self.review_path.write_text(json.dumps(source))
        data = adjudication(self.review_path)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.check_adjudication(data | dict(review_sha256="sha256:" + "0" * 64), source)
        for change in (dict(task_id="other"), dict(target_id="stale")):
            changed_source = source | change
            self.review_path.write_text(json.dumps(changed_source))
            changed_data = data | dict(
                review_sha256="sha256:" + a.hashlib.sha256(self.review_path.read_bytes()).hexdigest())
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "task or target mismatch"):
                self.check_adjudication(changed_data, changed_source)

    def test_incomplete_source_review_cannot_be_waived(self):
        finding = [dict(location="p:1", claim="Needs change.", evidence="Observed.")]
        variations = [
            dict(status="blocked", verdict="changes_required", violations=finding),
            dict(verdict="inconclusive", violations=finding),
            dict(verdict="changes_required", violations=finding, unresolved=["Authority unknown."]),
            dict(verdict="changes_required", violations=finding, evidence=[]),
            dict(verdict="changes_required", violations=finding, checked_scope=[]),
        ]
        for change in variations:
            source = review() | change
            self.review_path.write_text(json.dumps(source))
            data = adjudication(self.review_path, [decision("violations/0")])
            if source["unresolved"]:
                data["decisions"].append(decision("unresolved/0"))
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "inconclusive"):
                self.check_adjudication(data, source)

    def test_pending_decisions_require_inconclusive(self):
        source = review() | dict(suggestions=["Consider another design."])
        self.review_path.write_text(json.dumps(source))
        for action in ("investigate", "human_decision"):
            data = adjudication(self.review_path, [decision("suggestions/0", action)])
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, "inconclusive"):
                self.check_adjudication(data, source)
            data.update(verdict="inconclusive", unresolved=["Decision remains pending."])
            self.check_adjudication(data, source)

    def test_strict_acceptance_requires_both_host_receipts(self):
        source = review()
        self.review_path.write_text(json.dumps(source))
        data = adjudication(self.review_path)
        receipt_data = dict(requested=dict(model="gpt-6-astra", effort="high"),
                            observed=dict(model="gpt-6-astra", effort="high", sandbox="read-only"),
                            source="host response thread 123")
        receipt = Path(self.tmp.name) / "adjudicator-host.json"
        review_receipt = Path(self.tmp.name) / "reviewer-host.json"
        receipt.write_text(json.dumps(receipt_data))
        review_receipt.write_text(json.dumps(receipt_data))
        with self.assertRaisesRegex(ValueError, "requires --receipt"):
            self.check_adjudication(data, source, accept=True, assurance="strict")
        with self.assertRaisesRegex(ValueError, "requires --review-receipt"):
            self.check_adjudication(data, source, accept=True, assurance="strict", receipt=receipt)
        self.check_adjudication(data, source, accept=True, assurance="strict", receipt=receipt,
                                review_receipt=review_receipt)
        for option, path in (("--receipt", receipt), ("--review-receipt", review_receipt)):
            for change in (dict(model=None), dict(model="gpt-5.6-sol"),
                           dict(sandbox="workspace-write")):
                bad = copy.deepcopy(receipt_data)
                bad["observed"].update(change)
                path.write_text(json.dumps(bad))
                with self.subTest(option=option, change=change), self.assertRaisesRegex(ValueError, option):
                    self.check_adjudication(data, source, accept=True, assurance="strict", receipt=receipt,
                                            review_receipt=review_receipt)
                path.write_text(json.dumps(receipt_data))

    def test_review_acceptance_requires_pass(self):
        finding = dict(location="p:1", claim="crashes", evidence="repro")
        for change in (dict(verdict="changes_required", bugs=[finding]),
                       dict(verdict="inconclusive", unresolved=["Missing evidence"])):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "does not pass"):
                self.check_review(review() | change, accept=True)

    def test_strict_review_acceptance_requires_reviewer_receipt(self):
        with self.assertRaisesRegex(ValueError, "requires --receipt"):
            self.check_review(review(), accept=True, assurance="strict")
        receipt = Path(self.tmp.name) / "reviewer-host.json"
        receipt.write_text(json.dumps(dict(
            requested=dict(model="gpt-6-astra", effort="high"),
            observed=dict(model="gpt-6-astra", effort="high", sandbox="read-only"),
            source="host response thread 123")))
        self.assertTrue(self.check_review(review(), accept=True, assurance="strict",
                                         receipt=receipt)["acceptance_checks_passed"])

    def test_adjudication_only_arguments_are_rejected_for_review(self):
        with self.assertRaisesRegex(ValueError, "only for adjudication"):
            self.check_review(review(), review_result=self.review_path)
        self.path.write_text(json.dumps(review()))
        with self.assertRaisesRegex(ValueError, "requires --review-result"):
            a.validate_result(self.path, "adjudication", "t1", "state1")

    def test_all_schemas_and_examples(self):
        from jsonschema import Draft202012Validator, FormatChecker
        for kind in ("review", "adjudication", "exploration", "research", "implementation"):
            schema = a.read_json(a.PLUGIN / "schemas" / f"{kind}.json")
            Draft202012Validator.check_schema(schema)
            example = a.read_json(ROOT / "examples" / f"{kind}.json")
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
        result = a.validate_result(ROOT / "examples/adjudication.json", "adjudication",
                                   "example", "example-snapshot", accept=True,
                                   review_result=ROOT / "examples/review.json")
        self.assertTrue(result["acceptance_checks_passed"])


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
