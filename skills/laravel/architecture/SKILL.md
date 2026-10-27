---
name: architecture
description: Use when placing new Laravel behaviour, planning a feature or refactor, or reviewing where queries, validation, authorization, and responses belong.
---

# Architecture

Applies to: `app/**`.

## Boundaries

| Concern | Lives in | Skill |
|---|---|---|
| Authorization and validation | FormRequest, calling a policy | `requests`, `security` |
| Input normalization | Data `fromRequest()` | `data` |
| Queries, writes, transactions, relation loads, business decisions | Action in `app/Actions/{Domain}/` | `actions` |
| Output representation | Resource `fromModel()`, built by a read action | `data` |
| HTTP response: API envelope, Inertia page, redirect | Controller | `controllers`, `api-responses` |
| Background work | Job calling an action | `jobs` |

The flow is FormRequest → `Data::fromRequest()` → action → Resource or model → controller response. Web, API, job, and command callers reuse the same actions.

## Rules

- Only framework lookups may run outside actions: route-model binding, `exists`/`unique` rules, `$request->user()`, Gate, policy and `can()` checks, and Spatie's `hasRole()`/`hasPermissionTo()`. Any other lookup, including one inside a policy, calls an action.
- Data and Resources never query or lazy-load.
- Translate user-facing strings with `__()`.
- New work follows these boundaries. Fix unrelated legacy violations in separate changes.

## Workflow

1. Trace the entry points, authorization, input, database work, output, and response. Find other callers, such as API routes, jobs, and commands, that should share the operation.
2. Assign each responsibility using the table, and open only the skills for the concerns that change.
3. Before coding, check that the contracts line up:
   - request fields match Data properties;
   - the action's signature and return type fit its callers;
   - Resource fields match the frontend types;
   - the response shape matches what the caller expects.
4. Use `plans` when the change needs sequencing. Verify through the real callers and report what remains unverified.
