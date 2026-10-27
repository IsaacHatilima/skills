---
name: next-feature-development
description: Plan, implement, or review Next.js pages, React boundaries, route handlers, and Server Actions in a touched application.
---

# Build and review Next features

Identify the installed Next version and whether the changed code uses App Router, Pages Router, or both. Pair this with the React skill for touched components. Keep scaffold-tool stack labels separate from the actual server/browser architecture.

Inspect route handlers, API routes, server-only data modules, and `'use server'` actions. The absence of `app/api` or `pages/api` does not prove that all server behaviour lives in an external API.

A framework Server Action is the request adapter, not a reason to invent a second kind of business operation. Parse and validate FormData or other untrusted arguments, then call the project's server-only service/function with a named DTO, such as `updateUser(input: UpdateUserDto)`. The shared `action-architecture` contract applies regardless of the operation's name; a DTO may be a named schema-output type. Primitive/collection exceptions must remain explicitly typed. Do not introduce a Service class solely to match Nest terminology.

Treat every callable server mutation as an input and authorization boundary. Validate untrusted arguments and obtain the caller from trusted server context. A page/layout authentication check does not establish authorization inside a Server Action.

Reuse the project's server data-access layer and permission checks; scope records and fields before serializing data into client props. Keep credentials and server-only dependencies outside the client module graph.

Follow the existing caching and revalidation strategy after mutations. Use APIs supported by the installed version instead of assuming a particular default cache behaviour.

Review both the rendered state and directly callable server operation. If the API really is external, record the actual calls and the enforcement that cannot be verified in this repository.

Reference: Next's [data-security guidance](https://nextjs.org/docs/app/guides/data-security), using the documentation version that matches the project.

