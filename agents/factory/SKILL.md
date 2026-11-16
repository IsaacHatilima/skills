---
name: factory
description: Build a description into a reviewed, documented pull request. Use only when explicitly invoked as /factory in Claude Code or $factory in Codex, followed by a description, setup, run, run <job>, mitarbo <task-key>, or feedback about a job. Interactive brainstorming and grilling are separate from this workflow.
disable-model-invocation: true
---

# Factory command

Read [AGENT.md](AGENT.md) beside this file and follow it as the workflow entrypoint. Pass the user's request unchanged.

This file is the host command adapter. The orchestration lives in AGENT.md, the deterministic stages in `bin/`, and the project templates in `templates/`. The child agents are installed separately, in `.claude/agents/` and `.codex/agents/`. Reusable capabilities live in the shared skills library resolved through the skill catalog.

Keep the bundle together when installing this adapter so its local references and scripts remain readable.
