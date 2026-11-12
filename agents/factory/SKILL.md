---
name: factory
description: Run the software factory on GitHub issues labeled `factory`. Use only when explicitly invoked as /factory in Claude Code or $factory in Codex, followed by setup, run, run <n>, grill <n>, or anything else (a question, feedback on a job, rejecting a job, or a new feature).
disable-model-invocation: true
---

# Factory command

Read [AGENT.md](AGENT.md) beside this file and follow it as the workflow entrypoint. Pass the user's request unchanged.

This file is the host command adapter. The orchestration lives in AGENT.md, the deterministic stages in `bin/`, and the project templates in `templates/`. The child agents are installed separately, in `.claude/agents/` and `.codex/agents/`. Reusable capabilities live in the shared skills library resolved through the skill catalog.

Keep the bundle together when installing this adapter so its local references and scripts remain readable.
