---
name: architecture
description: "Use when placing new Laravel behaviour, naming a new class, planning a feature or refactor, or reviewing where queries, validation, authorization, and responses belong."
---

# Architecture

Applies to: `app/**`. The Laravel skills target Laravel 13. Project guidance (`AGENTS.md`, `CLAUDE.md`) and existing conventions win over their defaults.

## Boundaries

| Concern | Lives in | Skill |
|---|---|---|
| Authorization and validation | FormRequest, using the project's permission API or Gate/policy | `requests`, `security` |
| Input normalization | Data `fromRequest()` | `data` |
| Business decisions and operation orchestration | Action in `app/Actions/{Domain}/`, or service in `app/Services/{Domain}/` | `actions` |
| Database queries, writes, relation loads, locks and transaction boundaries | Repository in `app/Repositories/{Domain}/`, following project layout | `repositories` |
| Output representation and formatting | Resource `fromModel()`, returned by the action | `data` |
| HTTP response: API envelope, Inertia page, redirect | Controller | `controllers`, `api-responses` |
| Background work | Job calling an action | `jobs` |

The flow is FormRequest → `Data::fromRequest()` → action → repository → action result (Resource or model) → controller response. Web, API, job, and command callers reuse the same actions; controllers do not call repositories directly.

## Naming

Without a project convention, a class name ends with its type: `CreateUserAction` (or `CreateUserService`), `CreateUserRepository`, `CreateUserController`, `CreateUserRequest`, `CreateUserData`, `UserResource`, `UserPolicy`, `DetectCommitLanguageJob`, `UserCreatedEvent`, `SendWelcomeEmailListener`, `InvoicePaidNotification`, `WelcomeMail`. Models and enums are plain nouns: `User`, `UserStatus`. Test files mirror the class: `CreateUserActionTest.php`.

## Attributes

Where Laravel 13 offers an attribute instead of a property or method, use it. `models`, `jobs`, `requests`, and `controllers` list theirs. Console commands use `#[Signature]` and `#[Description]` from `Illuminate\Console\Attributes`. Injected values use `Illuminate\Container\Attributes`, such as `#[Config('services.mailer.key')]` and, in controllers, `#[CurrentUser]`.

## Rules

- Only framework-managed lookups may run outside repositories: route-model binding, validation's `exists`/`unique`, the current user and the project's authorization/permission APIs. Custom lookups, including those needed by a policy, go through an action backed by a repository. Actions contain no direct database calls.
- Data and Resources never query or lazy-load.
- Translate user-facing strings with `__()`.
- New work follows these boundaries. Fix unrelated legacy violations in separate changes.

## Workflow

1. Trace the entry points, authorization, input, database work, output, and response. Find other callers, such as API routes, jobs, and commands, that should share the operation.
2. Assign each responsibility using the table, and open only the skills for the concerns that change.
3. Before coding, check that request fields match Data properties, the action's signature and return type fit its callers, Resource fields match the frontend types, and the response shape matches what the caller expects.
4. Verify through the real callers' tests (see `tests`) and report what remains unverified.
