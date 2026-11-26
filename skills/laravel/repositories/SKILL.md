---
name: repositories
description: "Use when adding or changing Laravel database queries, writes, relation loads, pagination, locks or transaction boundaries, or moving persistence out of an action or service."
---

# Repositories

Applies to: `app/Repositories/**`, or the repository location recorded in the project's `AGENTS.md`/`CLAUDE.md`. Actions own business operations; repositories own their database access.

## Boundary and shape

- Put application queries, Eloquent writes, relation/count loads, raw SQL, locks and database transaction calls in repositories. Actions constructor-inject repositories and pass the typed data and trusted actor/parent context the operation needs; they do not query, save, delete, refresh or lazy-load models themselves.
- Use purpose-named classes such as `CreateUserRepository`, `ListUsersRepository` and `UserEmailExistsRepository`, grouped by domain. Follow established method names; without another project convention use `final readonly class`, `declare(strict_types=1);` and one fully typed public `handle()`.
- Take normalized Data or specific typed values, never a Request or unchecked request array. Require actor/parent scope explicitly for tenant-owned operations. Do not read `auth()` or `request()` inside a repository.
- Return a model, materialized collection, paginator, scalar or typed read result, as needed by the action. Do not return an unfinished query builder for the caller to execute. Keep Resources, redirects, API envelopes, validation messages and business decisions in their existing layers.
- Use Eloquent directly inside the repository. Do not add generic base repositories, pass-through interfaces or a duplicate query framework just to wrap each model method. Introduce shared query code only when actual callers need it.

Framework-managed lookups remain valid outside repositories: route-model binding, validation's `exists`/`unique`, and the project's authorization/permission APIs. Custom application lookups in a policy or request go through a check/read action backed by a repository; this exception does not allow handwritten SQL in those callers.

## Queries and writes

- Scope every read and write to the trusted tenant, owner or parent before executing it. Resource-level authorization still applies; a permission or a supplied record ID does not prove ownership.
- Select the columns the result needs, including keys needed to match eager-loaded relations. Load the relations and counts required by the Resource in the repository, so building the Resource performs no queries. Batch collection loads rather than querying once per row.
- Keep sort/filter input allowlisted by the FormRequest; the repository maps accepted names to real columns. Bind data values, and never interpolate request input into SQL or raw order expressions.
- Map create/update columns explicitly from typed input. Never pass an entire Data object, `toArray()` result or unchecked attribute bag to Eloquent. Match `#[Fillable]` for mass assignment; privileged fields come from trusted actor/parent context and are assigned explicitly.
- Keep storage conversions, such as password hashing, alongside the persistence mapping, following the model's established casts. Preserve omitted-versus-null semantics in partial updates and skip a write when no fields were supplied.
- Use database constraints for invariants that must survive concurrent requests. An existence check can improve a business error, but does not replace a unique constraint. Translate only understood persistence failures; do not swallow unrelated database errors.

## Atomic operations

Keep related writes inside one repository-owned transaction, with row locks for read-modify-write work where needed. When moving persistence out of an action, preserve the original atomic boundary: several separately committed repository calls are not equivalent to one transaction. Reuse the project's unit-of-work boundary or expose one purpose-specific persistence operation that coordinates the required repository calls; database transaction APIs stay in that persistence boundary.

An action's business decision that depends on locked state must run within the same atomic operation, through that existing boundary, rather than against an unlocked snapshot read beforehand. Do not move all business logic into a repository to hide this requirement.

Side effects that depend on committed data must remain after-commit safe. Reuse queue/message after-commit support or have the persistence boundary register the action's callback. Repositories do not decide which notifications to send, and actions do not add direct `DB::afterCommit()` or transaction calls. An inner repository returning does not prove an outer transaction has committed.

## Examples

`app/Repositories/Users/UserEmailExistsRepository.php` accepts only the value this check needs:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Models\User;

final readonly class UserEmailExistsRepository
{
    public function handle(string $email): bool
    {
        return User::query()->where('email', $email)->exists();
    }
}
```

`app/Repositories/Users/CreateUserRepository.php` owns the explicit storage mapping:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Data\Users\CreateUserData;
use App\Models\User;
use Illuminate\Support\Facades\Hash;

final readonly class CreateUserRepository
{
    public function handle(CreateUserData $data): User
    {
        return User::query()->create([
            'name' => $data->name,
            'email' => $data->email,
            'phone_number' => $data->phoneNumber,
            'password' => Hash::make($data->password),
        ]);
    }
}
```

The matching action checks the repository result, applies the business decision and builds the Resource (see `actions`). The unique email index remains necessary for concurrent inserts.

## Verify

Use focused database-backed tests for query scope, selected attributes and loaded relations, explicit write mappings, partial updates, pagination, uniqueness races, rollback and locking where applicable. Action/HTTP tests exercise the real repository integration. Check that Resource construction runs no queries and that query counts do not grow per returned row. Use the project's isolated test resources and testing schedule (see `tests`).

API details: Laravel's [database transactions](https://laravel.com/docs/13.x/database#database-transactions), [Eloquent relationships](https://laravel.com/docs/13.x/eloquent-relationships#eager-loading) and [pessimistic locking](https://laravel.com/docs/13.x/queries#pessimistic-locking). Repository ownership is this library's architecture rule, not a Laravel framework requirement.
