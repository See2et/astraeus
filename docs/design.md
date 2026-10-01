# Design decisions

Approved direction: global autonomous activation, native agents with prompt-level
no-edit/schema instructions plus post-validation, finite recovery, and Astra priority
for design and visual acceptance. The initial explicit-only activation proposal was
replaced before implementation. No exec-based inference fallback is in this MVP.

The core is orchestration, review, and adjudication skills. Detailed policy and contracts load only when useful.
There are no persona stacks, fixed team sizes, forced exploration passes, or extra
quality gates for optional improvements. Root remains free to reason, work alone,
choose models/effort, and inspect evidence according to the task. Implementers test
their own work; root avoids duplicating those tests without a concrete reason.

Independent review protects against implementation-context bias. It receives original
requirements and the actual artifact, not the entire implementation conversation or
its confidence. A fresh context does not mean a different filesystem, immunity from
shared project instructions, or independently verified model identity. Review remains
an evidence-based judgment rather than an automatic proof of correctness.

The user owns product intent and scope. A distinct fresh adjudicator assesses reviewer
claims before fixes or acceptance, including clean reviews. It can reject a purported
requirement using evidence; reviewer pass is no longer an unconditional veto or sole
acceptance gate. Incomplete coverage/evidence still blocks acceptance. Root checks the
adjudicator's reasons and owns final acceptance. Each reviewer round has at most one
adjudicator; both roles have finite budgets. This is not a recursive agent debate.

Existing code/tests are evidence of behavior, not sufficient authority to preserve it.
Implementation owners inspect only affected contracts and tests, explain intentionally
retired behavior or replacement guarantees, and add verification for concrete gaps.
No test-count target, full-repository audit, mandatory per-test provenance migration,
or extra inventory agent is introduced. Unknown dependencies require investigation,
not speculative compatibility layers or indiscriminate deletion.

Adjudication references every original finding by array/index and binds to the exact
review file hash and task/target. The validator rejects omissions, stale reports, and
contradictory acceptance states, but cannot prove the substance of decisions. Existing
review v1 remains readable; review-only `--accept` intentionally fails with migration
guidance. Strict adjudication needs both roles' independent host receipts.

JSON Schema is used as a well-known result interface, validated by jsonschema rather
than a home-grown schema interpreter. This adds one Python dependency only when result
validation runs. Helpers for activation, maintenance, policy and target identity use
the standard library. Contracts intentionally do not ask for private thought processes.

Metadata is not mixed with child claims: host observations belong in an optional root
receipt. Strict checks validate that supplied fields agree; they cannot authenticate
the source. Reported assurance is usable on hosts without all observability controls.
Known mismatches are errors. Missing observability is disclosed rather than invented.

Consequential-change review and finite retries are root policy, not a hook or tamperproof
state machine. A small result checker rejects malformed/stale/false passes, but cannot
prevent a caller bypassing it. This avoids building a second orchestration/session
engine. If enforcement outside Codex is needed, integrate the checker into an existing
CI gate with independently supplied task/target IDs and evidence.

Global activation is an explicit installation action with a narrow reversible block,
not a skill that rewrites AGENTS.md during ordinary tasks. The manager refuses ambiguous
or edited markers and symlinks. Its operations are preview-first. Local refresh checks
marketplace identity and relies on official Codex commands. A process racing to modify
the source/config after preflight is outside its guarantee; use serial maintenance.

MVP excludes: inference subprocesses, custom auth, agent session stores, recursive agent
trees, dashboards, price snapshots, automatic quota calculations, Cloud compatibility,
and a universal plugin-directory publication workflow. API-equivalent prices do not
measure Pro allowance savings; usage is collected only if already exposed.

Future portability can move to a root plugin.json when validated across supported CLI
versions. The current .codex-plugin/plugin.json compatibility layout was chosen because
it is supported by the official scaffold and verified on the actual local CLI.
