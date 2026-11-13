---
name: domain-driver
description: Scaffold domain-driven feature folders with the domain-driver CLI. Use when creating a feature, adding a layer (types, schema, repository, service, controller, component, container, hook) to an existing feature, or adding any operation beyond List, Show, Create, Update, and Delete.
---

# domain-driver

Every feature lives in one folder, and every action in every layer is one file. Use the CLI to create files; write the logic inside them by hand.

The flow is **page -> hook -> API -> service -> repository**, with schemas and types used along the way. Services and repositories sit behind the API, on the server. The hook calls the endpoint directly, so there is no client-side service or repository.

## Detect the stack

The tool reads `package.json` and prints `Stack: <stack> (detected), root: <dir>` before every command. Stacks: `next-fullstack`, `next-frontend`, `react`, `node` (Express, Fastify, Hono, or none), `nest`, `tanstack-start`. Override with `--stack <name>` if detection is wrong. A Vite app with React and no Next.js, such as [vite-dashboard-starter](https://github.com/IsaacHatilima/vite-dashboard-starter), is the `react` stack: components, containers, hooks, schemas and types in the feature, with hooks calling an API that lives outside the project.
Where features are written can be overridden too: `--root <dir>` for one command, or a `domainDriver.featureRoot` key in `package.json` for the project. Read the root off the stack line rather than assuming the convention.
On Nest the tool registers what it generates: the feature module in the root module (from 0.9.2, in `<root>/<root>.module.ts` when `--root` names an area folder that has one), and controllers, services and repositories in `<feature>.module.ts`. Do not add those by hand — it prints what it registered, and prints the lines to paste when it cannot. A bespoke action controller is placed before `Show<Entity>Controller` so its route is not swallowed by `/:id`.

## Commands

| Task | Command |
|---|---|
| New feature with every layer | `npx domain-driver make:feature users/User -a` |
| New feature, folders only | `npx domain-driver make:feature users` |
| Entity interface | `npx domain-driver make:types users/User` |
| Create and Update schemas (and Nest DTOs) | `npx domain-driver make:schema users/User` |
| Five repositories | `npx domain-driver make:repository users/User` |
| Five services | `npx domain-driver make:service users/User` |
| Five controllers or Next route handlers | `npx domain-driver make:controller users/User` |
| A bespoke operation | `npx domain-driver make:action users/User findActiveUsers` |
| Bespoke operation with a request body | `npx domain-driver make:action users/User archiveUser --with-input --returns one` |
| Component, container, hook | `npx domain-driver make:component users/UserCard`, `make:container users/UserContainer`, `make:hook users/User` |

`make:service` and `make:repository` generate the server side only, because that is the only side there is. They are unavailable on `next-frontend` and `react`, whose API lives outside the project; on those stacks the hook is the whole client.

Hooks are one file per action — `<Action><Entity>.hook.ts` exporting `use<Action><Entity>` — never a combined `use<Entity>.ts`. On `tanstack-start` they are TanStack Query hooks backed by a generated `<feature>.keys.ts`; elsewhere they are plain React state. From 0.9.1 the plain-state query hook keeps one result tagged with its request and derives `loading` and `error` from it, so it passes `eslint-plugin-react-hooks` 7 (`react-hooks/set-state-in-effect`). Keep that shape when you extend a hook: set state only in the request's callbacks or in event handlers, never synchronously in an effect. Older versions generate hooks that fail the rule; upgrade domain-driver rather than working around them. Never defer the call with `queueMicrotask` or `setTimeout`, or disable the rule, to get past the linter.

## Rules

1. **Scaffold before writing.** If a file the tool can generate does not exist yet, generate it. Do not create `services/FindActiveUsers.service.ts` by hand.
2. **One action, one file, every layer.** A new operation is a `make:action`, never a new method on an existing action class and never a branch inside Show or List. One file per action is not one copy per action: when two actions share a lifecycle, such as archive and restore hooks that differ only in their endpoint, they call one shared helper instead of repeating it.
3. **Keep the chain.** page -> hook -> API -> service -> repository. The hook calls the endpoint itself. A controller or route handler validates input and calls one service, a service calls one repository, and repositories do data access only. Never put a service or a repository in front of a `fetch`. On `next-fullstack` with Server Actions (`next/actions`), the chain is page -> Server Action -> service -> repository: delete the route handler and the fetch hook a command generates for that operation, and write the action in `server/actions/<Action><Entity>.action.ts`. Keep a route handler only for callers outside the app, such as webhooks.
4. **Names.** Feature folders kebab-case. Entities, actions, and classes PascalCase. Action names include their noun: `archiveUser`, `findActiveUsers`.
5. **Do not widen the standard five.** List returns all, Show returns one by id, Create takes the create schema, Update takes id and the update schema, Delete takes id. Anything else is a bespoke action.
6. **Finish what the tool leaves open.** Fill the `TODO` in each repository. Add the printed line to `<feature>.routes.ts` on Node or register the printed classes in `<feature>.module.ts` on Nest. Add fields to the Zod schemas.
7. **Zod is part of the stack.** The generated schemas import `zod`. When `package.json` lacks it, add it in the same change; never replace the generated schemas with hand-written parsers or type guards. Parse every request body and API response with a schema, and derive the feature's types with `z.infer` instead of keeping a parallel interface in `types/`.
8. **Shared plumbing lives outside features.** The API base URL, the fetch helper, the response envelope and its error type are the same for every feature. Keep them once in `src/lib/` (or the project's equivalent), created with the first feature that needs them, and have each hook call the endpoint through them. A feature folder holds only that feature's code, and nothing in it is named after the feature when it isn't specific to it.

## Layout by stack

- Next.js: `app/<feature>` or `src/app/<feature>`; route handlers under `app/api/<feature>`. The tool detects `next-fullstack` only when `app/api` (or `src/app/api`) exists; a full-stack app without one passes `--stack next-fullstack`.
- React (including Vite) and Node: `src/features/<feature>` or `features/<feature>`. Nest a feature under another with `--root`, as the starter's auth screens do: `npx domain-driver --root src/features/auth make:feature two-factor-setup`.
- Nest: `src/features/<feature>` when `src/features` exists, otherwise `src/<feature>`, with a `<feature>.module.ts`. A project that groups flows into areas, as nestjs-starter does, scaffolds each with `--root src/<area>` so it lands in the area and registers in `src/<area>/<area>.module.ts`.
- TanStack Start: `src/routes/<feature>` or `routes/<feature>`; every layer folder is prefixed with `-` so the router ignores it, and the entry file is `index.tsx`, not `page.tsx`.
