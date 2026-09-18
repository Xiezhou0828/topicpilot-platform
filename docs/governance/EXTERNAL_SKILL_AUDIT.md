# External Skill and Agent Customization Audit

**Decision:** use portable patterns, import no third-party code, and keep
TopicPilot repository evidence authoritative.

| Skill or pattern | Source | Useful idea | Imported code | Risk | Decision |
|---|---|---|---:|---|---|
| Project Agent Skills | https://docs.github.com/en/copilot/concepts/agents/about-agent-skills | Folder-scoped SKILL.md with progressive disclosure | 0 | Low after local review | Adopt format; TopicPilot-specific policy and scripts only |
| Copilot custom agents | https://docs.github.com/en/copilot/reference/custom-agents-configuration | Markdown agent profile with YAML frontmatter | 0 | Tool over-permission if unconstrained | Adopt profiles with bounded prompts and explicit non-production limits |
| Copilot hooks | https://docs.github.com/en/copilot/reference/hooks-reference | Version 1 JSON hook configuration and preToolUse decision output | 0 | Runtime availability and shell supply-chain risk | Adopt minimal local guard; CI/scripts remain authoritative |
| Copilot merge queue | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue | merge_group checks against the latest queue composition | 0 | Repository settings may be unavailable | Add merge_group-compatible workflow trigger; settings remain unconfigured |
| github/awesome-copilot and other community collections | Community sources | Discovery only | 0 | Unreviewed scripts, network calls, credentials, broad permissions | Do not vendor or execute |

No external shell script, package, network call, credential access, git mutation,
or destructive command was imported. External documentation informed file
formats only; it does not override TopicPilot authority.
