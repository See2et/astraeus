# User-requested Claude design delegation

## Routing and ownership

Use this path only when the user explicitly requests Claude for design direction or
directly related UI implementation. A request to improve appearance, project config,
or an available Claude executable is not authorization. Root records the user's
request in task context and attests to it with `--user-requested`; the flag cannot
authenticate user consent. Keep that authorization for follow-up fixes within the same
task, not new work. Explicit project prohibitions and model pins still apply.

Use **Claude Opus 5.5 or a higher version** for this path. Select an explicit model
ID supported by the local Claude Code CLI and available to the account. Use the
`opus` alias only when it is verified to resolve to Opus 5.5 or higher; do not
silently fall back to an older Opus version or another model family. If this
requirement conflicts with an explicit model pin or no qualifying model is
available, report the conflict or unavailability before dispatch.

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

Example request (replace the model placeholder with a supported Opus 5.5-or-higher
model ID, and paths and verification commands with the actual task):

```json
{
  "task_id": "design-001",
  "scope": "ui-implementation",
  "model": "YOUR_OPUS_5_5_OR_HIGHER_MODEL_ID",
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

### Launch evidence and recovery

CLI presence and successful capability/help checks establish supported options only;
they do not establish account authentication, workspace trust, or a successful live
dispatch. The state file binds the request before the launch command runs and survives
a failed launch. Its existence, including an assigned session UUID, is not evidence
that Claude started. Keep requested launch, command outcome, and observed exact-session
state distinct.

When invoking the bridge through an asynchronous host tool, retain the whole tool
result, including its running-cell/process handle, exit code, and output. If it yields,
resume that same invocation through the host's supported wait/poll interface until its
completion or failure is captured; extracting only the initial output can discard the
handle needed to retrieve launch stderr. A missing session is a symptom, not a diagnosis:
inspect the original launch's exit code and stderr before considering another launch.
If diagnostic output was lost, disclose that uncertainty rather than assigning a cause
from the state file or an empty session listing.

A zero launch exit code still needs exact-session verification. If the requested UUID
is absent but a session appears in the dedicated worktree, preserve the launch output
and compare the reported identifiers before recovery. Do not relaunch, rewrite the
state UUID, or automatically bind by cwd alone: another session's identity is not
proved by sharing the directory. Treat that mismatch as an unresolved compatibility
issue; use only supported CLI inspection and evidence for that specific candidate.

New dispatches use version-2 state and retain the requested UUID unchanged. Root-owned
`launch.json` records the launch's stdout, stderr, and exit code, including failures.
The bridge reads the documented `backgrounded · <short-id>` line and requires one
matching `agents` record with the dedicated cwd and a full UUID beginning with that
short ID. Status distinguishes `requested_session_id` from observed `session_id`.
Unknown output, ambiguous IDs, absent records, or changed cwd fail closed; inspect the
retained evidence rather than relaunching. Existing version-1 state still requires
the original requested UUID; old evidence is not automatically reconstructed.

If launch stderr reports `Workspace not trusted`, give the user the exact dedicated
worktree path and ask them to run `claude` interactively from that directory to approve
its trust dialog. Trust in the main checkout is not evidence that the delegated
worktree is trusted. Do not approve trust on the user's behalf, change authentication,
relax permission restrictions, or use a print/API fallback. After the user confirms
approval, preserve the failed handoff and first verify that its exact session is absent
and the worktree remains clean. A single new dispatch may then use a new dedicated
control directory with the authorized request and the same trusted worktree; retain
its outcome and check its exact session. If a session exists or files changed, inspect
that state before recovery to avoid duplicate work. Further failure requires its own
diagnosis, not a retry loop. User approval to resolve trust continues the already
authorized task; it does not authorize a different inference mode or broader ownership.

## Observe, collect, and stop

```sh
python3 /path/to/plugin/scripts/claude_bridge.py status --state /path/to/control/dispatch.json
uv run /path/to/plugin/scripts/claude_bridge.py result --state /path/to/control/dispatch.json
uv run /path/to/plugin/scripts/claude_bridge.py result --state /path/to/control/dispatch.json --apply
python3 /path/to/plugin/scripts/claude_bridge.py cancel --state /path/to/control/dispatch.json
```

Cancel previews by default; `--apply` stops only the selected session and keeps its
files and conversation. Status uses `claude agents --json --all` to select the exact
session. It does not read private session databases or expose unrelated sessions.
Version-2 `cancel --apply` captures the exact CLI stop's exit code and output in
root-owned `stop.json`. Only exit zero with `stopped <bound-short-id>` acknowledges
the stop; a failed or unknown acknowledgment is retained for diagnosis and cannot
authorize publication. Claude is denied edits to this receipt.
Unknown/missing state is not completion; report permission/input blocks and failures.
Use the local CLI's supported session interface to follow up with the same Claude
owner. No unbounded retries, automatic format repair, or respawn of all sessions.

For new version-2 dispatches, Claude writes its completed implementation report to
the specified control-directory `result.json.tmp`; root owns `result.json` and launch
evidence. Claude needs no Bash rename permission. A pending report may say `complete`
only if the work and checks are complete; report publication is root's responsibility.
With no declared checks, use `checks: []`, not an invented `not_run` check.
Prose explanations and design artifacts may accompany it; the entire
conversation need not be JSON. `--json-schema` is print-only, so background dispatch
uses a prompt contract plus post-validation, not generation-time enforcement. State
JSON from `claude agents` describes lifecycle, not implementation results.

The report follows [implementation.json](../schemas/implementation.json), echoing
the supplied task ID and **initial dispatch target ID**. Root collection separately
computes the **final review target ID** from actual Git state. Keep these identifiers
distinct; reviewers/adjudicators use the final stable target. This avoids report
self-hashing and does not let the child invent runtime receipts. Write the report
only after edits and verification. `result` previews validation; `result --apply`
publishes the original validated bytes atomically without overwriting a final report.
It requires an exact session in `done` or `stopped` state with supported `idle` status.
For a `stopped` record omitting status and live pid, a matching successful root-captured
stop receipt supplies affirmative freeze evidence. Missing status without that receipt,
unknown status, or a live pid on this receipt-based path fails closed. The bridge
rechecks the session, source target, and report before publication. Stop the exact
writer first when its last completed turn remains `blocked`/idle. A `blocked` report
is never upgraded to `complete`, even after stopping. Version-1 dispatches retain the
old Claude-owned rename contract and require `done` plus an existing final report.
A missing, malformed, stale, incomplete, or failed report is not a successful
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
still requires the native independent reviewer without a fixed total dispatch limit.
Only a complete `changes_required` review triggers a separate GPT adjudicator; a
validated complete `pass` goes directly to root acceptance. When appearance matters, Astra inspects rendered artifacts;
Claude's explanation or valid JSON is not visual acceptance. If unavailable, disclose
the missing check rather than silently substituting Claude.

## Compatibility and usage

Local help was checked with Claude Code 2.1.223 for `--bg`, `--session-id`, permission
controls, `agents --json --all`, and `stop <id>`. The bridge checks capabilities before
dispatch/stop. Mocked integration and real Git tests do not establish that a live
background inference succeeds with every account or future CLI version.

In a live Claude Code 2.1.288 run, after worktree trust approval, `start --apply`
returned exit code zero while `agents --json --all` showed a working session in the
same dedicated cwd with a different `sessionId` from the requested `--session-id`.
The version-1 bridge therefore reported the requested exact session missing and did
not retain successful launch output. A subsequent live version-2 launch on 2.1.288
captured the explicit stderr warning `--bg manages the session id; ignoring --session-id`
and a stdout `backgrounded · <short-id>` line. This identifies the CLI's background
ID behavior; use its emitted ID rather than assuming the requested UUID controls it.
The version-2 bridge successfully matched that emitted short ID to the observed full
session UUID and dedicated cwd. The earlier launch's missing output remains missing;
the later evidence does not establish behavior for every future CLI version.

In that run, Claude completed the design proposal but the required atomic report
rename (`mv -- <control>/result.json.tmp <control>/result.json`) was denied by Bash
permissions in `dontAsk` mode, despite the bridge declaring that exact command allowed.
Claude left `result.json.tmp` with status `blocked`; the reason for the permission
mismatch remains unknown. An allow declaration does not prove live permission success,
and a temporary report is not a complete handoff. Root may inspect the proposal directly
as a draft, while distinguishing that assessment from verified session binding or
successful bridge collection. Preserve the blocked evidence and diagnose the handoff
failure without relaxing permissions or presenting the draft as a collected result.

Primary references: [agent view and background lifecycle](https://code.claude.com/docs/en/agent-view),
[CLI output and permission options](https://code.claude.com/docs/en/cli-reference), and
[subscription/Agent SDK update](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).
The subscription update pauses the proposed separate SDK/print credit change; it does
not establish an interactive-vs-print consumption multiplier. Background is preferred
here by user choice, not a measured quota guarantee.
