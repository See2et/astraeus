# Astraeus

Lightweight Codex CLI orchestration: Astra owns judgment and acceptance; native
subagents take bounded work and independently review consequential changes.

[日本語](README.ja.md) · [Design](docs/design.md) · [Verification](docs/verification.md)

No model runtime, API authentication, daemon, fixed agent organization, or mandatory
cost receipt. Simple work stays with the root. Implementers own ordinary tests.
Design judgment and visual acceptance favor Astra, including inspection of rendered
artifacts when another model implements the design.

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
Astra, and use any project normally. No explicit per-task command is required.

Global activation is an instruction policy, not a guaranteed host hook. An
`AGENTS.override.md`, higher-priority instructions, disabled plugins, host truncation,
or project instructions can affect loading/behavior. Check these if it does not apply.
The plugin cannot silently change the root model or prove its realized identity.

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

Luna suits narrow easily checked work; Terra bounded work requiring moderate judgment;
Sol difficult dependencies or costly errors; fresh Astra deep/architectural or visual
judgment. These are heuristics, not performance measurements. Root can finish directly.

Consequential behavior, compatibility, data, permissions, installation, and substantial
cross-component changes require a fresh independent reviewer. Reviewers do not fix their
findings. Optional improvements do not block acceptance. Maximum: **two total reviewer
dispatches**, including failures (initial + one re-review). Unresolved or inconclusive
results remain incomplete. Pinned models are never changed automatically.

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

Four JSON Schemas cover exploration, research, implementation, and review. Only review
always requires structure. Small other tasks may return concise prose. Fields describe
outputs and evidence, never a prescribed thought process. See [contracts](plugins/astraeus/references/contracts.md).

In a Git project, freeze writers, put results in an ignored `.astraeus/` directory,
and capture a target ID:

```sh
python3 /path/to/plugin/scripts/astraeus.py target --repo /path/to/project
```

Pass that ID and a task ID to the reviewer. Recompute the target after review; validate
against that current value, not merely the ID the reviewer echoed:

```sh
uv run /path/to/plugin/scripts/astraeus.py validate-result .astraeus/review.json \
  --kind review --task-id task-1 --target-id sha256:CURRENT_HASH --accept
```

You can instead install `jsonschema` and use `python3`. Without `--accept`, exit 0 only
means a valid result, including a valid failure/inconclusive result. `--accept` checks
pass consistency but cannot prove truthful evidence, correct scope, independence, or
review budget adherence; root must check those. Example JSON is illustrative, not a
receipt for real work. Native spawn does not promise generation-time schema enforcement.

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
