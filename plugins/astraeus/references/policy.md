# Policy and host boundaries

Astraeus is an instruction layer, not a scheduler or security boundary. Codex owns
execution, authentication, threads, permissions, and model capabilities for native
agents. An explicitly requested Claude design task uses Claude Code's own lifecycle
and credentials through the optional bridge; Codex permissions do not establish the
permissions of a detached Claude process. Skill use
cannot guarantee that the host will always obey policy or load all instructions.

Project `astraeus.toml` is optional. Read only the file at the working project root.
Validate via `python3 <plugin>/scripts/astraeus.py doctor --config astraeus.toml`.
Defaults: five documented model candidates (including preferred GPT-6.1 Sol root); review_limit=2; no additional mandatory
paths; assurance=reported. review_limit can only be lowered to 1, never raised above 2.
Allowed model IDs are restrictions, not proof of availability.
`require_review_globs` matches project-relative changed paths with Python fnmatchcase
semantics (`*` can cross `/`); these add review requirements, never remove risk-based ones.
Global activation applies everywhere unless a higher-priority or explicit instruction
disables it. Do not make global edits or install anything while executing ordinary work.

Only a complete `changes_required` review triggers one separate fresh adjudicator
before fixes or acceptance of the rejected target. A complete `pass` goes directly to
root acceptance after review validation and current-target/evidence checks; optional
suggestions do not trigger adjudication. Incomplete or `inconclusive` reviews need
evidence or the next review round, not adjudication. `review_limit` still bounds
reviewer dispatches (maximum two); adjudicator dispatches are separately capped at one
per complete `changes_required` review and at the same total limit. Failed/malformed/interrupted attempts
consume their role's slot; there are no hidden repair turns, reviewer/adjudicator debate
loops, or recursive acceptance agents. Incomplete reviews first need evidence or the
next review round. Use remaining rounds for an updated target/evidence; exhausted or
unresolved work is incomplete until explicit user continuation grants a new finite budget.
Trivial work that needs no independent review needs no adjudicator.

Reviewer findings are proposals, not authorized requirements. Root checks an independent
adjudicator's dispositions; only adopted fixes return to the original implementation
owner. The user retains product scope authority. An adjudicator can reject unsupported
claims, but cannot waive incomplete review coverage or invent approval to retire a
real contract. See [adjudication](../skills/adjudicate/SKILL.md) and
[requirements and tests](requirements-and-tests.md) for decision criteria.

Check current spawn tool metadata once when needed and again only after capability
changes/errors. Exact controls vary by host/version. Do not invent `response_format`,
`sandbox`, or role arguments. A custom agent's configured model may override a spawn
selection, and live parent permissions can override an agent file's defaults. Prefer
generic native agents without fixed role/model TOMLs. If selection is unsupported or
contradictory, stop that dispatch and continue safe root work if useful.

Log requested model/effort and host-observed values separately. When host confirmation
is absent, use unknown, with a short source explanation. Do not inspect auth files,
private session history, unrelated personal skills, or billing to fill missing values.
Under reported assurance, unobservable realized settings can proceed with disclosure;
known mismatch cannot be called a successful pinned dispatch. Under strict assurance,
missing evidence is blocking. No silent model substitution or API charging fallback.
The sole external-inference exception is user-requested Claude design direction and
directly related UI implementation using `--bg`; see [Claude design delegation](claude-design.md).
`allowed_models` restricts native GPT routing, not proof of Claude availability or
permission to dispatch it. Project prohibitions and user pins remain authoritative.
Claude never replaces the native independent reviewer or adjudicator.

Review target IDs can be supplied by a caller's immutable snapshot or by the bundled
`target` command. The command hashes HEAD, tracked staged/unstaged changes, and
nonignored untracked files. Keep outputs in ignored `.astraeus/`; otherwise writing
the result changes the target. It does not hash ignored build outputs, dependency
state, or external services. Freeze concurrent writers while identifying/reviewing
a target; recheck identity before acceptance. Visual evidence must identify the
rendered artifact and relevant viewports/pages, not merely point to source code.

Record task ID, role-specific attempt counts, target ID, selected reviewer/adjudicator,
the original review's content hash, and results in ordinary
task context. If context compaction would lose this, save a short local note under
ignored `.astraeus/`. No mandatory ledger for solo work and no custom session database.
The checker binds adjudication to the exact supplied review and checks disposition
coverage and acceptance consistency. It does not authenticate rationale, host receipts,
role independence, or budgets, or discover consequential changes: root checks those.
