---
name: react-feature-development
description: Plan, implement, or review React components, hooks, async data, forms, and role-specific UI in a touched frontend.
---

# Build and review React features

Use the existing router, data layer, component library, and state conventions. Compose this skill with Laravel, Nest, Next, TanStack Start, or Inertia guidance when that code is part of the same feature.

- Keep render logic pure. Derive display values from current props/state rather than storing redundant copies in state with an Effect.

- Put user-triggered mutations in the established event/form workflow. Use Effects for synchronization with external systems, with correct dependencies and cleanup. Cancel or ignore obsolete async results when the component or resource changes.

- Reuse existing query keys, mutation hooks, cache updates, and invalidation. Include the actual resource/tenant scope in keys where the project requires it; avoid stale results crossing between records or actors.

- Match the spec's method, path, payload, and response shape. Loading, empty, validation, failure, and success states must reflect the real request lifecycle.

- Keep permission-based controls consistent with server capabilities. Disabled or hidden controls are presentation, and cannot establish server enforcement.

- Reuse semantic shared controls and established field, overlay, and focus patterns. Test visible outcomes and user interaction rather than internal state variables.

Inspect the existing frontend test runner and development workflow instead of introducing a new one. Browser evidence must say which routes and roles were exercised.

References: React's [Effect guidance](https://react.dev/learn/you-might-not-need-an-effect) and [synchronization and cleanup](https://react.dev/learn/synchronizing-with-effects).

