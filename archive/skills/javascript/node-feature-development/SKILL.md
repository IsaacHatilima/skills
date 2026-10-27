---
name: node-feature-development
description: Plan, implement, or review Node.js route handlers, middleware, and data access in packages without a more specific server framework skill.
---

# Build and review Node server features

Read the runtime version, installed server framework, package scripts, module format, router registration, and error middleware. Do not classify an unknown package as a Node API solely because other framework dependencies are absent.

Use the project's validation, caller-context, action/service, and persistence patterns. Trace middleware ordering so authentication, validation, and error handling actually cover the changed route.

Await work whose failure must reach the request boundary. Follow the installed framework version's asynchronous error behaviour; do not assume Express 4 and Express 5 propagate rejected promises in the same way.

Wire new routes into the real application and match the spec's method, path, body, and response. Fill any generated repository placeholders. Scope data queries to the permitted caller and parameterize untrusted input.

Inspect whether a handler returns JSON, redirects, or rendered HTML. Express templates and other server-rendered pages require UX/UI review when the change affects what a person sees.

Test through the existing request harness, including failed validation, refusals, missing records, and the expected error response. Keep external effects behind the project's test doubles.

Reference for Express projects: [official error-handling guide](https://expressjs.com/en/guide/error-handling.html). Select its version to match the installed package.

