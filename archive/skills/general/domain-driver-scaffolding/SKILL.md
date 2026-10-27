---
name: domain-driver-scaffolding
description: Plan, run, or review scaffolding in a package that explicitly uses the locally installed domain-driver generator.
---

# Scaffold with domain-driver

Use this skill only for packages whose implementation plan selects domain-driver. It does not require domain-driver in Laravel or in every other package of a mixed project.

Read the project's installed domain-driver skill and guidance first. Use its package script, or the package manager's command for a locally installed binary, such as `pnpm exec domain-driver` or `npx --no-install domain-driver`. Avoid a command that downloads an unpinned generator.

The invoking workflow records the installed `domain-driver` skill as a dependency for the stages that plan, execute, or review generation. Missing that dependency blocks those stages even if this scaffolding guide is available.

Run each command in its owning package, rather than a monorepo root without an application stack. A project's explicit `--stack` override controls the generator. Compare its printed `Stack:` value to the plan's expected scaffold stack and stop on a mismatch.

For a new feature, use `make:feature <feature>/<Entity> -a` when project guidance permits. Extend an existing feature with `make:action`. Bespoke actions include their noun, such as `archiveComment`; add `--with-input` for a body and `--returns one` or `--returns void` for a non-list result when supported by the installed tool.

Apply the plan's declared generation and cleanup instructions. Remove generated actions only when the project asks for that. Complete repository placeholders, schemas, and any route registration the tool leaves to the caller. Do not assume registration behaviour is the same across stacks.

When the invoking workflow requires a separate scaffold commit, commit only generated output and declared cleanup before implementation, using its commit convention. Review generated output as well as later changes; generated code is not exempt from correctness or permission checks.

Generate later operations with the same declared tool where it supports them. Record extra scaffold commands in the workflow's assigned evidence log. Match generated frontend calls to the real API contract, including response envelopes.

If the required binary, installed skill, or selected operation is unavailable, report the exact prerequisite. Do not substitute a remote download, silently change stacks, or fabricate a successful scaffold.

