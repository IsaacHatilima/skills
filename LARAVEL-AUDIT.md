# Laravel skills audit

Audited and refactored 2026-10-27. Scope: `skills/laravel/`.

## Still open

These need your decision:

- [ ] **Private methods:** `actions` recommends extracting private helper methods. The `insights` baseline enables `ForbiddenPrivateMethods` and requires an architecture score of 100. Either turn off the check or change the guidance. Running Insights on a real project would confirm whether the check fires.
- [ ] **Complexity limit:** `actions` uses a per-method cyclomatic limit of 5 unless the project has its own tool. Insights is that tool, and it measures per class with a limit of 15. Choose which limit applies.
- [ ] **`strict_types` scope:** it's required in action files, and every PHP example now uses it. Insights removes `DeclareStrictTypesSniff`, so nothing enforces it. Decide whether it's required in every file.
- [ ] **`plans`:** it isn't Laravel-specific and assumes the superpowers `docs/superpowers/` paths. Keep it, move it to a general group, or delete it.
- [ ] **`archive/skills/laravel/`:** its unique points (tenant and ownership scoping) now live in `actions` and `security`. Delete it when ready.

Version claims to re-check before shipping:
- Pest 5 needing PHP 8.4, and Pest 5.3's TIA and shard behaviour;
- `#[Scope]` arriving in Laravel 12.4;
- Inertia 3 APIs.

## Resolved

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
