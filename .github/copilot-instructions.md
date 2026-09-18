# TopicPilot governed task routing

Before mutation, read AGENTS.md, PROJECT_CONTEXT.md, the applicable work order
and report, then load the matching topicpilot-* skills. Select a task manifest
from docs/governance/tasks/ and run scripts/governance/validate_governance.py.

Use one named branch and one isolated E: worktree per mutation task. Treat
shared schemas, migrations, OpenAPI/generated clients, formal publication
contracts, release configuration, and central governance views as serial
integration surfaces. Never use chat memory as the sole authority. Stop at
owner-decision, operator, ownership, baseline-failure, or integration gates.
