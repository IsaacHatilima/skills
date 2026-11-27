---
name: requests
description: "Use when adding or changing a Laravel FormRequest, validation rules, request authorization, or query parameters such as filters, sorting, and pagination."
---

# Requests

Applies to: `app/Http/Requests/**`.

## Rules

- Every endpoint that accepts input, including GET filters and pagination, has a FormRequest in `app/Http/Requests/{Domain}/`.
  - Name it `{Operation}Request`, such as `CreateUserRequest`.
  - Share a `Save{Noun}Request` only when create and update have identical rules and authorization.
  - Lists use `List{Nouns}Request`.
- A FormRequest only authorizes and validates. It doesn't normalize, build Data, query, write, or build responses.
- Set request options with attributes from `Illuminate\Foundation\Http\Attributes` instead of properties: `#[StopOnFirstFailure]`, `#[ErrorBag('login')]`, `#[RedirectToRoute('users.index')]`.
- Choose authorization from the project's installed stack and documented rules, not a runtime `class_exists()` branch:
  - With `spatie/laravel-permission`, `authorize()` uses its permission API, such as `$this->user()?->hasPermissionTo('users.create') ?? false`, or the project's established permission helper. Use existing permission names and the active guard/team context. Do not replace this with `Gate::allows()` or `$user->can()`, which goes through Gate too. Do not install the package merely to follow this branch.
  - Without that package, `authorize()` calls the policy through `Gate::allows()`, passing the model class for create and the route-bound model otherwise.
  - Permission to perform an operation does not grant access to every record. Preserve the project's record/tenant checks and parent scoping through `scopeBindings()` (see `controllers`); any application lookup behind an authorization check goes through an action/repository, not an inline query.
  - Direct Spatie `hasPermissionTo()` checks do not run `Gate::before()` super-admin overrides. If the project has approved bypass semantics, keep them explicit in its established permission helper and test them. Never silently add a super-admin grant or fall back to Gate to hide the difference.
- Declare explicit rules for every accepted payload and query field, including nested keys.
  - Choose `required`, `nullable`, and `sometimes` so that omitting a field and sending `null` mean what the contract says.
  - For updates, take any model ignored by `unique` from the route, never from a submitted ID.
- Validate user-chosen sort fields against an allowlist with `Rule::in()`. List requests allowlist their filter keys too: `'filter' => ['nullable', 'array:search'], 'filter.search' => ['nullable', 'string', 'max:255']`. The repository maps accepted names to real columns (see `repositories`). Password fields use `Password::defaults()` (see `security`).
- Put checks that need another field or the database in `after()`.
  - It receives injected check actions as typed parameters and returns callbacks; those actions delegate database work to repositories. The FormRequest contains no Eloquent or `DB` calls.
  - Each callback returns early when its prerequisite fields already failed.
  - Checks that need normalized values belong in the action instead.
  - Framework `exists` and `unique` rules are fine.
- Rules used by one request stay inline in its `rules()`. Rules shared by two or more requests, or by a request and a Fortify action, go in a `…ValidationRules` trait such as `app/Concerns/DomainValidationRules.php`. Don't write a custom `Rule` class for checks only requests use.
- A shared check gives each failure its own message. A hostname check, for example, says separately that the name is too long, that one label is too long, that it includes a scheme, port or path, or that it's reserved; never one generic message for several conditions.
- Translate custom `messages()` and `attributes()`. Let Laravel's validation and authorization exceptions reach the web error bag or the central API handler (see `api-responses`). Don't override the failure methods.

## Without Spatie permissions

This FormRequest uses the application's Gate policy because `spatie/laravel-permission` is not part of its authorization stack.

```php
<?php

declare(strict_types=1);

namespace App\Http\Requests\Users;

use App\Models\User;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Support\Facades\Gate;
use Illuminate\Validation\Rules\Password;

final class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return Gate::allows('create', User::class);
    }

    /** @return array<string, list<mixed>> */
    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'email', 'max:255'],
            'phone_number' => ['nullable', 'string', 'max:30'],
            'password' => ['required', 'string', 'confirmed', Password::defaults()],
        ];
    }
}
```

## With Spatie permissions

In a project using `spatie/laravel-permission`, keep the same validation rules and replace the authorization method with the package-backed check below. `users.create` is an example; use the project's actual permission name. The `Gate` import and model-class policy call from the previous example are not needed for this create permission.

```php
public function authorize(): bool
{
    return $this->user()?->hasPermissionTo('users.create') ?? false;
}
```

Use the established project helper instead when it also implements approved guard/team, resource access, or bypass rules. It must preserve those rules explicitly rather than assuming a direct package call runs Gate hooks.

## Verify

Tests cover:
- guests, authorized and forbidden callers, and cross-tenant/record access;
- the selected Spatie permission or Gate-policy path, including any approved bypass and guard/team behaviour;
- each rule's failure, and omitted versus `null`;
- each message of a shared check;
- rejected sort values and unknown filter keys;
- translated errors;
- an `after()` lookup that doesn't run when its prerequisite fields failed.

References: Spatie's [permission checks](https://spatie.be/docs/laravel-permission/v8/basic-usage/direct-permissions) and [Gate versus direct permission checks](https://spatie.be/docs/laravel-permission/v8/basic-usage/super-admin). Use the docs for the installed package version.
