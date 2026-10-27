---
name: controllers
description: Use when adding or changing Laravel controllers or routes, wiring a FormRequest and action to an endpoint, or choosing between an API response, Inertia page, and redirect.
---

# Controllers

Applies to: `app/Http/Controllers/**`, `routes/**`.

## Rules

- A controller method:
  - injects the FormRequest, route-bound models, and actions as parameters;
  - builds input with `Data::fromRequest()`;
  - invokes actions;
  - returns a response.

  Single-action controllers use `__invoke`. Queries, relation loads, and mapping models to arrays belong to actions.
- Without a FormRequest, call `Gate::authorize()` before any action.
- A write endpoint invokes one write action, which composes any related writes itself. When the response needs a representation, a read action builds it from the returned model. Read endpoints may call several read actions.
- Pass actor and parent models explicitly. Never pass request arrays or plucked fields to actions.
- Use separate web and API controllers when their responses differ; both reuse the same actions. Don't choose the response type by inspecting headers.
- Routes:
  - Name route parameters after the bound model, such as `{conversation}` for `Conversation`.
  - Use consistent plural prefixes, and name every route.
  - Group nested routes in `scopeBindings()`.
  - Use `Route::model()` or `resolveRouteBinding()` only when a parameter must resolve differently.
- Never return models or input Data.

## Responses

- **API:**
  - Serialize the Resource with an explicit `data` wrapper and pass it to `ApiResponse::success()` with a translated message.
  - Use status 200 for reads and updates, 201 for synchronous creation, and 202 for queued work. A 204 stays bodyless.
  - Errors are formatted centrally (see `api-responses`).
- **Inertia:** reads render Resource-backed props plus any enum options and page metadata.
- **Web writes:**
  - Redirect with `to_route()` or `back()`.
  - Flash translated feedback only when a deliberate change would otherwise be unclear. Background writes, such as marking a notice read, need none.
- **Authentication:** session-based controllers handle session mechanics here. Token-based APIs follow their own guard.

## Example

Both controllers reuse `CreateUserRequest` (see `requests`), `CreateUserData` (see `data`), and `CreateUser` (see `actions`). `GetUser` is a read action that returns `UserResource::fromModel($user)`.

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Users;

use App\Actions\Users\CreateUser;
use App\Data\Users\CreateUserData;
use App\Http\Requests\Users\CreateUserRequest;
use Illuminate\Http\RedirectResponse;

final class CreateUserController
{
    public function __invoke(CreateUserRequest $request, CreateUser $create): RedirectResponse
    {
        $create->handle(CreateUserData::fromRequest($request));

        return back();
    }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Users;

use App\Actions\Users\CreateUser;
use App\Actions\Users\GetUser;
use App\Data\Users\CreateUserData;
use App\Http\Requests\Users\CreateUserRequest;
use App\Http\Responses\ApiResponse;
use Illuminate\Http\JsonResponse;
use Symfony\Component\HttpFoundation\Response;

final class CreateUserController
{
    public function __invoke(CreateUserRequest $request, CreateUser $create, GetUser $getUser): JsonResponse
    {
        $user = $create->handle(CreateUserData::fromRequest($request));

        return ApiResponse::success(
            resourceResponse: $getUser->handle($user)->wrap('data')->toResponse($request),
            message: __('User created successfully.'),
            status: Response::HTTP_CREATED,
        );
    }
}
```

`wrap('data')->toResponse()` is the Spatie Resource response API. Another Resource implementation uses its own equivalent.

## Verify

- **API:** the five envelope keys; status codes; private fields excluded; 401, 403, 404, and 422 with and without a JSON `Accept` header; pagination; empty 204 bodies.
- **Web:** the Inertia component and props, redirects, and flash only where intended.
- **Routes:** scoped bindings reject a child of another parent.
