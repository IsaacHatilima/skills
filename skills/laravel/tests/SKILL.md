---
name: tests
description: "Use when writing, choosing, or running tests for a Laravel application, including Pest unit, feature, action, HTTP, and browser tests, or when deciding which tests a change needs."
---

# Tests

Applies to: `tests/**`, `phpunit.xml*`, `playwright.config.*`.

## Suites

- **`tests/Unit/`:** isolated logic, with no Laravel boot and no database.
- **`tests/Feature/`:**
  - Action tests in `tests/Feature/Actions/{Domain}/` call `handle()` with real typed input and models.
  - Repository tests in `tests/Feature/Repositories/{Domain}/` verify database selection, scopes, writes, locking and transaction behaviour.
  - HTTP tests live in `tests/Feature/Http/{Domain}/`.
  - Scope `RefreshDatabase` to the Feature tests that need it.
- **`tests/Browser/`:** changed user journeys in applications with a frontend, using Pest Browser or the existing Playwright runner. API-only applications don't need browser tests.
- Test files mirror the class they cover: `CreateUserAction` is tested in `CreateUserActionTest.php`.
- Use Pest 5 conventions: behaviour-named `test()` cases, named datasets, factories, and states. Pest 5 needs PHP 8.4; if the project can't run it, keep the working runner and report the gap.

## What to test

- Repository tests own persistence details: selected and persisted columns, record/tenant scopes, eager loading, pagination, rollback and locking. Action tests own business decisions and orchestration, the returned model or Resource, side effects and failures; keep database-backed coverage of the combined action/repository flow.
- HTTP tests own the wiring: authorization, validation, the action call, and the response.
  - API tests assert the `api-responses` contract.
  - Web tests assert the Inertia component and props, redirects, session errors, and intended flash.
- Browser tests cover what HTTP assertions can't see: client rendering, form errors, navigation, pending states, and JavaScript errors.
- Fake external boundaries: the HTTP client, mail, notifications, storage, and the queue. Keep owned actions, repositories, models, and policies real in feature tests. Queued work is tested as `jobs` describes.
- Every test must be able to catch a real regression. Don't test getters, framework behaviour, or documentation wording.

## Development loop

During development, run the changed pipeline: the affected request, repository, action, controller, response and user journey, plus callers that can regress. A typo in one controller or action does not require the entire suite on every edit.

- Pass affected tests as explicit paths; use `--filter` for a particular failing behaviour. Include dependent flows when a shared repository, authorization rule or validation contract changes.
- After a fix, rerun the failures and tests of the code the fix touched. Expand that selection when new evidence exposes another affected caller.
- Use the installed runner and the project's existing scripts. Check supported flags before using sharding or parallelism; do not upgrade the runner or add CI configuration solely to copy an example.

For example, adding comments changes the comments pipeline and the post page:

```sh
./vendor/bin/pest tests/Feature/Repositories/Comments tests/Feature/Actions/Comments tests/Feature/Http/Comments tests/Feature/Http/Posts/ShowPostControllerTest.php tests/Browser/Posts
```

## Sharding and the pre-PR run

- Use supported sharding and parallel workers for larger selections and the full suite. Pest supports `--shard=<index>/<total>`; a selected pipeline can be split with the same paths on every worker, for example the command above with `--parallel --shard=1/2`, paired with `--shard=2/2`. A single small test does not need to be split.
- Isolate databases, storage, caches, queues and browser ports by checkout/job, shard and worker. Laravel's parallel testing supplies process tokens and separate test databases within a run; do not assume a token distinguishes separate concurrent runs or shards. Use only the project's disposable test resources; serialize any group whose resources cannot be isolated.
- Before opening a PR, run the complete configured project test suite against the final changes. Remove development path/filter/affected-only selections, and include separately configured browser or frontend suites. Existing CI also runs the full pipeline. Focused development results do not replace this pre-PR run.

For a Pest suite divided into two isolated workers, both commands must pass against the same code:

```sh
./vendor/bin/pest --ci --parallel --shard=1/2
./vendor/bin/pest --ci --parallel --shard=2/2
```

Schedule those shards independently only with isolated resources. Passing one shard is not a full-suite pass; collect every shard's result. If the runner has no sharding support, use its existing full-suite command. Record commands, scope, shard coverage and failures, and report browser or database-engine behaviour that was not exercised. After a narrow review fix, return to the focused loop instead of repeating the whole suite on each edit; run the full pipeline again when the fix changes broad/shared behaviour or project policy requires it.

Sources: [Pest sharding and CI](https://pestphp.com/docs/continuous-integration), [Pest CLI flags](https://pestphp.com/docs/cli-api-reference), and [Laravel parallel testing and database isolation](https://laravel.com/docs/13.x/testing#running-tests-in-parallel). Match commands to the installed versions.
