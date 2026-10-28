# Agents and skills

Agent bundles define workflows. Shared skills provide capabilities that any workflow can use.

```text
agents/
  factory/
    AGENT.md               factory workflow entrypoint
    SKILL.md               thin /factory command adapter
    builder.md             factory child-agent role
    reviewer-security.md
    ...
skills/
  catalog.md               shared capability index
  laravel/                 actions, controllers, data, ...
  nest/                    actions, controllers, dtos, database, migrations, ...
  next/                    actions
  tanstack-start/          actions
  frontend/                app-shell, overlays, data-display
  quality/                 simplicity, review, security-review
archive/
  skills/                  archived: general, react, javascript, inertia, and each stack's old *-feature-development skill
```

## Agent workflows

[Factory](agents/factory/AGENT.md) starts the feature-building workflow: specification, implementation, review, documentation, and approval. Its child agents and workflow-specific skill assignments live under [agents/factory/](agents/factory/README.md).

After host registration, invoke `/factory create login feature` in Claude Code or `$factory create login feature` in Codex. `AGENT.md` owns the workflow; `SKILL.md` adapts it to hosts that expose commands through skills. It is outside the shared capability library.

Add future workflows under `agents/<name>/`, with an `AGENT.md` entrypoint and the roles or command adapter they need. An E2E or security-testing workflow can work directly on existing code and reuse the shared library.

## Shared skills

The [catalog](skills/catalog.md) lists reusable capabilities and path-resolution rules. Each workflow selects the skills relevant to its scope and determines its own report and completion contracts.

| Location | Capabilities |
|---|---|
| `skills/laravel/` | Laravel conventions: [actions](skills/laravel/actions/SKILL.md), [api-responses](skills/laravel/api-responses/SKILL.md), [architecture](skills/laravel/architecture/SKILL.md), [controllers](skills/laravel/controllers/SKILL.md), [data](skills/laravel/data/SKILL.md), [eloquent-strictness](skills/laravel/eloquent-strictness/SKILL.md), [enums](skills/laravel/enums/SKILL.md), [frontend](skills/laravel/frontend/SKILL.md), [insights](skills/laravel/insights/SKILL.md), [jobs](skills/laravel/jobs/SKILL.md), [migrations](skills/laravel/migrations/SKILL.md), [models](skills/laravel/models/SKILL.md), [phpstan](skills/laravel/phpstan/SKILL.md), [requests](skills/laravel/requests/SKILL.md), [security](skills/laravel/security/SKILL.md), [tests](skills/laravel/tests/SKILL.md) |
| `skills/nest/` | NestJS conventions for Prisma and Zod: [actions](skills/nest/actions/SKILL.md), [api-responses](skills/nest/api-responses/SKILL.md), [architecture](skills/nest/architecture/SKILL.md), [controllers](skills/nest/controllers/SKILL.md), [database](skills/nest/database/SKILL.md), [dtos](skills/nest/dtos/SKILL.md), [jobs](skills/nest/jobs/SKILL.md), [migrations](skills/nest/migrations/SKILL.md), [security](skills/nest/security/SKILL.md), [tests](skills/nest/tests/SKILL.md) |
| `skills/next/` | [Next actions](skills/next/actions/SKILL.md) |
| `skills/tanstack-start/` | [TanStack Start actions](skills/tanstack-start/actions/SKILL.md) |
| `skills/frontend/` | Stack-agnostic: [app-shell](skills/frontend/app-shell/SKILL.md), [overlays](skills/frontend/overlays/SKILL.md), [data-display](skills/frontend/data-display/SKILL.md) |
| `skills/quality/` | Stack-agnostic, adapted from Anthropic's official plugins: [simplicity](skills/quality/simplicity/SKILL.md), [review](skills/quality/review/SKILL.md), [security-review](skills/quality/security-review/SKILL.md) |

Other skill groups (`general`, `react`, `javascript`, `inertia`, and the earlier `*-feature-development` skills of each stack) are archived under [`archive/skills/`](archive/skills/). They are not in the catalog and are not distributed. To restore one, move it back under `skills/` and add it to the catalog.

The factory workflow still assigns several archived skills to its roles (see [its selection rules](agents/factory/references/skills.md)); it cannot run from this repository until they are restored or its assignments are rewritten.

Use `skills/<group>/<skill-name>/SKILL.md` with lowercase, hyphenated names and YAML `name`/`description` frontmatter. Add supporting files only when needed. Register a new capability in the shared catalog; each agent workflow maintains its own role/phase selection rules.

Each stack folder is self-contained so it can ship on its own. Its `actions` skill covers only that framework; stack-agnostic rules live in `skills/quality/`.

## Planned distribution

Later, merges to `main` will open PRs in downstream repositories for the agent bundles and skill groups they use.

- `skills/laravel/` changes go to Laravel consumers through Laracanon; `skills/nest/`, `skills/next/` and `skills/tanstack-start/` go to JavaScript consumers through domain-driver.
- `skills/quality/` and `skills/frontend/` are stack-agnostic and go to every consumer that selects them.
- `agents/factory/` changes go to consumers of the factory workflow.
- `archive/` is never distributed.

Installation/rendering, downstream mappings, and PR automation remain future work. This repository contains workflow and skill sources.
