---
name: controllers
description: "Use when adding or changing Laravel controllers or routes, wiring a FormRequest and action to an endpoint, or choosing between an API response, Inertia page, and redirect."
---

# Controllers

Applies to: `app/Http/Controllers/**`, `routes/**`.

## Controller format

Read the agreed controller format in the project's `AGENTS.md` or `CLAUDE.md`. Both single-action and shared/resource controllers are supported, for web and API endpoints. Keep the documented choice; changing a response type does not require changing the controller format. Before introducing a controller family with no agreed format, settle and document that choice. A small fix in an existing controller does not justify converting it.

| Agreed format | Class and route shape |
|---|---|
| Single-action | One operation per controller, with `__invoke`; route to `CreateUserController::class`. |
| Shared/resource | Related operations in one `UserController`, with methods such as `index`, `show`, `store`, `update` and `destroy`; route to `[UserController::class, 'store']`, or use `Route::resource()` / `Route::apiResource()` for the supported methods. |

`Route::apiResource()` omits the HTML form methods `create` and `edit`. Register only the operations the endpoint actually supports; shared controllers do not require empty CRUD methods. Each shared method stays as thin as a single-action controller.

## Rules

- A controller method:
  - injects the FormRequest, route-bound models, the actor (`#[CurrentUser] User $user`), and actions as parameters;
  - builds input with `Data::fromRequest()`;
  - calls actions;
  - returns a response.

  Database calls and relation loads belong to repositories called by actions (see `repositories`); output formatting belongs to Resources. Controllers do neither.
- Declare controller middleware with `#[Middleware('auth')]` instead of a `middleware()` method. Authorization follows `requests`: Spatie-permission projects use their permission middleware/helper; projects without it use Gate/policies. Without a FormRequest, the latter can use `#[Authorize('view', 'user')]`: the ability, then the route parameter or model class. These controller attributes come from `Illuminate\Routing\Attributes\Controllers`.
- A write endpoint calls one write action, which composes any related writes and returns what the response needs (see `actions`). Read endpoints may call several read actions.
- Pass actor and parent models explicitly. Never pass request arrays or plucked fields to actions.
- Use separate web and API controllers when their responses differ; both reuse the same actions. Don't choose the response type by inspecting headers.
- Routes:
  - Name route parameters after the bound model, such as `{conversation}` for `Conversation`.
  - Use consistent plural prefixes, and name every route.
  - Group nested routes in `scopeBindings()`.
  - Use `Route::model()` or `resolveRouteBinding()` only when a parameter must resolve differently.
- Never return models or input Data.

## Responses

- **API:** pass the action's Resource, wrapped under `data`, to `ApiResponse::success()` with a translated message. Use 200 for reads and updates, 201 for synchronous creation, and 202 for queued work. A 204 stays bodyless. Errors are formatted centrally (see `api-responses`).
- **Inertia:** pass the actions' Resources as props, plus any enum options and page metadata.
- **Blade:** return `view()` with the action's prepared output and page metadata. Templates do not run queries or trigger lazy loading.
- **Web writes:**
  - Redirect with `to_route()` or `back()`.
  - Flash translated feedback only when a deliberate change would otherwise be unclear. Background writes, such as marking a notice read, need none.
- **Authentication:** session-based controllers handle session mechanics here. Token-based APIs follow their own guard.

## Single-action API example

Use this shape when the agreed format is single-action. It reuses `CreateUserRequest` (see `requests`), `CreateUserData` (see `data`), and `CreateUserAction` (see `actions`), which returns a `UserResource`.

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api\Users;

use App\Actions\Users\CreateUserAction;
use App\Data\Users\CreateUserData;
use App\Http\Requests\Users\CreateUserRequest;
use App\Http\Responses\ApiResponse;
use Illuminate\Http\JsonResponse;
use Symfony\Component\HttpFoundation\Response;

final class CreateUserController
{
    public function __invoke(CreateUserRequest $request, CreateUserAction $createUser): JsonResponse
    {
        $user = $createUser->handle(CreateUserData::fromRequest($request));

        return ApiResponse::success(
            resourceResponse: $user->wrap('data')->toResponse($request),
            message: __('User created successfully.'),
            status: Response::HTTP_CREATED,
        );
    }
}
```

`wrap('data')->toResponse()` is the Spatie Resource response API.

## Shared web controller example

Use named methods when the agreed format is shared/resource. This Inertia read and web write reuse the same action boundaries; API methods can use the response envelope shown above.

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Users;

use App\Actions\Users\CreateUserAction;
use App\Actions\Users\ListUsersAction;
use App\Data\Users\CreateUserData;
use App\Data\Users\ListUsersData;
use App\Http\Requests\Users\CreateUserRequest;
use App\Http\Requests\Users\ListUsersRequest;
use App\Models\User;
use Illuminate\Container\Attributes\CurrentUser;
use Illuminate\Http\RedirectResponse;
use Inertia\Inertia;
use Inertia\Response;

final class UserController
{
    public function index(ListUsersRequest $request, #[CurrentUser] User $actor, ListUsersAction $listUsers): Response
    {
        return Inertia::render('users/index', [
            'users' => $listUsers->handle($actor, ListUsersData::fromRequest($request)),
        ]);
    }

    public function store(CreateUserRequest $request, CreateUserAction $createUser): RedirectResponse
    {
        $createUser->handle(CreateUserData::fromRequest($request));

        return to_route('users.index')->with('success', __('User created successfully.'));
    }
}
```

Register it with `Route::resource('users', UserController::class)->only(['index', 'store'])`. For Blade, the read method returns `Illuminate\View\View` and `view('users.index', ['users' => $listUsers->handle($actor, $data)])` instead. In a single-action web project, put the same read or write body in that operation's `__invoke` method. Response channel and controller format are separate decisions.

## Verify

- **Format:** route registration matches the documented single-action or shared/resource format and the actual method names.
- **API:** the five envelope keys; status codes; private fields excluded; 401, 403, 404, and 422 with and without a JSON `Accept` header; pagination; empty 204 bodies.
- **Web:** the Inertia component and props or Blade view and data, redirects, session errors, and flash only where intended.
- **Routes:** scoped bindings reject a child of another parent.

References: Laravel's [single-action controllers](https://laravel.com/docs/13.x/controllers#single-action-controllers) and [resource controllers](https://laravel.com/docs/13.x/controllers#resource-controllers). Match APIs to the project's installed Laravel version.
