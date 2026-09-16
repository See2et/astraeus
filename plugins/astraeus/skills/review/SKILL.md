---
name: review
description: Conduct an explicitly requested independent review, or the required acceptance review of consequential changes under Astraeus. Do not review trivial work by ritual or fix findings as the reviewer.
---

# Independent review

Root remains the acceptance owner. Read [policy](../../references/policy.md) and
[contracts](../../references/contracts.md). Start after implementation and ordinary
verification, against an identified stable target including relevant untracked files.

Use a fresh native agent with no implementation conversation. Provide the original
requirements, constraints, exact target, relevant code, and verification evidence.
Do not prime the reviewer with the implementer's confidence or proposed verdict.
The reviewer may inspect context beyond the diff when needed to understand behavior.

Choose model/effort using the orchestrate routing guidance; difficult design or visual
judgment favors Astra. Tell the reviewer: do not edit files, implement fixes, or spawn
agents. Read-only is an instruction unless host permissions demonstrably enforce it.
Explicitly include any unavailable read-only enforcement or generation-time schema
enforcement in the review prompt. Default `reported` assurance permits these disclosed
limitations. `strict` requires host evidence for the requested model/effort and read-only
sandbox; otherwise stop the affected review. A read-only shell sandbox does not prove
MCP/connector operations are read-only: prohibit mutations through every tool.

Return the review JSON contract. Separate requirement violations and concrete bugs
from optional improvements. Every blocking finding needs a location, concrete claim,
and evidence/reproduction. Do not turn preferences into bugs. Use `inconclusive` for
missing evidence or incomplete coverage, never a speculative pass.

Root validates the reply and checks evidence against the target. `pass` is necessary,
not sufficient: require complete status, no violations/bugs/unresolved questions,
real coverage and evidence, and unchanged target identity. A process exit code or a
well-formed reply alone is not acceptance. Review existing user changes only to the
extent required to assess the authorized change, and never claim credit for them.

Hard limit: two total reviewer dispatches (initial + one re-review); project policy
may lower it to one. Failed,
interrupted, malformed, or inconclusive attempts consume a slot too. No hidden format
repair turns or automatic resetting of the budget. For fixes, the implementer/root
edits and verifies; a fresh reviewer checks the accumulated target with emphasis on
fixed issues and affected behavior. A renewed prompt may include prior findings as
issues to verify, without asserting their resolution. Do not repeat unrelated checks.

Root may change unpinned models with a reason within the same requirements and budget.
Never expand permissions, change billing routes, or widen scope to recover. If the
budget is exhausted, evidence is missing, reviewers disagree unresolvedly, or the
target changed after review, report incomplete and the precise next decision needed.
Explicit user continuation can authorize a new finite budget; it is not a pass.
