---
name: tests
description: Use when writing, choosing, or running tests for a Laravel application, including Pest unit, feature, action, HTTP, and browser tests, and focused or sharded test runs.
---

# Tests

Applies to: `tests/**`, `phpunit.xml*`, `playwright.config.*`.

## Suites

- **`tests/Unit/`:** isolated logic, with no Laravel boot and no database.
- **`tests/Feature/`:**
  - Action tests in `tests/Feature/Actions/{Domain}/` call `handle()` with real typed input and models.
  - HTTP tests are grouped by domain.
  - Scope `RefreshDatabase` to the Feature tests that need it.
- **`tests/Browser/`:**
  - Covers changed user journeys in applications with a frontend.
  - Uses Pest Browser or the existing Playwright Test runner.
  - API-only applications don't need browser tests.
- **Pest 5 conventions:** behaviour-named `test()` cases, named datasets, factories, and states.
  - Pest 5 needs PHP 8.4.
  - If the project can't run it, keep the working runner and report the gap rather than upgrading PHP or Laravel.

## What to test

- Action tests own the deep branches: persisted columns, the returned model or Resource, rollback, side effects, and failures.
- HTTP tests own the wiring: authorization, validation, the action call, and the response.
  - API tests assert the `api-responses` contract.
  - Web tests assert the Inertia component and props, redirects, session errors, and intended flash.
- Browser tests cover what HTTP assertions can't see: client rendering, form errors, navigation, pending states, and JavaScript errors.
- Fake external boundaries: the HTTP client, mail, notifications, storage, and the queue. Keep owned actions, models, and policies real.
- A queue or notification fake proves the dispatch, not the execution. Test the job itself separately (see `jobs`).
- Every test must be able to catch a real regression. Don't test getters, framework behaviour, or documentation wording.

## Running tests

- Run only the tests for the changed behaviour and its direct callers. After the focused checks pass, never run the whole suite again. Rerun only failures and newly affected selections.
- **Test Impact Analysis (TIA):**
  - Make sure `tests/Pest.php` contains `pest()->tia()->locally()->filtered();`. Extend a bare `pest()->tia()` call rather than duplicating it.
  - TIA needs PCOV or Xdebug and a baseline. Without them, run explicit paths with `--no-tia`.
- **Sharding:**
  - Pest 5.3 disables TIA for partial runs, so sharding takes an explicit list of affected files.
  - Give every shard index the same files and the same total, and run all indexes before treating the set as passed.
  - Don't combine `--filter` with `--shard`, and don't rely on `--dirty` to find affected tests.

```sh
./vendor/bin/pest tests/Unit/Users/UserNameTest.php tests/Feature/Users/CreateUserTest.php --no-tia --shard=1/2
./vendor/bin/pest tests/Unit/Users/UserNameTest.php tests/Feature/Users/CreateUserTest.php --no-tia --shard=2/2
npx playwright test 'tests/Browser/users/create-user\.spec\.ts$' --shard=1/1
```

- Report the selected files, shard results, and what couldn't be verified, such as browser runs or production-engine behaviour that SQLite can't prove.

## Browser example

```php
<?php

use App\Models\User;

test('shows the user creation form to an authorized actor', function () {
    $this->actingAs(User::factory()->create());

    visit('/users/create')
        ->assertSee('Create user')
        ->assertPresent('input[name="name"]')
        ->assertPresent('input[name="email"]')
        ->assertNoJavaScriptErrors();
});
```
