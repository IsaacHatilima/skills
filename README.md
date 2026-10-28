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
  javascript/              domain-driver CLI guidance
distribution/
  targets.json             downstream subscriptions
scripts/
  sync-skills.mjs          builds and synchronizes consumer bundles
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
| `skills/javascript/` | [domain-driver CLI](skills/javascript/domain-driver/SKILL.md) |
| `skills/next/` | [Next actions](skills/next/actions/SKILL.md) |
| `skills/tanstack-start/` | [TanStack Start actions](skills/tanstack-start/actions/SKILL.md) |
| `skills/frontend/` | Stack-agnostic: [app-shell](skills/frontend/app-shell/SKILL.md), [overlays](skills/frontend/overlays/SKILL.md), [data-display](skills/frontend/data-display/SKILL.md) |
| `skills/quality/` | Stack-agnostic, adapted from Anthropic's official plugins: [simplicity](skills/quality/simplicity/SKILL.md), [review](skills/quality/review/SKILL.md), [security-review](skills/quality/security-review/SKILL.md) |

Earlier capabilities (`general`, `react`, `inertia`, `javascript/node-feature-development`, and the earlier `*-feature-development` skills of each stack) are archived under [`archive/skills/`](archive/skills/). They are not in the catalog and are not distributed. To restore one, move it back under `skills/` and add it to the catalog.

Factory uses its role instructions for discovery, verification, and documentation, and selects additional capabilities from the delivered catalog. Archived skills are not prerequisites.

Use `skills/<group>/<skill-name>/SKILL.md` with lowercase, hyphenated names and YAML `name`/`description` frontmatter. Add supporting files only when needed. Register a new capability in the shared catalog; each agent workflow maintains its own role/phase selection rules.

Each stack folder is self-contained so it can ship on its own. Its `actions` skill covers only that framework; stack-agnostic rules live in `skills/quality/`.

## Distribution

[distribution/targets.json](distribution/targets.json) selects the files each downstream repository receives:

| Destination | Agent bundles | Skill folders | Generated directory |
|---|---|---|---|
| `IsaacHatilima/laracanon` | `agents/factory/**` | `skills/laravel/**` | `resources/agent-library/` |
| `IsaacHatilima/domain-driver` | `agents/factory/**` | Every active group except `laravel` | `agent-library/` |

The [delivery workflow](.github/workflows/sync-skills.yml) runs after relevant changes merge to `main`, or manually from `main`. It builds a complete snapshot for each destination and opens or updates its `chore/sync-skills` PR. A consumer whose generated files have not changed gets no PR. Removing a source file removes it from the next delivered snapshot. `archive/` is excluded.

Factory's bundle stays together, its eight child agents are rendered for Claude Code and Codex, and native skill names include their group (`laravel-actions`, `nest-actions`). Each consumer receives a catalog containing only its delivered skills. The destination installers read `catalog.json`; neither maintains its own authored skill content.

Set the `SKILLS_SYNC_TOKEN` Actions secret in this repository to a fine-grained GitHub token limited to the two destination repositories, with **Contents: read and write** and **Pull requests: read and write**. The source checkout uses its own read-only `GITHUB_TOKEN`. The cross-repository token also lets downstream PR checks run. No credential belongs in this repository's files.

Preview or bootstrap a delivery locally in a destination checkout:

```sh
node scripts/sync-skills.mjs laracanon ../Laracanon
node scripts/sync-skills.mjs domain-driver ../domain-driver
node --test scripts/sync-skills.test.mjs
```

The script owns only the configured generated directory and the explicitly listed legacy skill directories. It replaces old `resources/items/` in Laracanon and `factory/` in domain-driver. Make future skill and agent changes here, then merge the generated downstream PR after review.

For initial setup, merge each consumer's installer migration first. The workflow checks for the required adapter before opening a delivery PR.
