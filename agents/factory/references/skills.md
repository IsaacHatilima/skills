# Factory skill selection

The [shared catalog](../../../skills/catalog.md) defines reusable skills and their canonical paths. This file only assigns those skills to factory roles. When installed elsewhere, read the catalog supplied by the workflow's actual skill-library roots rather than assuming the source checkout exists.

The orchestrator resolves `project-discovery` before starting spec-writer. Spec-writer uses this mapping and the shared catalog to resolve the remaining task-relevant files. It records `Skill | Package or scope | Roles | Resolved path | Why` under `## Skills` in `spec.md`, with `Status: READY` or `Status: BLOCKED`.

Every role reads only its assigned skills. Missing required files block implementation or the affected later stage; missing unused framework groups do not. The shared library is read-only during a factory job. Skills do not change write ownership or the workflow's approval policy.

## Shared skill assignments

| Skill id | Assign to | Condition |
|---|---|---|
| project-discovery | spec-writer | Every job; bootstrap before planning. |
| laravel/actions, nest/actions, next/actions, tanstack-start/actions | builder, reviewer-code | The task changes application code. |
| domain-driver-scaffolding | spec-writer, builder, reviewer-code | A touched package explicitly selects domain-driver. |
| feature-verification | builder, reviewer-code, reviewer-ux, reviewer-ui, approver | Evidence for the role's task and acceptance criteria. |
| access-control-review | spec-writer, builder, reviewer-security, approver | Changed entry points, permissions, scoped data, or client/server exposure. |
| ux-review | builder, reviewer-ux | A changed screen, template, or interactive user flow. |
| ui-review | builder, reviewer-ui | A changed visual surface, including server-rendered HTML. |
| feature-documentation | documenter | Every job that reaches documentation. |

When domain-driver is selected, also resolve its installed project-specific `domain-driver` skill and list it for spec-writer, builder, and reviewer-code. Treat its absence as a missing prerequisite.

For a security review without changed access/data boundaries, use the role's baseline diff review. The approver reuses verification and relevant access-control guidance while retaining its own decision policy.

## Stack assignments

Use the shared catalog's stack entries for each touched package or portion of a package. Spec-writer, builder, and reviewer-code read the relevant stack skills. Reviewer-security reads those covering the changed server/client trust boundary. UX/UI reviewers read frontend stack skills only for the surfaces they review.

The documenter and approver do not need every implementation skill just because a package uses that framework. For another stack, use an explicitly available project-specific skill that covers it and record that choice; report a missing required capability rather than substituting an unrelated framework.

Resolve paths with the shared catalog's precedence rules. Record absolute readable files so every fresh child agent uses the same selected copy. Only the factory planning artifact and role assignments are specific to this bundle; other workflows define their own mappings and reports.
