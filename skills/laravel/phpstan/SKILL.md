---
name: phpstan
description: Use when adding, configuring, or running PHPStan or Larastan static analysis in a Laravel application.
---

# PHPStan

Applies to: `phpstan.neon`, `phpstan.neon.dist`, `phpstan.dist.neon`, `app/**/*.php`.

## Rules

- `phpstan/phpstan` (2.0 or newer, which level 10 requires) and `larastan/larastan` are development dependencies. Preserve existing constraints; a missing package resolves to the latest compatible stable release.
- Analyse at `level: 10`. Never lower the level or upgrade other dependencies to make a project pass.
- Use the first existing configuration in PHPStan's discovery order: `phpstan.neon`, `phpstan.neon.dist`, then `phpstan.dist.neon`.
  - Change only `parameters.level`, and never create a second configuration.
  - If the configuration is malformed or the PHPStan version can't support level 10, report it and leave the file unchanged.
- If no configuration exists, copy [phpstan.neon](phpstan.neon) to the application root.
- Run analysis on the changed or affected paths and fix findings at their source. Don't add Composer scripts unless asked.
