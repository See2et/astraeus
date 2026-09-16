# Sources and attribution

Astraeus is a new implementation inspired by the dynamic routing, root acceptance,
and fresh-review concepts in [AstraAdvisor](https://github.com/DannyMac180/astra-advisor),
reviewed at `c72d3280551f118eba51a5884e3971a0c0058aa6` (2026-09-16).
AstraAdvisor is MIT licensed, Copyright (c) 2026 Daniel McAteer. Its code, prompts,
pricing calculator, and pricing snapshots are not bundled here.

Codex's official plugin-creator generated the initial standard manifest/catalog
scaffold; the public [OpenAI plugins](https://github.com/openai/plugins) repository
was consulted for packaging conventions. No personal skills, private repositories,
credentials, histories, or third-party application assets are included.

Primary specifications consulted on 2026-09-16:

- [Plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Skills and invocation policy](https://learn.chatgpt.com/docs/build-skills)
- [Non-interactive mode and JSON Schema](https://learn.chatgpt.com/docs/non-interactive-mode)

Observed local compatibility target: Codex CLI 0.153.4. Live tool schemas and future
CLI behavior may differ. The compatibility manifest remains supported alongside the
newer portable root plugin.json format. This project targets local Codex CLI, not
ChatGPT cloud orchestration or the public universal plugin directory's submission flow.
