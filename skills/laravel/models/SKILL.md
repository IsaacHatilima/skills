---
name: models
description: Use when creating or changing an Eloquent model, or its casts, relationships, scopes, fillable columns, or PHPDoc properties.
---

# Models

Applies to: `app/Models/**`.

## Rules

- Models are declarative: relationships, scopes, `casts()`, mass assignment, route keys, constants, and property types.
  - Relationships and scopes build queries but never run them: no `get()`, `first()`, `exists()`, `count()`, or writes.
  - Accessors compute only from loaded attributes.
- Queries, writes, and business behaviour live in actions. Never put them in model helpers, `app/Concerns` traits, events, boot hooks, or observers. Framework lifecycle features stay: UUID generation, timestamps, casts, and authentication traits.
- Entity models use `HasUuids`; pivot and lookup models keep integer keys. Match the real schema, and don't convert existing keys or routes without a planned migration (see `migrations`).
- Declare only the columns that actions mass-assign: `#[Fillable([...])]` on Laravel 13+, or the existing `$fillable` on older versions. Privileged columns stay non-fillable and secrets go in `$hidden` (see `security`). Never use `$guarded = []`.
- Cast string enum columns to their backed enum in `casts()` (see `enums`). Use a custom cast or `Attribute` for value objects, such as money stored in minor units.
- Local scopes are protected `#[Scope]` methods on Laravel 12.4+ and `scopeName()` methods before that.
  - Prefer local scopes called from actions.
  - Reserve a global scope for a filter that every query must have, such as tenant isolation. Never define the same filter both ways.
  - Recoverable records use `SoftDeletes`.
- Every model has a class-level PHPDoc block.
  - Use `@property` for writable attributes and `@property-read` for computed attributes and relations.
  - Types match the casts and nullability. To-many relations use collection generics.

## Workflow

1. Check the installed `laravel/framework` version before choosing `#[Fillable]` or `#[Scope]`. Don't upgrade Laravel for these conventions.
2. For an existing model such as `User`, keep its base class, authentication and notification traits, hidden fields, casts, and route binding. Change only the requested concern.
3. When moving logic out of a helper, observer, or boot hook, put it in an action, update its callers, and keep its transaction and after-commit timing.
4. Verify:
   - key generation;
   - fillable versus protected assignment;
   - casts, relationships, and scopes;
   - reading accessors or Resources runs no extra queries.
