---
name: actions
description: "Use when creating, refactoring, or reviewing a Laravel action or operation service that makes a business decision or coordinates reads and writes through repositories."
---

# Actions

Applies to: `app/Actions/**`, or `app/Services/**` in a project that uses services. An action is one business operation.

## Class shape

- Follow the project: `app/Actions/{Domain}/` with an `Action` suffix, or `app/Services/{Domain}/` with a `Service` suffix. A new project with neither uses actions. The rules are the same for both.
- `final readonly class` with `declare(strict_types=1);` and one public, fully typed `handle()`. Name writes with a domain verb (`CreateUserAction`), reads `List{Nouns}Action` or `Get{Noun}Action`, and checks `Is*` or `Has*`.
- Constructor-inject repositories and reused actions; never resolve or construct them inside `handle()`. Keep per-call state in local variables.
- Keep methods small: follow the project's complexity tool, or keep each method at a cyclomatic complexity of 5 or less. Above that, extract private methods that share the caller's transaction.

## Inputs

- Request input arrives as a Data object built by the caller (see `data`); existing records arrive as models. Never accept a Request or a request array.
- Pass the actor and parent models to `handle()`. Never read `auth()`, `request()`, or `#[CurrentUser]` inside an action.
- Small internal values may be typed scalars or PHPDoc-shaped arrays, such as `@param list<string> $userIds`. Use Data once a value needs normalization or crosses boundaries.
- Trust Data's normalization; don't trim or parse again.
- Owner, tenant, and team columns come from the actor or parent, never from input. Every read is scoped to records the caller may see (see `security`).

## Repository calls

- All database access belongs to repositories (see `repositories`): queries, writes, `save()`/`delete()`, relation loads, counts, locks and transaction calls. An action calls the needed repositories with normalized Data or specific typed values and trusted actor/parent context. It never finishes a query builder or triggers lazy loading itself.
- Keep business decisions here. A repository returns records or typed results; the action applies rules and decides what subsequent work is needed. Do not pass an entire request or more data than the repository operation needs.
- Repository calls preserve explicit column mapping, omitted-versus-null updates, tenant scope and database constraints. Ask the repository for exactly the result data and loaded relations required by its caller.
- Preserve atomicity when composing writes: use the project's repository/unit-of-work boundary for one atomic operation, rather than adding `DB::transaction()` here or committing each repository call independently. Decisions based on locked state must run within that boundary.
- Notifications, mail, jobs and events that depend on writes run after commit through the established message/queue support or a callback registered by the persistence boundary. An inner repository returning doesn't mean an outer transaction committed.

## Results and failures

- Return what the caller needs, always typed. Never return an untyped array or `mixed`.
  - The result goes into a response (API JSON or Inertia props): request every needed relation and count from the repository, then return `{Noun}Resource::fromModel()` (see `data`). Building it must not query.
  - The caller keeps working with the record, such as another action or a redirect to its route: return the model.
  - Callers need both: return the model, and the response caller passes it to a `Get{Noun}Action` that returns the Resource.
  - Deletes return `void`; checks return `bool`.
- Repositories select the needed columns; preserve their pagination when mapping results to Resources.
- Broken business rules throw a translated `ValidationException::withMessages()` or a domain exception. Authorization, redirects, JSON, and flash messages belong to the caller.
- Fortify contracts keep their required `array $input` in the adapter, which validates, builds Data, and delegates to an action without querying.

## Example

```php
<?php

declare(strict_types=1);

namespace App\Actions\Users;

use App\Data\Users\CreateUserData;
use App\Data\Users\UserResource;
use App\Repositories\Users\CreateUserRepository;
use App\Repositories\Users\UserEmailExistsRepository;
use Illuminate\Validation\ValidationException;

final readonly class CreateUserAction
{
    public function __construct(
        private UserEmailExistsRepository $emailExists,
        private CreateUserRepository $createUser,
    ) {}

    public function handle(CreateUserData $data): UserResource
    {
        if ($this->emailExists->handle($data->email)) {
            throw ValidationException::withMessages([
                'email' => __('The email has already been taken.'),
            ]);
        }

        $user = $this->createUser->handle($data);

        return UserResource::fromModel($user);
    }
}
```

`CreateUserData` has already lower-cased the email, so the repository check matches stored values; the unique index still guards concurrent inserts. Both repository implementations are shown in `repositories`.

## Verify

Database-backed tests cover the writes or reads, the returned type, explicit column mapping, business failures, and any rollback, locking, after-commit delivery, or pagination. HTTP tests cover authorization and response wiring (see `tests`).
