---
name: tanstack-start-feature-development
description: Plan, implement, or review TanStack Start routes, server functions, validation, and query updates in a touched application.
---

# Build and review TanStack Start features

Inspect installed Start/Router/Query versions and existing route, loader, server-function, and schema conventions. Pair this skill with React for touched components.

Identify the actual callable server functions, even when their filenames do not follow a `*.fn.ts` convention. Validate network input with the project's existing validator, and ensure the handler or its applied server middleware authenticates and authorizes the caller.

The server-function handler is the request adapter. Map its validated data into the named DTO expected by the project's server-only service or operation function, such as `updateUser(input: UpdateUserDto)`. Use the shared `action-architecture` contract for that business operation; a named schema-output type can be the DTO without adding a class. Primitive/collection exceptions still require concrete types. Do not introduce a Service class just because Nest uses that naming.

Follow the caller and target record into the server data layer. TypeScript inference and a protected client route do not establish permission at the callable server boundary.

Reuse the project's request methods, server context, query keys, and mutation invalidation. A read operation should not mutate state just because the framework allows a convenient call path.

Keep server-only data and dependencies out of the browser graph. Follow established route-generation commands when routes change; do not hand-edit generated route trees.

Test the server function's allowed/refused paths and its client-visible states with the installed project's harness. Record runtime or database prerequisites that prevented those checks.

Reference: [TanStack Start server functions](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions). Check the project's installed version before choosing API syntax.

