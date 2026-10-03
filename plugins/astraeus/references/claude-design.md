# User-requested Claude design delegation

## Routing and ownership

Use this path only when the user explicitly requests Claude for design direction or
directly related UI implementation. A request to improve appearance, project config,
or an available Claude executable is not authorization. Root records the user's
request in task context and attests to it with `--user-requested`; the flag cannot
authenticate user consent. Keep that authorization for follow-up fixes within the same
task, not new work. Explicit project prohibitions and model pins still apply.

GPT/native Codex remains the default for all other work, including business logic,
APIs, data, architecture, integration, independent review, adjudication, and final
acceptance. Claude's implementation owner also performs its ordinary verification
and follow-up fixes. Give writers disjoint paths; sequence edits when UI and business
logic share a file. Do not broaden Claude ownership merely because a file is frontend
code. Design direction can return documents with no code changes.

The bridge is `../scripts/claude_bridge.py`. It invokes the existing Claude Code CLI;
it does not create a Codex-native thread or inherit its authentication, sandbox, or
host receipts. No Claude installation, login changes, billing inspection, permission
bypass, print/API fallback, or nested agent delegation is performed. Missing CLI
capabilities or permissions are explicit errors, not permission to switch execution
modes. Do not claim quota savings or observed Claude identity from a requested model.

## Start

Root prepares a clean, dedicated **linked Git worktree** at the source snapshot to
delegate. The shared/main checkout is refused. Preserve unsaved user work: do not
reset, stash, or commit it merely to prepare delegation. A linked worktree alone is
not a security sandbox. Put request/state/report in a dedicated control directory
outside that worktree; never expose an unrelated personal directory to the agent.

Example request (replace paths and verification commands with the actual task):

```json
{
  "task_id": "design-001",
  "scope": "ui-implementation",
  "model": "opus",
  "effort": "high",
  "owned_paths": ["src/components/ProductCard.tsx", "src/styles/product-card.css"],
  "goal": "Implement the requested product card layout using the supplied design brief.",
  "constraints": ["Preserve props and purchase behavior", "Do not publish, push, or open a PR"],
  "checks": ["npm run build"]
}
```

`scope` is `design-direction` or `ui-implementation`; `effort` is optional. Owned
paths are worktree-relative files/directories, not blanket ownership of the project.
Include expected build/verification output paths in ownership too; collection checks
ignored output files as well as source changes, so undeclared generated files block
handoff. For example, a build creating `dist/` requires that output directory in scope.
The model is requested, not host-observed. Root supplies only needed context in the
goal/constraints and referenced artifacts, not the entire implementation conversation.
Checks are trusted task commands, not externally sourced instructions. No extra
inference permission follows from running these commands.

```sh
python3 /path/to/plugin/scripts/claude_bridge.py start \
  --request /path/to/control/request.json \
  --worktree /path/to/design-worktree \
  --state /path/to/control/dispatch.json --user-requested
```

Start previews by default; add `--apply` for the authorized dispatch. The bridge
records the initial source target/base and assigns a session identifier. It starts
Claude with `--bg` in the existing linked worktree, rather than letting a background
session create and publish another isolated branch. Permission restrictions deny
publication and nested agents; allowed editing and verification are bounded to the
request. They supplement instructions and collection checks, not an OS sandbox.
Approval prompts or denied checks can leave work blocked. Never remove these limits
or switch to `-p` just to obtain a result.
The worktree must already be trusted by Claude Code and the CLI must already be
authenticated. A noninteractive background launch cannot accept a workspace trust
dialog. Failed dispatch retains the handoff for inspection; do not blindly relaunch.

## Observe, collect, and stop

```sh
python3 /path/to/plugin/scripts/claude_bridge.py status --state /path/to/control/dispatch.json
uv run /path/to/plugin/scripts/claude_bridge.py result --state /path/to/control/dispatch.json
python3 /path/to/plugin/scripts/claude_bridge.py cancel --state /path/to/control/dispatch.json
```

Cancel previews by default; `--apply` stops only the selected session and keeps its
files and conversation. Status uses `claude agents --json --all` to select the exact
session. It does not read private session databases or expose unrelated sessions.
Unknown/missing state is not completion; report permission/input blocks and failures.
Use the local CLI's supported session interface to follow up with the same Claude
owner. No unbounded retries, automatic format repair, or respawn of all sessions.

Claude writes its final implementation report to the specified control-directory
`result.json`. Prose explanations and design artifacts may accompany it; the entire
conversation need not be JSON. `--json-schema` is print-only, so background dispatch
uses a prompt contract plus post-validation, not generation-time enforcement. State
JSON from `claude agents` describes lifecycle, not implementation results.

The report follows [implementation.json](../schemas/implementation.json), echoing
the supplied task ID and **initial dispatch target ID**. Root collection separately
computes the **final review target ID** from actual Git state. Keep these identifiers
distinct; reviewers/adjudicators use the final stable target. This avoids report
self-hashing and does not let the child invent runtime receipts. Write the report
only after edits and verification; use a temporary file and rename to avoid partial
reads. A missing, malformed, stale, incomplete, or failed report is not a successful
handoff.

Result collection validates the contract and actual changes against the initial
baseline, including committed edits, staged/unstaged changes, and untracked files
(including ignored outputs).
It rejects changes outside ownership and mismatches between reported/actual files,
remaining issues, and incomplete required verification. Freeze the Claude writer
while collecting; recheck the final target before integration/review. Ignored outputs,
external services, and writes outside the worktree are not covered by source hashing.

Successful collection is **not final acceptance**. Root checks the diff, evidence,
and remaining risk, then integrates only the authorized changes. Consequential work
still requires the native independent reviewer under the existing finite budget.
Only a complete `changes_required` review triggers a separate GPT adjudicator; a
validated complete `pass` goes directly to root acceptance. When appearance matters, Astra inspects rendered artifacts;
Claude's explanation or valid JSON is not visual acceptance. If unavailable, disclose
the missing check rather than silently substituting Claude.

## Compatibility and usage

Local help was checked with Claude Code 2.1.223 for `--bg`, `--session-id`, permission
controls, `agents --json --all`, and `stop <id>`. The bridge checks capabilities before
dispatch/stop. Mocked integration and real Git tests do not establish that a live
background inference succeeds with every account or future CLI version.

Primary references: [agent view and background lifecycle](https://code.claude.com/docs/en/agent-view),
[CLI output and permission options](https://code.claude.com/docs/en/cli-reference), and
[subscription/Agent SDK update](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
The subscription update pauses the proposed separate SDK/print credit change; it does
not establish an interactive-vs-print consumption multiplier. Background is preferred
here by user choice, not a measured quota guarantee.
