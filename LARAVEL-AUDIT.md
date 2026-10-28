# Laravel skills audit

Audited and refactored 2026-10-27. Scope: `skills/laravel/`.

## Still open

These need your decision:

- [ ] **Complexity limit:** `actions` uses a per-method cyclomatic limit of 5 unless the project has its own tool. Insights is that tool, and it measures per class with a limit of 15. Choose which limit applies.
- [ ] **`strict_types` scope:** it's required in action files, and every PHP example now uses it. Insights removes `DeclareStrictTypesSniff`, so nothing enforces it. Decide whether it's required in every file.
- [ ] **`archive/skills/laravel/`:** its unique points (tenant and ownership scoping) now live in `actions` and `security`. Delete it when ready.

Version claims to re-check before shipping:
- Pest 5 needing PHP 8.4;
- Inertia 3 APIs.

## Resolved

Change request of 2026-10-28:
- **Private methods:** the baseline lists `ForbiddenPrivateMethods` under `remove`, so private helpers are allowed. A project whose own config forbids them gets the Insights finding, and the agent restructures the code.
- **Config files:** `insights` and `phpstan` follow the project's configuration and never edit it. The baseline is copied only when the project has none.
- **`plans`:** deleted. Planning belongs to the factory's spec-writer.
- **Laravel 13 attributes:** jobs, models, controllers, form requests, commands, and container injection use attributes, checked against the 13.34 source.
- **Naming:** every class except models and enums ends with its type (`CreateUserAction`, `DetectCommitLanguageJob`). Actions live in `app/Actions` or `app/Services`, whichever the project uses.
- **Action results:** an action returns what its caller needs. Results headed for a response return an outbound Resource; a caller that keeps working with the record gets the model.
- **Tests:** only the tests for affected files and flows run. TIA and sharding guidance is removed; CI owns full runs.

Earlier:

- **Duplication:**
  - Each rule now lives in one skill, and the others link to it.
  - The User example is split: each skill shows only the class it owns.
  - The duplicate `CreateUser` and web controller copies are gone.
- **Long code moved to supporting files:** `api-responses/templates/ApiResponse.php`, `api-responses/templates/api-exceptions.php`, `insights/insights.php`, and `phpstan/phpstan.neon`.
- **Contradictions fixed:**
  - Example actions use `final readonly class` with `strict_types`.
  - The `tests` intro no longer claims it changes no configuration.
  - Resources live in `app/Data/{Domain}/` only.
  - Array inputs follow one rule: typed scalars or PHPDoc-shaped arrays are allowed for small internal values, and request payloads always use Data.
- **`actions`:** the generic shared rules and the Laravel rules are merged into one set, and the JavaScript-only wording is gone.
- **Descriptions:** all now say when to use the skill.
- **Leftovers removed:** installer wording, "not an official Spatie skill", the unused `$request->validated()` call, the old `api-responses` rule 5, and the redundant PHPStan exclusions.
- **Gaps filled:**
  - Policies and hardening are in the new `security` skill.
  - Queued work is in the new `jobs` skill.
  - Tenant and ownership scoping is in `actions`.
