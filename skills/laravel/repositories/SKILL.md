---
name: repositories
description: "Use when adding or changing Laravel database queries, writes, relation loads, list search and filters, pagination, locks or transaction boundaries, or moving persistence out of an action or service."
---

# Repositories

Applies to: `app/Repositories/**`, or the repository location recorded in the project's `AGENTS.md`/`CLAUDE.md`. Actions own business operations; repositories own their database access.

## Boundary and shape

- Put application queries, Eloquent writes, relation/count loads, raw SQL, locks and database transaction calls in repositories. Actions constructor-inject repositories and pass the typed data and trusted actor/parent context the operation needs; they do not query, save, delete, refresh or lazy-load models themselves.
- Each persistence operation is its own small class with one fully typed public `handle()`, named for what it does, without a `Repository` suffix: `CreateUser`, `ListUsers`, `UserEmailTaken`, grouped by domain in `app/Repositories/{Domain}/`. Follow established names; without another project convention use `final readonly class` and `declare(strict_types=1);`.
- The domain's entry file, such as `app/Repositories/Users/UserRepository.php`, constructor-injects those classes and exposes one method per operation, such as `create()` and `emailTaken()`, that delegates to its `handle()`. Actions inject only the entry repository: one import and one constructor parameter. A new query is a new operation class plus a method on the entry repository.
- Take normalized Data or specific typed values, never a Request or unchecked request array; the one exception is a list query (see below). Require actor/parent scope explicitly for tenant-owned operations. Do not read `auth()` or `request()` inside a repository.
- Return a model, materialized collection, paginator, scalar or typed read result, as needed by the action. Do not return an unfinished query builder for the caller to execute. Keep Resources, redirects, API envelopes, validation messages and business decisions in their existing layers.
- Use Eloquent directly inside the operation classes. Apart from the entry file, do not add generic base repositories, pass-through interfaces or a duplicate query framework just to wrap each model method. Introduce shared query code only when actual callers need it.

Framework-managed lookups remain valid outside repositories: route-model binding, validation's `exists`/`unique`, and the project's authorization/permission APIs. Custom application lookups in a policy or request go through a check/read action backed by a repository; this exception does not allow handwritten SQL in those callers.

## Queries and writes

- Scope every read and write to the trusted tenant, owner or parent before executing it. Resource-level authorization still applies; a permission or a supplied record ID does not prove ownership.
- Select the columns the result needs, including keys needed to match eager-loaded relations. Load the relations and counts required by the Resource in the repository, so building the Resource performs no queries. Batch collection loads rather than querying once per row.
- Simple lookups use plain Eloquent. A table or list with search, filters or sorts uses `spatie/laravel-query-builder`: the operation takes the validated FormRequest explicitly, `QueryBuilder::for($query, $request)`, allowlists every filter and sort, and never calls `request()`. This is the one exception to "never take a Request". Bind data values, and never interpolate request input into SQL or raw order expressions.
- A query that leaves one record out, such as a uniqueness check on update, takes that record's id under a name that says what it is (`?string $userId = null`), not the model and not a generic `$except`.
- Write by assigning each property from the Data object, then `save()`. Don't use `fill()`, `forceFill()`, or `create([...])` and `update([...])` with attribute arrays: Larastan checks property assignments, not array keys. Never pass an entire Data object, `toArray()` result or attribute bag to Eloquent. Privileged fields come from trusted actor/parent context and are assigned the same way.
- When create and update write the same columns, use one save operation that takes an optional model and starts with `$tenant ??= new Tenant();`, exposed on the entry repository as `save(SaveTenantData $data, ?Tenant $tenant = null)`. When they write different columns, keep separate operations.
- Keep storage conversions, such as password hashing, alongside the persistence mapping, following the model's established casts. Preserve omitted-versus-null semantics in partial updates: write only the fields that aren't `Optional` (see `data`), and skip a write when no fields were supplied.
- Return the saved model without `refresh()`: ids, UUIDs and timestamps are set in PHP. Refresh only for values the database fills, such as a column default or a trigger, and prefer a model `$attributes` default to a refresh.
- When a pivot column must be typed, such as a feature's `limit` on a plan, query the Pivot model with its relation loaded instead of reading `$model->pivot`, which Larastan can't type (see `models`).
- Use database constraints for invariants that must survive concurrent requests. An existence check can improve a business error, but does not replace a unique constraint. Translate only understood persistence failures; do not swallow unrelated database errors.

## Atomic operations

Keep related writes inside one repository-owned transaction, with row locks for read-modify-write work where needed. When moving persistence out of an action, preserve the original atomic boundary: several separately committed repository calls are not equivalent to one transaction. Reuse the project's unit-of-work boundary or expose one purpose-specific persistence operation that coordinates the required repository calls; database transaction APIs stay in that persistence boundary.

An action's business decision that depends on locked state must run within the same atomic operation, through that existing boundary, rather than against an unlocked snapshot read beforehand. Do not move all business logic into a repository to hide this requirement.

Side effects that depend on committed data must remain after-commit safe. Reuse queue/message after-commit support or have the persistence boundary register the action's callback. Repositories do not decide which notifications to send, and actions do not add direct `DB::afterCommit()` or transaction calls. An inner repository returning does not prove an outer transaction has committed.

## Examples

`app/Repositories/Users/UserEmailTaken.php` accepts only the values this check needs:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Models\User;

final readonly class UserEmailTaken
{
    public function handle(string $email, ?string $userId = null): bool
    {
        $query = User::query()->where('email', $email);

        if ($userId !== null) {
            $query->whereKeyNot($userId);
        }

        return $query->exists();
    }
}
```

`app/Repositories/Users/CreateUser.php` owns the explicit storage mapping:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Data\Users\CreateUserData;
use App\Models\User;

final readonly class CreateUser
{
    public function handle(CreateUserData $data): User
    {
        $user = new User();
        $user->name = $data->name;
        $user->email = $data->email;
        $user->phone_number = $data->phoneNumber;
        $user->password = $data->password;
        $user->save();

        return $user;
    }
}
```

The model's `hashed` cast stores the password hashed (see `models`), and the model is returned as saved.

`app/Repositories/Users/ListUsers.php` filters a table through its validated request:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Http\Requests\Users\ListUsersRequest;
use App\Models\User;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Pagination\LengthAwarePaginator;
use Spatie\QueryBuilder\AllowedFilter;
use Spatie\QueryBuilder\QueryBuilder;

final readonly class ListUsers
{
    /** @return LengthAwarePaginator<int, User> */
    public function handle(ListUsersRequest $request, int $perPage): LengthAwarePaginator
    {
        return QueryBuilder::for(User::query()->select(['id', 'name', 'email']), $request)
            ->allowedFilters(
                AllowedFilter::callback('search', fn (Builder $query, string $search) => $query->where(
                    fn (Builder $matches) => $matches
                        ->whereLike('name', '%'.$search.'%')
                        ->orWhereLike('email', '%'.$search.'%'),
                ))->delimiter(''),
            )
            ->orderBy('name')
            ->orderBy('id')
            ->paginate($perPage)
            ->withQueryString();
    }
}
```

`delimiter('')` keeps a search containing a comma as one value. The request allowlists `filter.search` (see `requests`).

`app/Repositories/Users/UserRepository.php` is the entry file the action injects:

```php
<?php

declare(strict_types=1);

namespace App\Repositories\Users;

use App\Data\Users\CreateUserData;
use App\Http\Requests\Users\ListUsersRequest;
use App\Models\User;
use Illuminate\Pagination\LengthAwarePaginator;

final readonly class UserRepository
{
    public function __construct(
        private CreateUser $createUser,
        private ListUsers $listUsers,
        private UserEmailTaken $userEmailTaken,
    ) {}

    public function create(CreateUserData $data): User
    {
        return $this->createUser->handle($data);
    }

    /** @return LengthAwarePaginator<int, User> */
    public function list(ListUsersRequest $request, int $perPage): LengthAwarePaginator
    {
        return $this->listUsers->handle($request, $perPage);
    }

    public function emailTaken(string $email, ?string $userId = null): bool
    {
        return $this->userEmailTaken->handle($email, $userId);
    }
}
```

The matching action injects `UserRepository` alone, checks `emailTaken()`, applies the business decision and builds the Resource (see `actions`). The unique email index remains necessary for concurrent inserts.

## Verify

Use focused database-backed tests for query scope, selected attributes and loaded relations, explicit write mappings, partial updates, list filters, pagination, uniqueness races, rollback and locking where applicable. Action/HTTP tests exercise the real repository integration. Check that Resource construction runs no queries and that query counts do not grow per returned row. Use the project's isolated test resources and testing schedule (see `tests`).

API details: Laravel's [database transactions](https://laravel.com/docs/13.x/database#database-transactions), [Eloquent relationships](https://laravel.com/docs/13.x/eloquent-relationships#eager-loading) and [pessimistic locking](https://laravel.com/docs/13.x/queries#pessimistic-locking), and Spatie's [Query Builder filtering](https://spatie.be/docs/laravel-query-builder/v7/features/filtering). Repository ownership is this library's architecture rule, not a Laravel framework requirement.
