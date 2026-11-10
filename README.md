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
  nest/                    actions, controllers, dtos, database, migrations, ...
  next/                    actions
  tanstack-start/          actions
  frontend/                app-shell, overlays, data-display
  quality/                 simplicity, review, security-review
  javascript/              domain-driver CLI guidance
archive/
  skills/                  archived: general, react, javascript, inertia, and each stack's old *-feature-development skill
```

Laravel skills are not here: [Laracanon](https://github.com/IsaacHatilima/laracanon) maintains them and installs them into a Laravel application with `php artisan canon:install`.

## Agent workflows

[Factory](agents/factory/AGENT.md) starts the feature-building workflow: specification, implementation, review, documentation, and approval. Its child agents and workflow-specific skill assignments live under [agents/factory/](agents/factory/README.md).

After [installing it in a project](#using-these-in-a-project), invoke `/factory create login feature` in Claude Code or `$factory create login feature` in Codex. `AGENT.md` owns the workflow; `SKILL.md` adapts it to hosts that expose commands through skills. It is outside the shared capability library.

Add future workflows under `agents/<name>/`, with an `AGENT.md` entrypoint and the roles or command adapter they need. An E2E or security-testing workflow can work directly on existing code and reuse the shared library.

## Shared skills

The [catalog](skills/catalog.md) lists reusable capabilities and path-resolution rules. Each workflow selects the skills relevant to its scope and determines its own report and completion contracts.

| Location | Capabilities |
|---|---|
| `skills/nest/` | NestJS conventions for Prisma and Zod: [actions](skills/nest/actions/SKILL.md), [api-responses](skills/nest/api-responses/SKILL.md), [architecture](skills/nest/architecture/SKILL.md), [controllers](skills/nest/controllers/SKILL.md), [database](skills/nest/database/SKILL.md), [dtos](skills/nest/dtos/SKILL.md), [jobs](skills/nest/jobs/SKILL.md), [migrations](skills/nest/migrations/SKILL.md), [security](skills/nest/security/SKILL.md), [tests](skills/nest/tests/SKILL.md) |
| `skills/javascript/` | [domain-driver CLI](skills/javascript/domain-driver/SKILL.md) |
| `skills/next/` | [Next actions](skills/next/actions/SKILL.md) |
| `skills/tanstack-start/` | [TanStack Start actions](skills/tanstack-start/actions/SKILL.md) |
| `skills/frontend/` | Stack-agnostic: [app-shell](skills/frontend/app-shell/SKILL.md), [overlays](skills/frontend/overlays/SKILL.md), [data-display](skills/frontend/data-display/SKILL.md) |
| `skills/quality/` | Stack-agnostic, adapted from Anthropic's official plugins: [simplicity](skills/quality/simplicity/SKILL.md), [review](skills/quality/review/SKILL.md), [security-review](skills/quality/security-review/SKILL.md) |

Earlier capabilities (`general`, `react`, `inertia`, `javascript/node-feature-development`, and the earlier `*-feature-development` skills of each stack) are archived under [`archive/skills/`](archive/skills/). They are not in the catalog and are not distributed. To restore one, move it back under `skills/` and add it to the catalog.

Factory uses its role instructions for discovery, verification, and documentation, and selects additional capabilities from the installed catalog. Archived skills are not prerequisites.

Use `skills/<group>/<skill-name>/SKILL.md` with lowercase, hyphenated names and YAML `name`/`description` frontmatter. Add supporting files only when needed. Register a new capability in the shared catalog; each agent workflow maintains its own role/phase selection rules.

Each stack folder is self-contained so it can ship on its own. Its `actions` skill covers only that framework; stack-agnostic rules live in `skills/quality/`.

## Using these in a project

Nothing is delivered from this repository: no workflow copies these files into other repositories, and no downstream package bundles them. Copy what a project needs by hand.

- **Skills.** Copy `skills/<group>/<name>/` to `.agents/skills/<group>-<name>/`, for example `skills/nest/actions/` to `.agents/skills/nest-actions/`. Set the `name` in the copied `SKILL.md` to the same `<group>-<name>`. Codex reads `.agents/skills/` directly; Claude Code reads `.claude/skills/`, so link or copy the folder there too.
- **Catalog.** Copy `skills/catalog.md` to `.agents/skills/catalog.md`. Factory resolves skills through it; skills listed there but not copied block a job only when that job needs them.
- **Factory.** Copy `agents/factory/` to `.agents/skills/factory/` (and link it from `.claude/skills/factory/`). Its eight role files (`spec-writer.md`, `builder.md`, the four `reviewer-*.md`, `documenter.md`, `approver.md`) are also child agents:
  - Claude Code: `.claude/agents/<name>.md`, with frontmatter `name`, `description`, `tools` (from `claude-tools`), `model` (from `claude-model`) and `effort` (from `claude-effort`), followed by the role's Markdown body.
  - Codex: `.codex/agents/<name>.toml`, with `name`, `description`, `model` (from `codex-model`), `model_reasoning_effort` (from `codex-reasoning-effort`) and the Markdown body as `developer_instructions`.
