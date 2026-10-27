---
name: insights
description: Use when adding, configuring, or running PHP Insights code-quality checks in a Laravel application.
---

# PHP Insights

Applies to: `config/insights.php`, `app/**/*.php`.

## Rules

- `nunomaduro/phpinsights` is a development dependency, run with `php artisan insights`. Preserve existing constraints; a missing package resolves to the latest compatible stable release.
- PHP Insights pulls in `dealerdirect/phpcodesniffer-composer-installer`, which needs a Composer `allow-plugins` entry. Add that exact entry only when no existing plugin policy covers it.
- The baseline is [insights.php](insights.php), copied to `config/insights.php` when the project has none. Keep an existing configuration's local edits.
  - The baseline requires a score of 100 in every category.
  - It enables the private-methods check, which flags the private helper methods that `actions` recommends. Decide per project which rule wins.
- Run Insights on the changed or affected paths and fix findings at their source. Don't add Composer scripts or apply automatic fixes unless asked.

The baseline matches the [City Directory configuration](https://github.com/city-directory/citydirectory/blob/8c5cdb0093067933cb74481d7fb087ca2fb63b98/config/insights.php) at commit `8c5cdb0`.
