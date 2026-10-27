---
name: laravel-feature-development
description: Plan, implement, or review Laravel routes, requests, policies, actions, Eloquent access, and feature tests in a touched PHP application.
---

# Build and review Laravel features

Inspect `composer.json`, `composer.lock`, root guidance, routes, existing actions, policies, and tests. A Laravel app may also contain React, Inertia, or Blade. Select those skills only for the parts the task touches.

The shared `action-architecture` contract applies to the business operation whether the project calls it an Action or a Service. Prefer typed Eloquent models and named DTO/data objects, for example `handle(User $user, UpdateUserData $data): User`. Convert validated Form Request data into the project's DTO before invoking the operation; passing a Form Request or an unstructured validated array is not a substitute. Primitive/collection inputs remain rare, explicitly typed exceptions.

Use the project's documented Artisan or custom scaffolding commands when they fit. If no generator creates the needed action, follow the spec's explicit manual strategy and the neighbouring PHP layout. Laravel does not require domain-driver.

- Use existing Form Requests or validators and pass only permitted, validated fields into the operation. Obtain caller identity from the authenticated request/context; do not mass-assign untrusted ownership or tenant fields.

- Follow policies, gates, or authorized middleware into the action. Route-model binding finds a model; independently verify permission and tenant scope for that model.

- Preserve the project's action/service conventions and Eloquent or repository usage. Do not add layers solely to imitate Nest. Use existing response Resources, redirects, or Inertia responses as the contract requires.

- Keep a multi-write operation inside the project's transaction boundary. Add schema changes through its migration conventions; do not run migrations against shared or production data as incidental verification.

- Scope reads and relation loading to the caller's permitted records, and serialize only fields the response contract allows. Blade and Inertia props require the same server-side permission discipline as JSON APIs.

Use the existing Pest/PHPUnit and frontend commands. Cover invalid data, allowed/refused callers, and observable data changes. Respect the project's database-isolation rules.

Consult documentation matching the installed version: [authorization](https://laravel.com/docs/authorization), [validation](https://laravel.com/docs/validation), and [transactions](https://laravel.com/docs/database#database-transactions).

