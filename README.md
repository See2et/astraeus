# Astraeus

Lightweight Codex CLI orchestration: GPT-6.1 Sol root owns routing and final acceptance; native
subagents take bounded work and independently review consequential changes.

Review findings go to a separate fresh adjudicator before fixes or acceptance. It checks
requirement authority, concrete impact, and proportionality; root owns final acceptance.
Existing code and tests describe behavior, but do not by themselves make it a requirement.

[日本語](README.ja.md) · [Design](docs/design.md) · [Verification](docs/verification.md)

No model runtime, API authentication, daemon, fixed agent organization, or mandatory
cost receipt. Simple work stays with the root. Implementers own ordinary tests.
Design judgment and visual acceptance favor Astra, including inspection of rendered
artifacts when another model implements the design.

To avoid duplicate work, root stops discovery once the goal, scope, constraints, and
acceptance check are clear enough to delegate. One owner keeps bounded discovery,
implementation, ordinary verification, and follow-up fixes. Independent work starts
with fresh context containing relevant files, decisions, and constraints; conversation
inheritance is reserved for necessary context. Root inspects diffs, evidence, and open
issues, repeating discovery or checks only for integration changes, failed checks,
missing evidence, or concrete concerns in the affected scope. Independent review
focuses on requirements, behavior at risk, and verification gaps, following dependencies
as needed, without unrelated improvement searches or redesign. Review requirements
remain unchanged. These practices reduce duplication; they do not guarantee Pro quota
savings.

## Install and enable across projects

Requires a current Codex CLI with native subagents and plugin commands (tested with
0.153.4), Python 3.11+, and an existing Codex login. Astraeus uses that host, never an
API-key fallback. `uv` or `jsonschema` is needed only for contract validation.

From your local checkout:

```sh
codex plugin marketplace add /absolute/path/to/astraeus
codex plugin add astraeus@astraeus
python3 plugins/astraeus/scripts/astraeus.py activation enable
python3 plugins/astraeus/scripts/astraeus.py activation enable --apply
```

The activation command previews by default. `--apply` appends a small managed block to
`$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`), preserving existing text and saving
a local backup when changing existing content. It never replaces your personal rules.
The installed skill permits implicit invocation. Start a **new Codex session**, select
GPT-6.1 Sol (`gpt-6.1-sol`), and use any project normally. No explicit per-task command is required.

Global activation is an instruction policy, not a guaranteed host hook. An
`AGENTS.override.md`, higher-priority instructions, disabled plugins, host truncation,
or project instructions can affect loading/behavior. Check these if it does not apply.
The plugin cannot silently change the root model or prove its realized identity.
If the host does not expose GPT-6.1 Sol, disclose that it has not been selected; do not
substitute GPT-5.6 Sol for it. Update the client if needed and select the requested model
in a new session. Model availability still depends on the host and account.

Once the repository contains a published commit, Git-source installation is also:

```sh
codex plugin marketplace add See2et/astraeus --ref main
codex plugin add astraeus@astraeus
```

Private repositories require your own Git access. An empty remote is not installable.
Do not register the Git source and local checkout under the same marketplace name
simultaneously. Remove the old source explicitly before switching.

## Use

You can also explicitly invoke `$astraeus:orchestrate` for a task or
`$astraeus:review` for an existing change. Root chooses whether delegation is useful,
then selects the model and supported effort from difficulty, risk, independence, and
checkability. No fixed headcount, role/model mapping, or required search count.

GPT-5.6 Luna suits narrow easily checked work; GPT-5.6 Terra bounded work requiring
moderate judgment; GPT-5.6 Sol difficult dependencies or costly errors; fresh GPT-6 Astra
deep/architectural or visual judgment. GPT-6.1 Sol handles root integration and acceptance.
GPT-6 Luna is excluded from default routing; GPT-5.6 Luna remains available. These are heuristics, not performance measurements. Root can finish directly.

Consequential behavior, compatibility, data, permissions, installation, and substantial
cross-component changes require a fresh independent reviewer. Reviewers do not fix their
findings. Optional improvements do not block acceptance. Maximum: **two total reviewer
dispatches**, including failures (initial + one re-review). Each complete review has one
separate adjudicator dispatch, capped at the same total limit including failures.
Unresolved or inconclusive results remain incomplete. Pinned models are never changed automatically.

## Optional project policy

Copy `astraeus.example.toml` to the working project's `astraeus.toml` when needed.
Defaults work without configuration. It restricts models, adds mandatory review paths,
can lower the review limit to one, and selects reported/strict assurance. No global config
rewrites and no workflow DSL. Unknown settings fail validation.

```sh
python3 plugins/astraeus/scripts/astraeus.py doctor --config astraeus.example.toml
```

Reported assurance is the default: native subagents + explicit no-edit/schema prompts
+ result validation, with unavailable enforcement disclosed. Strict assurance requires
host evidence of requested model/effort and read-only sandbox. No silent fallback.
Neither prompt-only restrictions nor shell sandboxing prove that connector tools are
read-only; reviewers are instructed not to mutate through any tool.

## Result contracts

Five JSON Schemas cover exploration, research, implementation, review, and adjudication.
Review and adjudication always require structure. Small other tasks may return concise prose. Fields describe
outputs and evidence, never a prescribed thought process. See [contracts](plugins/astraeus/references/contracts.md).

In a Git project, freeze writers, put results in an ignored `.astraeus/` directory,
and capture a target ID:

```sh
python3 /path/to/plugin/scripts/astraeus.py target --repo /path/to/project
```

Pass that ID and a task ID to the reviewer, then the adjudicator along with the original
review. Recompute the target before acceptance; validate against that current value,
not merely the ID the agents echoed:

```sh
uv run /path/to/plugin/scripts/astraeus.py validate-result .astraeus/review.json \
  --kind review --task-id task-1 --target-id sha256:CURRENT_HASH

uv run /path/to/plugin/scripts/astraeus.py validate-result .astraeus/adjudication.json \
  --kind adjudication --task-id task-1 --target-id sha256:CURRENT_HASH \
  --review-result .astraeus/review.json --accept
```

You can instead install `jsonschema` and use `python3`. Without `--accept`, exit 0 only
means a valid result, including a valid failure/inconclusive result. `--accept` checks
adjudication consistency, exact review identity, and disposition coverage, but cannot
prove truthful evidence, correct scope, independence, or dispatch budget adherence;
root must check those. Review v1 files remain valid; review-only `--accept` is deliberately
rejected. Strict adjudication requires `--receipt` for the adjudicator and
`--review-receipt` for the reviewer. Example JSON is illustrative, not a
receipt for real work. Native spawn does not promise generation-time schema enforcement.

## Requirements, findings, and tests

The user owns product scope. Root derives the outcome, non-goals, acceptance conditions,
and preserved contracts from the request and relevant evidence; clear requests need no
extra approval. The implementation owner inspects affected tests/behavior, implements,
and verifies. No full-repository inventory or mandatory new spec documents are required.

Use `$astraeus:adjudicate` after independent review. Its dispositions are `fix`,
`investigate`, `reject`, and `human_decision`. Only adopted fixes return to the original
implementation owner. Speculative features, severity labels, or a test's existence do
not authorize new requirements. Real consumers, data invariants, and published contracts
still matter even when undocumented. Incomplete review evidence cannot be waived.

Add tests for concrete requirements/risks and gaps in existing verification. When tests
change or disappear, explain which behavior was intentionally retired or which remaining
check protects its guarantee and regression value. Never weaken assertions just to pass,
or restore obsolete behavior just because an old test failed. Unknown dependencies get
bounded investigation; unauthorized product changes return to the user as grouped
decisions. See [requirements and tests](plugins/astraeus/references/requirements-and-tests.md).

## Update and local development

Four different things exist: your editable checkout, a Codex Git-marketplace snapshot,
the installed plugin cache, and the running session. Editing one does not update all.

For a **local checkout** already registered as the source:

```sh
python3 plugins/astraeus/scripts/astraeus.py plugin refresh --repo .
python3 plugins/astraeus/scripts/astraeus.py plugin refresh --repo . --apply
```

Refresh checks source identity, updates only Astraeus's local version suffix to
`+codex.<timestamp>`, then runs official `codex plugin add`. It never increments a
release version or edits a marketplace catalog to force a different source. The suffix
is a development change in your checkout; remove it before a release. If install fails,
the suffix remains and the error is returned; fix the error and rerun. Start a new
session after success.

For a **Git source**:

```sh
codex plugin marketplace upgrade astraeus
codex plugin add astraeus@astraeus
```

For a broken local install, preview then apply the target-only reset:

```sh
python3 plugins/astraeus/scripts/astraeus.py plugin reset --repo .
python3 plugins/astraeus/scripts/astraeus.py plugin reset --repo . --apply
```

Reset uses official removal/reinstallation for `astraeus@astraeus`; it does not delete
cache trees manually. If reinstallation fails, report the error and reinstall after
fixing the cause. A different/Git source is refused by the local maintenance tool.
Use official commands for that source. No hot reload is claimed for active threads.

## Remove

```sh
python3 plugins/astraeus/scripts/astraeus.py activation disable --apply
codex plugin remove astraeus@astraeus
codex plugin marketplace remove astraeus
```

Disable activation before removing the script. Only the exact owned block is removed;
edited/ambiguous blocks require manual inspection. Existing text, backups, authentication,
history, and other plugins are retained. Start a fresh session. A checkout or Git remote
is not deleted by uninstalling. Backups may contain your private instructions; keep
them local and delete them manually when no longer needed.

## Develop and verify

```sh
uv sync --locked
uv run python -m unittest discover -s tests -v
python3 tests/smoke_plugin.py
```

The smoke test uses the real CLI in a temporary `CODEX_HOME`, checks lifecycle and
sentinel preservation, and performs no model calls. CI runs offline logic tests after
installing the validator, with no Codex credentials. Live native-agent checks and exact
tested limits are recorded in [verification](docs/verification.md).

MIT. [Sources and attribution](NOTICE.md). Usage telemetry is optional; API-equivalent
prices are never called measured ChatGPT Pro quota savings.
