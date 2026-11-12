# Agents and skills

Agent bundles define workflows. Shared skills provide capabilities that any workflow can use. One install sets them up for Claude Code and Codex, on macOS or Linux.

## Quick start

```bash
git clone https://github.com/IsaacHatilima/skills.git ~/skills
~/skills/install --list               # see the bundles
~/skills/install web api              # install for your account (see Installing for one project)
```

Then start a new Claude Code or Codex session: they load skills, agents and commands only when a session starts. The skills are ready to use. To use the [factory](agents/factory/README.md) in a project, run `/factory setup` there once (`$factory setup` in Codex), push the commit it makes, and give it work with `/factory run` or `/factory add a login page`.

```text
install                    installs bundles of skills, and the factory, for your account or a project
bundles.json               the bundles: basic, web, laravel, api, all
scripts/
  sync-brand-colours       refreshes brand/identity's colour library, generator and reference systems
agents/
  factory/
    AGENT.md               factory orchestrator
    SKILL.md               thin /factory command adapter
    intake.md, builder.md  factory child-agent roles, one file each
    ...
    bin/                   job, gate, route: the factory's deterministic stages
    templates/             config.json, checks.sh, dashboard.html for a project
skills/
  catalog.md               shared capability index
  laravel/                 actions, controllers, data, models, requests, tests, ... (Laravel 13)
  nest/                    actions, controllers, dtos, database, migrations, ...
  next/                    actions
  tanstack-start/          actions
  frontend/                app-shell, overlays, data-display
  quality/                 simplicity, review, thermo-nuclear-review, deslop, security-review
  typescript/              best-practices
  brand/                   identity: brand.py, the colour library and generator, reference systems
  planning/                grilling (Matt Pocock's grill-me)
  javascript/              domain-driver CLI guidance
tests/                     python3 -m unittest discover -s tests
```


## Agent workflows

[Factory](agents/factory/README.md) builds GitHub issues labeled `factory` into reviewed, documented pull requests: intake, specification, implementation, a scripted gate, routed reviews, documentation, and approval. It is adapted from the ZazenCodes software factory v2 and, like the original, licensed under the [GPLv3](agents/factory/LICENSE).

After [installing it](#installing), run `/factory setup` once in a project, then `/factory run` in Claude Code. Codex invokes skills with `$`, so there it is `$factory setup` and `$factory run`. `/factory add a login page` files that request as an issue and builds it. `AGENT.md` owns the workflow; `SKILL.md` adapts it to hosts that expose commands through skills. It is outside the shared capability library.

Add future workflows under `agents/<name>/`, with an `AGENT.md` entrypoint and the roles or command adapter they need. An E2E or security-testing workflow can work directly on existing code and reuse the shared library.

## Shared skills

The [catalog](skills/catalog.md) lists reusable capabilities and path-resolution rules. Each workflow selects the skills relevant to its scope and determines its own report and completion contracts.

| Location | Capabilities |
|---|---|
| `skills/laravel/` | Laravel 13 conventions: [actions](skills/laravel/actions/SKILL.md), [api-responses](skills/laravel/api-responses/SKILL.md), [architecture](skills/laravel/architecture/SKILL.md), [controllers](skills/laravel/controllers/SKILL.md), [data](skills/laravel/data/SKILL.md), [eloquent-strictness](skills/laravel/eloquent-strictness/SKILL.md), [enums](skills/laravel/enums/SKILL.md), [frontend](skills/laravel/frontend/SKILL.md), [insights](skills/laravel/insights/SKILL.md), [jobs](skills/laravel/jobs/SKILL.md), [migrations](skills/laravel/migrations/SKILL.md), [models](skills/laravel/models/SKILL.md), [phpstan](skills/laravel/phpstan/SKILL.md), [requests](skills/laravel/requests/SKILL.md), [security](skills/laravel/security/SKILL.md), [tests](skills/laravel/tests/SKILL.md) |
| `skills/nest/` | NestJS conventions for Drizzle (or an existing Prisma setup) and Zod: [actions](skills/nest/actions/SKILL.md), [api-responses](skills/nest/api-responses/SKILL.md), [architecture](skills/nest/architecture/SKILL.md), [controllers](skills/nest/controllers/SKILL.md), [database](skills/nest/database/SKILL.md), [dtos](skills/nest/dtos/SKILL.md), [jobs](skills/nest/jobs/SKILL.md), [migrations](skills/nest/migrations/SKILL.md), [security](skills/nest/security/SKILL.md), [tests](skills/nest/tests/SKILL.md) |
| `skills/javascript/` | [domain-driver CLI](skills/javascript/domain-driver/SKILL.md) |
| `skills/next/` | [Next actions](skills/next/actions/SKILL.md) |
| `skills/tanstack-start/` | [TanStack Start actions](skills/tanstack-start/actions/SKILL.md) |
| `skills/frontend/` | Stack-agnostic: [app-shell](skills/frontend/app-shell/SKILL.md), [overlays](skills/frontend/overlays/SKILL.md), [data-display](skills/frontend/data-display/SKILL.md) |
| `skills/quality/` | Stack-agnostic: [simplicity](skills/quality/simplicity/SKILL.md), [review](skills/quality/review/SKILL.md), [thermo-nuclear-review](skills/quality/thermo-nuclear-review/SKILL.md) and [deslop](skills/quality/deslop/SKILL.md) (from Cursor), [security-review](skills/quality/security-review/SKILL.md) (with Cloudflare's attack-class checklists) |
| `skills/typescript/` | [best-practices](skills/typescript/best-practices/SKILL.md) (from pstack): unions, brands, boundary parsing, no casts |
| `skills/planning/` | [grilling](skills/planning/grilling/SKILL.md) (Matt Pocock's grill-me): rounds of questions with recommended answers until a plan has no open decisions |
| `skills/brand/` | [identity](skills/brand/identity/SKILL.md): composes a brand's colour system and guidelines from the [brand-colours](https://github.com/IsaacHatilima/brand-colours) library, then theming, typography, logo, BRAND.md |

Factory uses its role instructions for discovery, verification, and documentation, and selects additional capabilities from the installed catalog.

Use `skills/<group>/<skill-name>/SKILL.md` with lowercase, hyphenated names and YAML `name`/`description` frontmatter. Add supporting files only when needed. Register a new capability in the shared catalog; each agent workflow maintains its own role/phase selection rules.

Each stack folder is self-contained so it can ship on its own. Its `actions` skill covers only that framework; stack-agnostic rules live in `skills/quality/`.

## Installing

On a new machine, clone this repository and install the bundles you use. It needs `git` and `python3` 3.10 or later. Everything goes into your home directory, for every project, unless you pass `--project`.

```bash
./install --list                      # the bundles and what they hold
./install basic                       # factory, planning, quality, TypeScript, brand
./install web                         # basic plus frontend, domain-driver, Next, TanStack Start (Vite apps too)
./install web api                     # several bundles install their union, such as a Vite or Next app with a Nest API
./install laravel                     # basic plus the Laravel and frontend skills
./install all                         # everything in this repository
./install basic --project ~/code/app  # into one project instead of your account
./install basic --host codex          # only Codex (or --host claude)
```

The installer copies files, so the clone isn't needed afterwards. To install without keeping one:

```bash
tmp=$(mktemp -d) && git clone --depth 1 https://github.com/IsaacHatilima/skills.git "$tmp" && "$tmp/install" web api; rm -rf "$tmp"
```

Bundles live in [bundles.json](bundles.json). Each lists skill patterns (`quality/*`, `brand/identity`, `*`), the workflows it brings (`factory`), and other bundles it `include`s. Add a skill to the library and to the catalog, then to the bundles that should carry it; `./install --list` and the tests fail on a pattern that matches nothing.

Every skill has one copy, in `.ai/skills/` (`~/.ai/skills/` for your account), which Laravel Boost also reads. Claude Code and Codex find it through a managed block that the installer writes into the project's `AGENTS.md` and `CLAUDE.md` (or `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md`): where the skills are, and each installed skill with its "use when". Everything outside the block is left as it is, and a `CLAUDE.md` that imports `@AGENTS.md` gets no second copy of it.

- **Skills.** Each `skills/<group>/<name>/` becomes `.ai/skills/<group>-<name>/`, with that `name`.
- **Catalog.** `skills/catalog.md` goes to `.ai/skills/catalog.md`. The factory resolves skills through it; a catalog skill that isn't installed blocks a job only when that job needs it.
- **Factory.** A bundle with the `factory` workflow puts the factory in `.ai/skills/factory/`. Claude Code and Codex register commands only from their own folders, so `.claude/skills/factory/SKILL.md` (`/factory`) and `.agents/skills/factory/SKILL.md` (`$factory`) are short pointers to it. Its nine roles become `.claude/agents/<name>.md` (with `tools`, `model` and `effort` from `claude-tools`, `claude-model` and `claude-effort`) and `.codex/agents/<name>.toml` (with `model` and `model_reasoning_effort` from `codex-model` and `codex-reasoning-effort`, and the Markdown body as `developer_instructions`). Then run `/factory setup` once in each project.

Existing files that differ are left alone unless you pass `--force`. Pull this repository and rerun the same command to update.

### After installing

- **Start a new session.** Claude Code and Codex read `CLAUDE.md`, `AGENTS.md`, agents and commands when a session starts, so an open session won't see the install.
- **Skills need nothing else.** Agents read the block in the instruction files and open the skill a task needs.
- **The factory needs `/factory setup` once per project**, run from either tool. The project must be on GitHub with `gh` signed in. Setup writes `factory/config.json`, `factory/checks.sh` and the dashboard, creates the labels, adds a factory section to `AGENTS.md`, checks that `checks.sh` passes, and commits. Push that commit before the first `/factory run`, because jobs branch from `origin/<base>`.
- **Claude Code and Codex share it.** One install covers both, and setup's files serve both. Run the factory from one of them at a time per project, because two orchestrators can pick up the same job. The dashboard's cost counts only Claude Code agents.
- **Worktrees see only what their branch has.** A project install exists only on branches that contain its commit, so a thread working in another worktree won't find it. When you work in many worktrees, as T3 Code does, install for your account instead.

## Brand colours

`brand/identity` carries a copy of the [brand-colours](https://github.com/IsaacHatilima/brand-colours) library (948 colours), its system generator, and its 32 reference systems, so it works offline. Agents pick four library colours with `brand.py pick` and build a full, contrast-audited system and guideline document with `brand.py build`. When brand-colours changes, refresh the copy and reinstall:

```bash
scripts/sync-brand-colours            # or --source ~/code/brand-colours for a local checkout
git add skills/brand && git commit -m "chore: sync brand colours"
./install basic --force
```

## Tests

```bash
python3 -m unittest discover -s tests
```

They cover the factory's scripts end to end, the installer and bundles, the brand sync, and the library's consistency: every skill in the catalog, names matching folders, and links that resolve.
