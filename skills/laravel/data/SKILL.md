---
name: data
description: "Use when creating or changing Laravel input Data classes, output Resources, or the frontend-facing representation of a model, including partial updates."
---

# Data

Applies to: `app/Data/**`. Uses `spatie/laravel-data`; if it's missing, install it with Composer. Publish `data-config` only for custom settings.

## Input Data

- Lives in `app/Data/{Domain}/` as `{Operation}Data`, with readonly properties.
- Built only through an explicit, typed `fromRequest()` that the controller calls after the FormRequest has authorized and validated. Don't use automatic request injection, container resolution, or `from($request)`.
- The factory reads only validated, known fields through typed getters such as `$request->string('name')`. It owns domain normalization: trimming, letter case, and turning blank strings into null. Passwords and other opaque values pass through untouched.
- Jobs and commands build the same Data through their own factory.
- An operation that only ever happens as part of a larger create may take that create's Data instead of its own class, such as `CreateProfile::handle(User $user, CreateUserData $data)`.
- Partial-update contracts use [`Optional`](https://spatie.be/docs/laravel-data/v4/as-a-data-transfer-object/optional-properties) properties, so an omitted field differs from an explicit `null`. A table's update grows through one partial-update Data, such as `UpdateUserData` with `string|Optional $email` and later a role, with one factory per form that fills only its fields. The operation writes only the fields that aren't `Optional` (see `repositories`).
- Data is never sent to the frontend or passed wholesale to Eloquent. Actions pass the needed typed input to repositories, which map columns explicitly (see `repositories`).

## Output Resources

- Also live in `app/Data/{Domain}/`, named `{Noun}Resource`, with camelCase properties matching the frontend type and an explicit, typed `fromModel()`.
- A Resource is the outbound shape for API JSON and Inertia props. Formatting and derived values, such as labels, full names, and money from minor units, are computed in `fromModel()`, so controllers and pages receive them ready.
- Read only selected attributes and already-loaded relations or counts. The action obtains them from a repository before building the Resource (see `actions`, `repositories`); Resources never query or lazy-load.

## Example

`app/Data/Users/CreateUserData.php`:

```php
<?php

declare(strict_types=1);

namespace App\Data\Users;

use App\Http\Requests\Users\CreateUserRequest;
use Illuminate\Support\Str;
use Spatie\LaravelData\Data;

final class CreateUserData extends Data
{
    public function __construct(
        public readonly string $name,
        public readonly string $email,
        public readonly ?string $phoneNumber,
        public readonly string $password,
    ) {}

    public static function fromRequest(CreateUserRequest $request): self
    {
        $phoneNumber = trim($request->string('phone_number')->value());

        return new self(
            name: Str::title(trim($request->string('name')->value())),
            email: Str::lower(trim($request->string('email')->value())),
            phoneNumber: $phoneNumber === '' ? null : $phoneNumber,
            password: $request->string('password')->value(),
        );
    }
}
```

`string()` returns an empty string for missing or null input, so a blank phone number becomes `null` after trimming.

`app/Data/Users/UpdateUserData.php` is the one update contract for the `users` table:

```php
<?php

declare(strict_types=1);

namespace App\Data\Users;

use App\Http\Requests\Settings\UpdateEmailRequest;
use Illuminate\Support\Str;
use Spatie\LaravelData\Data;
use Spatie\LaravelData\Optional;

final class UpdateUserData extends Data
{
    public function __construct(
        public readonly string|Optional $email = new Optional(),
    ) {}

    public static function fromEmailRequest(UpdateEmailRequest $request): self
    {
        return new self(email: Str::lower(trim($request->string('email')->value())));
    }
}
```

A later field, such as a role, joins as another `Optional` property with its own factory; the email form still leaves it `Optional`, so it isn't written.

`app/Data/Users/UserResource.php`:

```php
<?php

declare(strict_types=1);

namespace App\Data\Users;

use App\Models\User;
use Spatie\LaravelData\Resource;

final class UserResource extends Resource
{
    public function __construct(
        public readonly string $id,
        public readonly string $name,
        public readonly string $email,
        public readonly ?string $phoneNumber,
    ) {}

    public static function fromModel(User $user): self
    {
        return new self(
            id: (string) $user->getKey(),
            name: $user->name,
            email: $user->email,
            phoneNumber: $user->phone_number,
        );
    }
}
```

## Verify

Tests cover:
- normalization, including blank-to-null;
- ignored extra fields;
- passwords passed through untouched;
- omitted versus `null` on partial updates;
- building a Resource runs no queries.
