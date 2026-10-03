# Verification record

## 2026-10-03 Claude design bridge

The optional bridge delegates only explicitly requested design work to `claude --bg`.
Ordinary GPT routing and native review/adjudication remain unchanged. Final reports
are JSON files validated after generation, not structured-output guarantees from
background Claude. Initial dispatch and final review source identities are separate.

Local Claude Code 2.1.223 help confirms background launch, full session identifiers,
permission/configuration controls, session JSON listing, and exact-session stop.
These capability checks perform no inference. Source isolation/scope and lifecycle
handling are verified with real temporary Git worktrees and a mocked Claude CLI.
The combined suite and the bridge's final 10-test suite pass, including authorization, preview-only dispatch,
session/worktree binding, report validation, committed/staged/reverted/untracked/ignored scope checks,
symlink escapes, and exact-session cancellation.
This does not prove live authentication, runtime permissions, background supervisor
behavior, rendered-artifact quality, or subscription usage savings. No Claude inference
or `-p` call is made during verification.

The real Codex 0.159.3 isolated plugin lifecycle smoke check verifies that the installed
package includes the Claude bridge and its reference, and that the installed bridge's
CLI entrypoint executes. Installation, refresh, reset, activation/removal, and unrelated
plugin/auth/history/config preservation pass in a temporary `CODEX_HOME`. The changed
orchestrate skill passes its structural validator. Existing schemas remain compatible.

## 2026-10-02 update

Only complete `changes_required` reviews trigger adjudication. A complete `pass`
can be validated with `--kind review --accept` before root acceptance, including
optional suggestions. Incomplete or `inconclusive` reviews remain incomplete.
Strict review acceptance requires the reviewer host receipt; rejected-review
adjudication still requires both receipts. Target/task identity checks remain intact.

The 25-test unit suite passed, covering direct pass acceptance, rejection of non-pass,
false-pass and stale review inputs, strict receipt requirements, and the existing
adjudication guarantees. `git diff --check` passed. This checks the validator and
policy consistency, not automatic compliance by future model sessions.

## 2026-10-01 update

The workflow now separates review findings from adoption decisions and checks the
requirement basis of affected behavior/tests. That update required adjudication
plus its original review for acceptance; the 2026-10-02 update above supersedes that rule.

A fresh-context native agent requested as Astra/high applied the new guidance to four
bounded fixtures. It rejected speculative simultaneous coin input and restoration of
explicitly retired CSV export, adopted a reproduced document-loss fix despite 80 passing
happy-path tests, and required investigation for an unverified signup fallback dependency.
It preserved the distinction between rejecting a remedy and accepting the whole change.
This was a read-only simulation using supplied fixture facts, not independently reproduced
product behavior or proof of automatic activation. No ambiguity prevented disposition.
Host-observed realized model/effort and per-agent read-only enforcement remain unknown.

Local verification for this update: the unit suite covers review/adjudication binding,
complete dispositions, acceptance consistency, strict receipts, and legacy CLI migration.
The isolated real-CLI smoke test passed installation (including the new skill/schema),
refresh, reset, source checks, activation/removal, and preservation of unrelated state.
The plugin and all three skills passed their official structural validators; example
policy validation and `git diff --check` passed. These deterministic checks do not prove
that arbitrary model decisions are correct or that all future tasks will obey the skills.

### Earlier verification — 2026-09-16

## Confirmed locally

- Codex CLI 0.153.4 on macOS arm64; Python 3.13/3.14 used locally.
- Sixteen unit tests cover invalid/stale/false-pass results, strict receipt checks,
  all four schemas/examples, invalid policy, reversible activation, source mismatch,
  and source target identity. `uv run python -m unittest discover -s tests -v` passed.
- `python3 tests/smoke_plugin.py` passed with the real CLI and temporary CODEX_HOME:
  install, changed skill content refresh with a new cached version, target-only reset,
  source mismatch refusal, activation enable/disable, removal, marketplace removal.
  Sentinel plugin bytes, unrelated config, dummy auth, and history remained intact.
- The official plugin validator and both official Skill validators passed. These
  validators were used during development; no private tool or skill is bundled.
- A native fresh-context exploration agent requested as Luna/medium returned JSON
  matching exploration.json. The parent validated it, used its source-boundary findings
  in maintenance documentation, and resolved its missing successful-refresh evidence
  via the isolated real-CLI smoke test. No prescribed search count or thought sequence
  was supplied. It returned targeted findings rather than a raw work log.

## Independent review

The first fresh-context reviewer requested as Sol/high returned changes_required:
review_limit could be raised beyond two, and activation disable left separator
newlines behind. The implementation now caps the policy at two and records/removes
only its own separator bytes. Regression tests cover exact LF/CRLF/no-newline
roundtrips and preservation of user text added after activation. All 16 tests and
the real CLI smoke test passed after the correction.

A second fresh-context Sol/high reviewer returned pass, with no violations, bugs, or
unresolved items. The parent rechecked the current target ID and validated the JSON
with --accept successfully. Exactly two review dispatches were used. Reviewed target:
`sha256:14ffaf1ef5fa7214dede1b6f14b143e54230d740f6e9649562c89d190e6cdf2e`.
Only this factual verification record was updated after acceptance; runtime code,
skills, schemas, and tests were unchanged. Both review replies were used directly as
structured inputs to correction/acceptance; no format repair turn was needed.

## Independence and observability

Native agent dispatch uses `fork_turns: none`. Requested model/effort is recorded;
the spawn response here does not independently confirm realized model/effort or a
per-child read-only sandbox. Those observations remain unknown. Review and exploration
prompts prohibit editing and disclose schema/read-only enforcement limitations.
This is reported assurance, not strict assurance. No model calls were made through
codex exec, API keys, or a custom runner.

## Local installation

Version 0.1.0 was installed from the local checkout through official marketplace/add
commands. The global activation block was applied. A fresh interactive session is
still required to observe loading and automatic behavior; the current session cannot
prove hot reload. The GitHub repository was created Private and verified as Private.
No source push or public visibility change was performed.

## Not verified / limits

- Automatic Skill activation in a newly opened interactive CLI across real user projects;
  package installation and the global block lifecycle were tested, not host adherence.
- All model/effort combinations, arbitrary custom user Codex configurations, Windows,
  Linux runtime behavior, ChatGPT cloud, or future CLI versions.
- Git-source remote install/upgrade (local source lifecycle was executed). The Git
  workflow is based on official commands, and requires a nonempty remote repository.
- Read-only enforcement for every connector, actual runtime model identity, Pro quota
  savings, and truthfulness of arbitrary submitted result/receipt JSON.
- Actual visual artifact review: this repository provides policy/tools, not a visual
  product; no visual-model benchmark was run.
- GitHub Actions execution: workflow is included, but source has not been pushed.

The test suite checks concrete failure conditions, not whether model output repeats
prompt wording. Native JSON contracts are post-validated, not generation-enforced.
Review retry budgets and identifying consequential work remain root responsibilities.

## Reproduce

```sh
uv sync --locked
uv run python -m unittest discover -s tests -v
python3 tests/smoke_plugin.py
```

To test live integration after installing and opening a new session: ask for a narrow
exploration using exploration.json; validate and use its evidence. Then have a fresh
reviewer inspect a bounded change using review.json, followed by a distinct adjudicator
using adjudication.json and the original review. Validate the adjudication against a
newly computed target ID with `--review-result <original-review> --accept`; confirm a
seeded bug requires a fix, an unsupported requirement can be rejected, and missing
evidence remains inconclusive. Observe no-edit behavior without claiming an enforced
sandbox unless the host exposes evidence. Live tests consume the user's Codex allowance.
