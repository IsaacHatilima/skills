# Shared skill catalog

Any workflow can select skills from this library. Selection depends on its task, target packages, and required capabilities; a workflow does not need to run another workflow first. The invoking workflow defines its own steps, roles, report paths, and completion rules.

## Resolve skill files

Canonical paths below are relative to the library root containing this `catalog.md`. In this repository that root is `skills/`. Workflows pass the actual catalog path and available library roots to their agents.

Resolve a selected skill in this order:

1. A project-local copy in the target worktree's `.agents/skills/`, `.claude/skills/`, or `.ai/skills/`, using the group-prefixed folder name, such as `laravel-actions/SKILL.md`.
2. Supplied library roots in their stated order. Use the canonical grouped path, or the group-prefixed folder name in a flat native root.

Read the actual file and record its absolute path. Conflicting copies at the same priority require an explicit selection. Library roots outside the target worktree are read-only inputs. Do not infer another checkout's location or load every skill in a group.

Report a missing required skill through the invoking workflow's blocked/reporting contract, naming the skill and canonical path. Missing unused groups do not block a task. Project guidance takes precedence over defaults; skill selection does not expand write ownership or authorize external effects.

## Skill ids

A skill id is `<group>/<name>`, which is its folder path under the library root. Names are only unique within a group, so a flat install into a project must prefix them with the group (`laravel-actions`, `nest-actions`) to avoid collisions.

## Stack actions

Each stack folder has its own action skill, written only for that framework. Select by the runtime that owns the business operation, not every dependency in the repository. A Laravel backend with a React UI uses `laravel/actions`.

| Stack | Skill id | Canonical path |
|---|---|---|
| Laravel | laravel/actions | `laravel/actions/SKILL.md` |
| Nest | nest/actions | `nest/actions/SKILL.md` |
| Next | next/actions | `next/actions/SKILL.md` |
| TanStack Start | tanstack-start/actions | `tanstack-start/actions/SKILL.md` |

## Laravel

Laravel conventions, originally ported from Laracanon. Each skill lists the paths it applies to. Business operations use `laravel/actions`.

| Skill id | Canonical path | Use when |
|---|---|---|
| laravel/actions | `laravel/actions/SKILL.md` | Creating, refactoring, or reviewing a Laravel action or operation service that queries, writes, or makes a business decision. |
| laravel/api-responses | `laravel/api-responses/SKILL.md` | Adding or changing a Laravel JSON API endpoint, its response envelope or pagination output, or how API errors such as 401, 403, 404, 422, 429, and 500 are rendered. |
| laravel/architecture | `laravel/architecture/SKILL.md` | Placing new Laravel behaviour, naming a new class, planning a feature or refactor, or reviewing where queries, validation, authorization, and responses belong. |
| laravel/controllers | `laravel/controllers/SKILL.md` | Adding or changing Laravel controllers or routes, wiring a FormRequest and action to an endpoint, or choosing between an API response, Inertia page, and redirect. |
| laravel/data | `laravel/data/SKILL.md` | Creating or changing Laravel input Data classes, output Resources, or the frontend-facing representation of a model, including partial updates. |
| laravel/eloquent-strictness | `laravel/eloquent-strictness/SKILL.md` | Enabling Eloquent strict mode, or when fixing a lazy-loading, missing-attribute, or discarded-attribute violation or an N+1 query. |
| laravel/enums | `laravel/enums/SKILL.md` | Adding or changing a PHP enum used by a Laravel model, or its stored values, labels, validation, or select options. |
| laravel/frontend | `laravel/frontend/SKILL.md` | Adding or changing React or Inertia pages, page props, Wayfinder routes, forms, or shared UI in a Laravel application's resources/js. |
| laravel/insights | `laravel/insights/SKILL.md` | Adding or running PHP Insights in a Laravel application, or when Insights reports a finding. |
| laravel/jobs | `laravel/jobs/SKILL.md` | Adding or reviewing Laravel queued jobs, listeners, or background work such as exports, reports, webhooks, imports, and notifications, or when a request is slow because it does work the user doesn't need to wait for. |
| laravel/migrations | `laravel/migrations/SKILL.md` | Adding or changing a Laravel migration, table, column, index, foreign key, or schema backfill. |
| laravel/models | `laravel/models/SKILL.md` | Creating or changing an Eloquent model, or its casts, relationships, scopes, fillable columns, or PHPDoc properties. |
| laravel/phpstan | `laravel/phpstan/SKILL.md` | Adding or running PHPStan or Larastan in a Laravel application, or when PHPStan reports an error. |
| laravel/requests | `laravel/requests/SKILL.md` | Adding or changing a Laravel FormRequest, validation rules, request authorization, or query parameters such as filters, sorting, and pagination. |
| laravel/security | `laravel/security/SKILL.md` | Adding or reviewing Laravel authorization, policies, authentication, API tokens, CORS, CSRF exceptions, file uploads, raw queries, HTML output, rate limits, or production configuration, or before deploying a Laravel application. |
| laravel/tests | `laravel/tests/SKILL.md` | Writing, choosing, or running tests for a Laravel application, including Pest unit, feature, action, HTTP, and browser tests, or deciding which tests a change needs. |

## Nest

NestJS conventions for Prisma and Zod, with the file layout domain-driver generates. Business operations use `nest/actions`.

| Skill id | Canonical path | Use when |
|---|---|---|
| nest/actions | `nest/actions/SKILL.md` | Creating or reviewing a class that runs one business operation: its input, actor, transaction, side effects, and return value. |
| nest/api-responses | `nest/api-responses/SKILL.md` | Changing the response envelope, exception filter, error codes, or paginated output, or how validation, auth, Prisma, and unexpected errors reach the client. |
| nest/architecture | `nest/architecture/SKILL.md` | Adding a feature or module, deciding where code belongs, sharing providers, fixing dependency-resolution or circular-import errors, using events, or setting up config validation, logging, and shutdown. |
| nest/controllers | `nest/controllers/SKILL.md` | Adding or changing a controller or route, wiring DTOs, pipes, and guards, choosing an HTTP method or status, or reading the actor. |
| nest/database | `nest/database/SKILL.md` | Setting up Prisma, changing schema conventions, writing repository queries, fixing N+1 queries or over-fetching, using transactions, or paginating. |
| nest/dtos | `nest/dtos/SKILL.md` | Creating Zod request schemas and DTOs, query or path validation, or partial updates, or deciding what an endpoint returns and how a Prisma result becomes it. |
| nest/jobs | `nest/jobs/SKILL.md` | Adding BullMQ background work or recurring jobs, or when a request is slow because of work the client needn't wait for. |
| nest/migrations | `nest/migrations/SKILL.md` | Changing Prisma models or constraints, writing backfills, or running migrations locally, in CI, or in production. |
| nest/security | `nest/security/SKILL.md` | Adding or reviewing auth and permission guards, public routes, ownership and tenant scoping, rate limits, CORS and helmet, JWT and refresh tokens, passwords, or secrets. |
| nest/tests | `nest/tests/SKILL.md` | Writing or running unit and e2e tests, using an isolated Prisma test database, overriding providers, or deciding which tests a change needs. |

## Frontend

Stack-agnostic interface skills. Combine them with the stack skills for the code in scope.

| Skill id | Canonical path | Use when |
|---|---|---|
| frontend/app-shell | `frontend/app-shell/SKILL.md` | Building or reviewing the frame around signed-in screens: the route after login, sidebar, header, page layout, density, and page-level loading, empty, and error states. |
| frontend/overlays | `frontend/overlays/SKILL.md` | Choosing, building, or reviewing dialogs, drawers, sheets, popovers, menus, tooltips, toasts, and confirmations: what opens them, focus, dismissal, stacking, and mobile behaviour. |
| frontend/data-display | `frontend/data-display/SKILL.md` | Designing, building, or reviewing data tables, lists, activity or audit logs, timelines, KPI tiles, and summary charts. |

## Quality

Stack-agnostic skills for writing and reviewing any change. Combine them with the stack skills for the code in scope.

| Skill id | Canonical path | Use when |
|---|---|---|
| quality/simplicity | `quality/simplicity/SKILL.md` | Writing, refactoring, or reviewing code that should be easy for the next developer to read. |
| quality/review | `quality/review/SKILL.md` | Reviewing a diff, branch, or pull request and deciding what blocks the merge. |
| quality/security-review | `quality/security-review/SKILL.md` | Reviewing a change for security problems and deciding which ones block the merge. |

Other skill groups are archived under `archive/skills/` and are not part of the library. Restore a group to `skills/` and register it here before a workflow selects it.
