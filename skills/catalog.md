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

Each stack folder carries its own self-contained action skill: the common operation contract plus that stack's conventions. Select by the runtime that owns the business operation, not every dependency in the repository. A Laravel backend with a React UI uses `laravel/actions`.

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
| laravel/architecture | `laravel/architecture/SKILL.md` | Placing new Laravel behaviour, planning a feature or refactor, or reviewing where queries, validation, authorization, and responses belong. |
| laravel/controllers | `laravel/controllers/SKILL.md` | Adding or changing Laravel controllers or routes, wiring a FormRequest and action to an endpoint, or choosing between an API response, Inertia page, and redirect. |
| laravel/data | `laravel/data/SKILL.md` | Creating or changing Laravel input Data classes, output Resources, or the frontend-facing representation of a model, including partial updates. |
| laravel/eloquent-strictness | `laravel/eloquent-strictness/SKILL.md` | Enabling Eloquent strict mode, or when fixing a lazy-loading, missing-attribute, or discarded-attribute violation or an N+1 query. |
| laravel/enums | `laravel/enums/SKILL.md` | Adding or changing a PHP enum used by a Laravel model, or its stored values, labels, validation, or select options. |
| laravel/frontend | `laravel/frontend/SKILL.md` | Adding or changing React or Inertia pages, page props, Wayfinder routes, forms, or shared UI in a Laravel application's resources/js. |
| laravel/insights | `laravel/insights/SKILL.md` | Adding, configuring, or running PHP Insights code-quality checks in a Laravel application. |
| laravel/jobs | `laravel/jobs/SKILL.md` | Adding or reviewing Laravel queued jobs, listeners, or background work such as exports, reports, webhooks, imports, and notifications, or when a request is slow because it does work the user doesn't need to wait for. |
| laravel/migrations | `laravel/migrations/SKILL.md` | Adding or changing a Laravel migration, table, column, index, foreign key, or schema backfill. |
| laravel/models | `laravel/models/SKILL.md` | Creating or changing an Eloquent model, or its casts, relationships, scopes, fillable columns, or PHPDoc properties. |
| laravel/phpstan | `laravel/phpstan/SKILL.md` | Adding, configuring, or running PHPStan or Larastan static analysis in a Laravel application. |
| laravel/plans | `laravel/plans/SKILL.md` | Writing or reviewing an implementation plan for a Laravel change before coding it. |
| laravel/requests | `laravel/requests/SKILL.md` | Adding or changing a Laravel FormRequest, validation rules, request authorization, or query parameters such as filters, sorting, and pagination. |
| laravel/security | `laravel/security/SKILL.md` | Adding or reviewing Laravel authorization, policies, authentication, API tokens, CORS, CSRF exceptions, file uploads, raw queries, HTML output, rate limits, or production configuration, or before deploying a Laravel application. |
| laravel/tests | `laravel/tests/SKILL.md` | Writing, choosing, or running tests for a Laravel application, including Pest unit, feature, action, HTTP, and browser tests, and focused or sharded test runs. |

## Nest

NestJS conventions adapted from nestjs-best-practices (MIT). Business operations use `nest/actions`.

| Skill id | Canonical path | Use when |
|---|---|---|
| nest/architecture | `nest/architecture/SKILL.md` | Structuring modules, sharing providers, fixing dependency-resolution or circular import errors, choosing provider scopes, injecting interfaces, or decoupling features with events. |
| nest/security | `nest/security/SKILL.md` | Adding or reviewing request validation, guards, JWT and refresh tokens, rate limiting, or responses that could leak entity fields or secrets. |
| nest/api | `nest/api/SKILL.md` | Adding exception filters and domain errors, handling async and event failures, writing interceptors, using built-in pipes, or versioning an HTTP API. |
| nest/data | `nest/data/SKILL.md` | Writing TypeORM or Prisma persistence: transactions, N+1 queries, pagination and indexes, caching, and migrations. |
| nest/testing | `nest/testing/SKILL.md` | Writing unit and e2e tests with TestingModule, provider overrides, supertest, an isolated test database, and faked external services. |
| nest/operations | `nest/operations/SKILL.md` | Setting up validated config, structured logging, lifecycle hooks and graceful shutdown, health checks, BullMQ queues, or microservice message handlers. |

## Frontend

Stack-agnostic interface skills. Combine them with the stack skills for the code in scope.

| Skill id | Canonical path | Use when |
|---|---|---|
| frontend/dashboard-design | `frontend/dashboard-design/SKILL.md` | Designing, building, or reviewing dashboards, admin panels, data tables, activity logs, share/settings popovers, or first-run experiences. |

Other skill groups are archived under `archive/skills/` and are not part of the library. Restore a group to `skills/` and register it here before a workflow selects it.
