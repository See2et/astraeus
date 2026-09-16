# Output contracts

Contracts describe results, never the agent's private reasoning or search sequence.
Read only the relevant schema under `../schemas/`. Review requires JSON; exploration,
research, and implementation may use concise prose when parsing offers little value.
Empty lists are valid where there is nothing to report. Do not manufacture findings.

Common fields: `schema_version: 1`, `kind`, `task_id`, `target_id`, `status`
(`complete|blocked|failed`), and a short `summary`.

| Kind | Additional fields |
| --- | --- |
| exploration | `locations`, `findings`, `evidence`, `unresolved` |
| research | `conclusions`, `sources` (URL, applicable version, checked date, support), `uncertainties` |
| implementation | `changed_files`, `checks` (command, outcome, evidence), `remaining` |
| review | `verdict`, `violations`, `bugs`, `suggestions`, `checked_scope`, `evidence`, `unresolved` |

Review findings contain `location`, `claim`, `evidence`. Suggestions are short strings.
`verdict` is `pass|changes_required|inconclusive`. Missing evidence/coverage or unresolved
questions require inconclusive. A valid changes_required/inconclusive reply is useful
data, not acceptance. The implementer returns what actually ran, including failures.
Research sources must support the attached claim; a URL's existence is not proof.

Native spawn has no assumed schema-enforcement capability. Put the relevant shape in
the prompt, state that enforcement is unavailable when it is, and validate the return:

```sh
uv run <plugin>/scripts/astraeus.py validate-result .astraeus/result.json \
  --kind review --task-id task-1 --target-id <current-target> --accept
```

`uv run` installs only the declared JSON Schema validator dependency, not any model
runtime. Alternatively install jsonschema in your Python environment and use python3.
For non-review roles omit `--accept`; inspect status and evidence before integration.
No `--accept` means format/semantic validation only (exit 0 does NOT mean pass).

The host receipt is separate from the child's contract. A child must not invent
runtime confirmation. Strict acceptance also requires `--assurance strict --receipt`
with JSON shaped as:

```json
{"requested":{"model":"gpt-6-astra","effort":"high"},
 "observed":{"model":"gpt-6-astra","effort":"high","sandbox":"read-only"},
 "source":"host metadata: actual thread/tool response reference"}
```

The checker verifies consistency of supplied data; it cannot authenticate the receipt.
Root must obtain it from the host, never fabricate it or accept child self-report.
Do not collect extra telemetry merely to fill a receipt under reported assurance.
