---
name: models
description: "Use when creating or changing an Eloquent model, or its casts, relationships, scopes, fillable columns, or PHPDoc properties."
---

# Models

Applies to: `app/Models/**`.

## Rules

- Models are declarative: attributes, relationships, scopes, `casts()`, constants, and property types.
  - Relationships and scopes build queries but never run them: no `get()`, `first()`, `exists()`, `count()`, or writes.
  - Accessors compute only from loaded attributes.
- Repositories own queries, writes and relation loads; actions own business behaviour. Never put them in model helpers, `app/Concerns` traits, events, boot hooks or observers. Framework lifecycle features stay: UUID generation, timestamps, casts and authentication traits.
- Configure the model with class attributes from `Illuminate\Database\Eloquent\Attributes`, never the matching property or method: `#[Table]`, `#[Fillable]`, `#[Hidden]`, `#[RouteKey]`, `#[UseFactory]`, `#[UsePolicy]`, `#[ObservedBy]`, `#[ScopedBy]`. Add only the ones the model needs. A public property such as `$incrementing` also fails PHP Insights, which forbids public properties on models (see `insights`).
- `#[Fillable]` lists the columns the application writes, which repositories assign as properties (see `repositories`). Privileged columns stay out, and secrets go in `#[Hidden]` (see `security`). Never use `#[Unguarded]` or `$guarded = []`.
- Every model uses `spatie/laravel-activitylog`'s `LogsActivity` unless the task says otherwise. Its `getActivitylogOptions()` returns `LogOptions::defaults()->logFillable()->logOnlyDirty()->dontLogEmptyChanges()`. When `#[Fillable]` includes a secret, such as a password or token, replace `logFillable()` with an explicit `logOnly([...])` that leaves it out.
- A pivot whose columns the application writes, such as a feature's `limit` on a plan, gets its own `Pivot` model, set on the relation with `->using()`. So that activity can point at the row, give its table an incrementing id and configure it with `#[Table(name: 'plan_feature', incrementing: true)]`.
- Entity models use `HasUuids`; pivot and lookup models keep integer keys. Match the real schema, and don't convert existing keys or routes without a planned migration (see `migrations`).
- Cast string enum columns to their backed enum in `casts()` (see `enums`). Use a custom cast or `Attribute` for value objects, such as money stored in minor units.
- Local scopes are protected `#[Scope]` methods, called from repositories. Reserve a global scope, registered with `#[ScopedBy]`, for a filter that every query must have, such as tenant isolation. Never define the same filter both ways.
- Recoverable records use `SoftDeletes`.
- Every model has a class-level PHPDoc block. Use `@property` for writable attributes and `@property-read` for computed attributes and relations. Types match the casts and nullability; to-many relations use collection generics.

## Example

```php
<?php

declare(strict_types=1);

namespace App\Models;

use App\Enums\UserStatus;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;
use Illuminate\Database\Eloquent\Attributes\Scope;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Spatie\Activitylog\Models\Concerns\LogsActivity;
use Spatie\Activitylog\Support\LogOptions;

/**
 * @property string $id
 * @property string $name
 * @property string $email
 * @property string|null $phone_number
 * @property string $password
 * @property UserStatus $status
 */
#[Fillable(['name', 'email', 'phone_number', 'password'])]
#[Hidden(['password', 'remember_token'])]
class User extends Authenticatable
{
    use HasUuids;
    use LogsActivity;

    public function getActivitylogOptions(): LogOptions
    {
        return LogOptions::defaults()
            ->logOnly(['name', 'email', 'phone_number'])
            ->logOnlyDirty()
            ->dontLogEmptyChanges();
    }

    /** @return array<string, string> */
    protected function casts(): array
    {
        return ['password' => 'hashed', 'status' => UserStatus::class];
    }

    /** @param Builder<self> $query */
    #[Scope]
    protected function active(Builder $query): void
    {
        $query->where('status', UserStatus::Active);
    }
}
```

`status` is privileged, so it stays out of `#[Fillable]`; the action decides its value and a repository assigns it explicitly. `password` is fillable but secret, so the activity log names its columns with `logOnly()` instead of `logFillable()`. The namespaces are `spatie/laravel-activitylog` v5's; v4 has `Spatie\Activitylog\Traits\LogsActivity` and `Spatie\Activitylog\LogOptions`.

## Workflow

1. For an existing model such as `User`, keep its base class, authentication and notification traits, hidden fields, casts, and route binding. Change only the requested concern.
2. When moving logic out of a helper, observer or boot hook, put business decisions in an action and persistence in repositories. Update callers and preserve transaction and after-commit timing.
3. Verify:
   - key generation;
   - fillable versus protected assignment;
   - casts, relationships, and scopes;
   - the activity log records the intended columns, and no secret;
   - reading accessors or Resources runs no extra queries.
