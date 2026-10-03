---
name: orchestrate
description: Apply Astraeus orchestration policy autonomously to project work when globally enabled, or when explicitly requested. Keep simple work solo; delegate only bounded useful work and independently review consequential changes. Do not expand the user's task.
---

# Astraeus

The user owns product intent and scope; root interprets the authorized requirements
and owns architecture, routing, integration, and final acceptance within that scope.
Prefer GPT-6.1 Sol (`gpt-6.1-sol`) for root; preserve explicit user model/effort pins.
This is a selection preference, not a runtime switch. If host metadata shows a different
root from the requested one, disclose it; never claim a switch or Astra judgment without
host evidence. Unknown is unknown. Continue useful authorized work on the existing root
when switching is unavailable; report the requested root as not yet applied.
Default to GPT and native Codex agents, with the actual exposed tool names and schema.
Only an explicit user request permits Claude Code for design direction and directly
related UI implementation; read [Claude design delegation](../../references/claude-design.md)
before that dispatch. Preserve this request through the same task's follow-up fixes,
not unrelated tasks. A generic request to improve appearance is not Claude authorization.
Keep other implementation, integration, independent review, adjudication, and final
acceptance on GPT where available. No other inference CLI, API-key/print fallback,
invented controls, or custom model/session/authentication engine.

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
| GPT-5.6 Luna | Narrow, explicit, local, easily checked work; targeted discovery, mechanical edits. |
| GPT-5.6 Terra | Bounded work requiring moderate judgment or several related files; ordinary implementation/investigation/review. |
| GPT-5.6 Sol | Ambiguous or complex dependencies, costly errors, difficult bugs, concurrency/compatibility/security review. |
| Fresh GPT-6 Astra | Deep independent reasoning, architectural scrutiny, or design/visual quality judgment. |
| Root GPT-6.1 Sol | Handoff costs dominate, scope is still unclear, work is tightly coupled, or final integration/acceptance is needed. |

Prioritize Astra for design direction, composition, typography, color, polish, and
visual acceptance of screens, documents, slides, or other visual artifacts. Other
models can implement a settled design or perform objective extraction/dimension checks.
When appearance matters, GPT-6 Astra must inspect rendered artifacts; an implementation
report is not visual acceptance. With a Sol root, delegate this judgment to a fresh Astra
agent and use that evidence in root's final acceptance. Combine this with the required
independent review when its scope fits; do not add another agent just to repeat it.
If root is explicitly pinned to Astra, it may inspect directly, with fresh independent
review when required. If visual access or Astra is unavailable, report the missing check
rather than substituting silently.

Do not try the cheapest model first by ritual, or assume maximum effort on a smaller
model replaces a stronger model. Consider uncertainty, context, risk, and checkability.
Use live capabilities, not this table, to resolve exact model IDs and effort support.
Allowed defaults: `gpt-6.1-sol`, `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`.
GPT-6 Luna (`gpt-6-luna`) is not a default candidate; do not route to it unless the user
explicitly requests it. GPT-5.6 Luna remains a distinct candidate for narrow work.
Availability in documentation or an allowlist does not prove live host support. Do not
substitute GPT-5.6 Sol for a GPT-6.1 Sol pin. Respect project restrictions and user pins.
Explain material routing changes briefly.

## Handoff and acceptance

Before dispatch, state the task, requested model/effort, and one-line reason. Supply
only the goal, scope/ownership, constraints, acceptance evidence, and useful output
contract. Start independent bounded work with fresh context by default, supplying
relevant files, decisions, and constraints rather than the full conversation. Inherit
conversation only when needed to preserve material context, and keep it to the minimum
supported extent. For reviews, never fork the implementation conversation. Use
`fork_turns: "none"` where supported, or the host's documented equivalent. Do not ask children
to spawn more agents; root owns delegation and keeps it proportionate to the task.

For consequential changes, use [independent review](../review/SKILL.md) after ordinary
verification. Dispatch a separate [adjudicator](../adjudicate/SKILL.md) only when a
complete review returns `changes_required`, before adopting fixes or accepting that
rejected target. For `pass`, root validates the review and current target and owns final
acceptance without an adjudicator. `inconclusive` or incomplete reviews need evidence
or the next review round; do not dispatch an adjudicator to waive missing evidence. This includes behavior/API/compatibility, data, permissions, installation,
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
