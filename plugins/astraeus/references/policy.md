# Policy and host boundaries

Astraeus is an instruction layer, not a scheduler or security boundary. Codex owns
execution, authentication, threads, permissions, and model capabilities. Skill use
cannot guarantee that the host will always obey policy or load all instructions.

Project `astraeus.toml` is optional. Read only the file at the working project root.
Validate via `python3 <plugin>/scripts/astraeus.py doctor --config astraeus.toml`.
Defaults: four documented model candidates; review_limit=2; no additional mandatory
paths; assurance=reported. review_limit can only be lowered to 1, never raised above 2.
Allowed model IDs are restrictions, not proof of availability.
`require_review_globs` matches project-relative changed paths with Python fnmatchcase
semantics (`*` can cross `/`); these add review requirements, never remove risk-based ones.
Global activation applies everywhere unless a higher-priority or explicit instruction
disables it. Do not make global edits or install anything while executing ordinary work.

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
missing evidence is blocking. No silent model substitution, external inference, or
API charging fallback. User pins remain authoritative.

Review target IDs can be supplied by a caller's immutable snapshot or by the bundled
`target` command. The command hashes HEAD, tracked staged/unstaged changes, and
nonignored untracked files. Keep outputs in ignored `.astraeus/`; otherwise writing
the result changes the target. It does not hash ignored build outputs, dependency
state, or external services. Freeze concurrent writers while identifying/reviewing
a target; recheck identity before acceptance. Visual evidence must identify the
rendered artifact and relevant viewports/pages, not merely point to source code.

Record task ID, attempt count, target ID, selected reviewer and results in ordinary
task context. If context compaction would lose this, save a short local note under
ignored `.astraeus/`. No mandatory ledger for solo work and no custom session database.
The checker does not independently enforce review budgets or discover consequential
changes: those remain explicit root responsibilities.
