# Factory

Factory is a feature-building workflow. [AGENT.md](AGENT.md) coordinates specification, implementation, four reviews, documentation, and approval. The eight child-role definitions live beside it.

```text
/factory <feature request>           Claude Code
$factory <feature request>           Codex
/factory approve <job-id>
/factory rework <job-id> <note>
```

[SKILL.md](SKILL.md) is a thin host command adapter that loads the workflow definition. It is not part of the shared capability library. The adapter's Codex metadata remains in `agents/openai.yaml`; its explicit-invocation policy is preserved.

## Source layout

```text
agents/factory/
  AGENT.md
  SKILL.md
  agents/openai.yaml
  spec-writer.md
  builder.md
  reviewer-security.md
  reviewer-code.md
  reviewer-ux.md
  reviewer-ui.md
  documenter.md
  approver.md
  references/skills.md

skills/
  catalog.md
  <group>/<skill-name>/SKILL.md
```

## Workflow and ownership

The orchestrator owns job state and transitions. The spec-writer owns `spec.md`; the builder owns implementation and `build.md`; reviewers each own their review; the documenter owns its Documentation files; the approver owns `decision.md`.

Four reviews run in parallel, with at most two rebuilds after the initial review. Each job uses a worktree on `factory/<job-id>`. Review verdicts are `PASS` or `CHANGES`; the final decision is `APPROVE` or `ESCALATE`. The existing write boundaries and approval policy stay in the workflow and child-role definitions.

## Shared capabilities

The [shared catalog](../../skills/catalog.md) belongs to all workflows. Factory's [selection rules](references/skills.md) assign those capabilities to its roles. Spec-writer resolves actual paths for the task and records the assignments in `spec.md`; each role reads its assigned files.

| Agent | Shared capabilities |
|---|---|
| spec-writer | Project discovery; relevant stack and access-control/scaffold skills. |
| builder | Architecture, verification, relevant stacks, and conditional access-control/UX/UI/scaffolding. |
| reviewer-code | Architecture, verification, and the applicable stack/scaffold conventions. |
| reviewer-security | Access-control review and skills covering the changed trust boundaries. |
| reviewer-ux | Verification, relevant UX guidance, and frontend stack skills. |
| reviewer-ui | Verification, relevant UI guidance, and frontend stack skills. |
| documenter | Feature documentation. |
| approver | Verification and relevant access-control guidance; its decision policy stays in the agent. |

A Laravel/React/Inertia feature can select all three stack skills. A backend-only Nest fix need not load an untouched client's React skill. UI review follows actual rendered output, including server templates. Missing required skills block the relevant stage; unused groups need not be installed.

Shared skills use the invoking workflow's scope and reporting contract. Another workflow can reuse verification, access-control review, or stack guidance without factory job files.

## Setup and validation limits

These files are source definitions. Host registration/rendering must expose the factory command and its eight child agents. Preserve the bundle's relative files when installing the command adapter, and supply the shared catalog and readable skill-library roots. The original external domain-driver initializer has not been updated for this repository layout.

Child sources retain `name`, `description`, `claude-model`, `claude-tools`, `claude-effort`, `codex-model`, and `codex-reasoning-effort`. Skill loading does not change their model choices or write permissions.

The target project supplies setup/dev/check commands and its chosen scaffolding tools. Domain-driver is used only where selected; Laravel can use existing Artisan/custom tools or an explicit manual strategy.

Runtime job state remains in `.factory/jobs/<job-id>/`, worktrees beside the target repository, and feature documentation under `Documentation/`. A prepared branch document is not deployment evidence.

Format, reference, and routing checks are separate from running a complete feature job. No end-to-end factory job is established by this source refactor.

## Credit

The workflow was imported from `domain-driver/factory`, whose loop was modelled on [zazencodes-season-3](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code). This repository separates that workflow from the reusable skills it consumes.
