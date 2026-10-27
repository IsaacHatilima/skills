---
name: project-discovery
description: Discover package stacks, project guidance, commands, and applicable skills before planning or running a development, testing, or review workflow.
---

# Discover the project and its skills

Inspect tracked source and manifests before choosing a framework, generator, or skill. A package can have several stacks; a scaffold tool's `--stack` option is not the project's complete architecture.

## Map the work

- Read root guidance, then guidance for each package the request touches. Use `git ls-files` to find manifests, workspace configuration, routes, templates, and existing features. Inspect `composer.json` as well as `package.json` and their lockfiles; use the installed versions when looking up framework APIs.

- Record each touched package's real root, languages, frameworks, feature folders, commands, and server/browser responsibilities. A Laravel app can contain React in the same folder; it does not need a monorepo to have both.

- Detect Nest from `@nestjs/core`, React from `react`, Next from `next`, and TanStack Start from `@tanstack/react-start`. Detect Laravel from `laravel/framework`. Inertia requires evidence such as its server/client adapters and actual Inertia routes; React alone does not imply Inertia.

- Find the actual server boundary: controllers, PHP routes, Next route handlers or Server Actions, TanStack server functions, or a separate API. The absence of an API directory does not make Next frontend-only. Node and Nest can render pages. A build dependency on React does not prove that this task changes React source.

- Read the feature's authentication, data access, response shapes, and neighbouring tests. Identify external APIs from actual calls and configuration, rather than framework labels.

## Resolve skills

Read the shared skill catalog supplied by the invoking workflow and any workflow-specific role or phase mapping. Select skills by the requested task and the packages, capabilities, and files it touches. A Laravel/React/Inertia form can need all three stack skills; a Nest-only server change does not need the client package's React skill.

Resolve each selected skill to a real readable `SKILL.md` using the supplied roots. Prefer the worktree's project-local copy, then explicitly supplied library roots. In a grouped root use the catalog's canonical path; in a flat native skill root use `<skill-id>/SKILL.md`. Do not guess an absolute path, scan unrelated projects, or load every skill in a group.

Record each selected skill's id, package or scope, consuming roles/phases, absolute path, and reason in the invoking workflow's planning or execution artifact. The workflow chooses that artifact and its status format; this skill does not require a feature spec or a particular job folder. If a required skill is unavailable, name its canonical path and report the blocked prerequisite through that workflow. Do not drop an identified stack to bypass a missing required skill. Unused framework groups need not be installed.

## When the workflow needs scaffolding

Use the project's documented, locally available generator and commands. Record its expected stack independently of the detected stacks. Select `domain-driver-scaffolding` only when domain-driver is actually chosen. For Laravel use existing Artisan/project tooling where applicable; an action without a matching generator may follow an explicit manual strategy. Testing and review workflows do not need a scaffolder unless their requested work actually requires generation.

