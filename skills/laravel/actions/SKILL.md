---
name: actions
description: Use when creating, refactoring, or reviewing a Laravel action or operation service that queries, writes, or makes a business decision.
---

# Actions

Applies to: `app/Actions/**`. An action is one business operation. A project that calls these Services follows the same rules under its own name.

## Class shape

- `final readonly class` in `app/Actions/{Domain}/`, with `declare(strict_types=1);` after `<?php`. If the PHP version or class setup can't support this, report it rather than dropping it.
- One public, fully typed `handle()` method per operation. Name writes with a domain verb (`CreateUser`), reads `List{Nouns}` or `Get{Noun}`, and checks `Is*` or `Has*`.
- Constructor-inject reused actions; never resolve or construct them inside `handle()`. Keep per-call state in local variables.
- Keep methods small. Use the project's complexity tool and threshold; otherwise use a cyclomatic complexity of 5 per method, adding 1 for each `if`, loop, `case` or `match` arm, `catch`, `&&`/`||`, and ternary. Above the limit, extract private methods that share the caller's transaction.

## Inputs

- Request input arrives as a typed Data object built by the caller (see `data`), and existing records arrive as models. Never accept a Request or a request array.
- Pass the actor and parent models explicitly; never read `auth()` or `request()`.
- Small internal values may be typed scalars or arrays with a PHPDoc shape, such as `@param list<string> $userIds`. Switch to Data once a value needs normalization or crosses boundaries.
- Trust Data's normalization; don't trim or parse again.
- Owner, tenant, and team columns come from the actor or parent, never from input. Every read is scoped to records the caller may see (see `security`).

## Persistence

- Map every column explicitly from typed input, in both create and update calls: `'phone_number' => $data->phoneNumber`. Never pass Data, `toArray()`, or an attributes array to Eloquent. The model must allow those columns (see `models`). Storage conversions such as hashing happen here.
- Partial updates write only the supplied fields, keep an allowed explicit `null`, and skip the write when nothing was supplied.
- Related writes share one `DB::transaction()`. Read-modify-write logic locks its rows with `lockForUpdate()` inside that transaction. A single insert needs no transaction.
- Notifications, mail, jobs, and events that depend on the write run after commit, through `DB::afterCommit()` or the queue's `afterCommit` behaviour. An inner action returning does not mean the outer transaction committed.
- A read action may cache an expensive result. The write action that changes the data invalidates that cache after commit, not in a model event.

## Results and failures

- Writes return the model, deletes return `void`, and checks return `bool`.
- Reads select the needed columns, eager-load every relation and count the Resource reads, then map with `Resource::fromModel()`, preserving pagination.
- Broken business rules throw a translated `ValidationException::withMessages()` or a domain exception. Authorization, redirects, JSON, and flash messages belong to the caller.
- Fortify contracts keep their required `array $input` in the adapter. The adapter validates, builds Data, and delegates to an action; it never queries.

## Example

```php
<?php

declare(strict_types=1);

namespace App\Actions\Users;

use App\Data\Users\CreateUserData;
use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

final readonly class CreateUser
{
    public function handle(CreateUserData $data): User
    {
        if (User::query()->where('email', $data->email)->exists()) {
            throw ValidationException::withMessages([
                'email' => __('The email has already been taken.'),
            ]);
        }

        return User::query()->create([
            'name' => $data->name,
            'email' => $data->email,
            'phone_number' => $data->phoneNumber,
            'password' => Hash::make($data->password),
        ]);
    }
}
```

`CreateUserData` has already lower-cased the email, so the check matches stored values. The unique index still guards concurrent inserts.

## Verify

Database-backed tests cover:
- the writes or reads;
- ignored input and explicit column mapping;
- business failures;
- any rollback, locking, after-commit delivery, or pagination involved.

HTTP tests cover authorization and response wiring (see `tests`).
