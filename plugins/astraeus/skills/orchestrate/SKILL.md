---
name: orchestrate
description: Apply Astraeus orchestration policy autonomously to project work when globally enabled, or when explicitly requested. Keep simple work solo; delegate only bounded useful work and independently review consequential changes. Do not expand the user's task.
---

# Astraeus

The user owns product intent and scope; root Astra interprets the authorized requirements
and owns architecture, routing, integration, and final acceptance within that scope.
Keep the user's root model/effort. If host metadata shows a non-Astra root, disclose
the mismatch; do not claim Astra judgment or silently switch models. Unknown is unknown.
Use native Codex agents only, with the actual exposed tool names and schema. No nested
inference CLI, API-key fallback, invented controls, or model/session/authentication engine.

For trivial work, finish directly. Do not generate a plan, receipt, contract, or agent
just to follow this skill. For consequential work, read [policy](../../references/policy.md)
and the project's explicit `astraeus.toml` if present (use `doctor` to validate it).
Do not search parent directories or personal skills for more policy. Explicit user
constraints and Codex permissions remain authoritative.

For behavior changes, establish the intended outcome, acceptance conditions, non-goals,
and contracts to preserve from the request and relevant evidence. Clear requests need
no extra approval or permanent spec file. Use [requirements and tests](../../references/requirements-and-tests.md)
when existing behavior/tests constrain a change, a test fails, or verification is added,
changed, or removed. Inspect only the affected area. Code, tests, and agent suggestions
describe current behavior; they do not by themselves authorize requirements.

Delegate only when a bounded outcome, adequate context, and an acceptance check can
be stated and the benefit exceeds handoff/integration cost. No fixed agent count,
role-to-model assignment, or mandatory search/thinking sequence. Keep coupled decisions
with the root. Give each writer disjoint ownership; preserve existing user changes.
Once the goal, scope, constraints, and acceptance check are clear enough to delegate,
stop root discovery and hand off; do not solve implementation details first. Resolve
coupled requirements or architecture at the root when they are needed for that handoff.
Keep discovery, implementation, and ordinary verification for a bounded outcome with
one owner, including follow-up fixes; do not split agents merely by phase. The owner
returns specification decisions to the root and handles local implementation choices.
Root checks the diff, verification evidence, and remaining issues. Repeat discovery
or checks only for integration changes, failed checks, missing evidence, or a concrete
concern; name the trigger and limit the follow-up to the affected scope.

## Routing

Choose a capable model first, then an appropriate supported effort. These are heuristics,
not measured quota savings or guarantees about model quality:

| Candidate | Prefer when |
| --- | --- |
| Luna | Narrow, explicit, local, easily checked work; targeted discovery, mechanical edits. |
| Terra | Bounded work requiring moderate judgment or several related files; ordinary implementation/investigation/review. |
| Sol | Ambiguous or complex dependencies, costly errors, difficult bugs, concurrency/compatibility/security review. |
| Fresh Astra | Deep independent reasoning, architectural scrutiny, or design/visual quality judgment. |
| Root Astra | Handoff costs dominate, scope is still unclear, work is tightly coupled, or final integration/acceptance is needed. |

Prioritize Astra for design direction, composition, typography, color, polish, and
visual acceptance of screens, documents, slides, or other visual artifacts. Other
models can implement a settled design or perform objective extraction/dimension checks.
Root Astra must inspect rendered artifacts when appearance matters; a worker's report
is not visual acceptance. Use fresh Astra for an independent visual review when needed,
not an extra agent merely to repeat the root's inspection. If visual access or Astra
is unavailable, report the missing check rather than substituting silently.

Do not try the cheapest model first by ritual, or assume maximum effort on a smaller
model replaces a stronger model. Consider uncertainty, context, risk, and checkability.
Use live capabilities, not this table, to resolve exact model IDs and effort support.
Allowed defaults: `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`.
Respect project restrictions and user pins. Explain material routing changes briefly.

## Handoff and acceptance

Before dispatch, state the task, requested model/effort, and one-line reason. Supply
only the goal, scope/ownership, constraints, acceptance evidence, and useful output
contract. Start independent bounded work with fresh context by default, supplying
relevant files, decisions, and constraints rather than the full conversation. Inherit
conversation only when needed to preserve material context, and keep it to the minimum
supported extent. For reviews, never fork the implementation conversation. Use
`fork_turns: "none"` where supported, or the host's documented equivalent. Do not ask children
to spawn more agents; root owns delegation and the finite budget.

For consequential changes, use [independent review](../review/SKILL.md) after ordinary
verification, then a separate [adjudicator](../adjudicate/SKILL.md) before adopting any
finding or accepting the work. This includes behavior/API/compatibility, data, permissions, installation,
or meaningful multi-component changes. Trivial spelling/format-only edits may finish
solo. Apply additional mandatory paths from project policy. Root decides borderline
cases with a short reason; optional polish never becomes a new acceptance gate.

Read [contracts](../../references/contracts.md) only when structured output helps.
Review and adjudication always use their contracts. Other small tasks may return concise prose.
Report outcomes and missing checks, not raw work logs. Separate requested values from
host-observed values and their sources; child self-identification is not host evidence.
Never claim enforced read-only or generation-time schema guarantees from instructions.
Cost telemetry is optional and only uses already available observations. Do not query
billing or estimate Pro quota savings from API prices or message length.
