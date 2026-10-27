---
name: plans
description: Use when writing or reviewing an implementation plan for a Laravel change before coding it.
---

# Plans

Applies to: `docs/superpowers/plans/**`.

## Rules

- A plan states what changes, which contracts are involved, and how completion is verified. It is not a copy of the implementation: no full classes, tests, factories, or components.
- Each task lists:
  - its goal and affected files;
  - inputs and outputs;
  - acceptance behaviours;
  - dependencies and order;
  - material risks;
  - validation commands.
- Name only the contracts that change:
  - request fields and authorization;
  - Data factories, action signatures, and Resource fields;
  - routes, and the response or page props;
  - schema: columns, constraints, indexes, and delete policy.
- Include a code snippet only when it settles a contract, such as an action signature, a request or response shape, a schema constraint, or a tricky query.
- Separate verified current behaviour from proposals and open decisions. Link specs in `docs/superpowers/specs/` and the relevant skills instead of restating them.
- Acceptance checks are observable behaviours: allowed and refused callers, writes and reads, status and output shape, and failure behaviour.
- Never claim that a proposed command has passed. During implementation, update the plan when a contract changes and record the actual validation results.
