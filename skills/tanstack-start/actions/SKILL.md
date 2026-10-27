---
name: actions
description: Use when creating, refactoring, or reviewing a TanStack Start server function, server route, or the server-only operation behind it.
---

# TanStack Start actions

The common contract applies first, then TanStack Start conventions.

## Common operation contract

An action means one business operation here. An application service or server-only function fulfilling that role follows the same contract. Preserve project naming and invocation style rather than adding an Action-to-Service wrapper solely to translate names. This describes the operation role, not every utility called Service.

- Every operation parameter **MUST have an explicit, concrete type in its callable contract**. Prefer named DTO/data objects or concrete domain models. DTO fields must also have meaningful types.
- Primitive and array/collection inputs are rare exceptions for a genuinely narrow contract. They still need declared types, including collection item types or shapes. Explain non-obvious exceptions in the plan or review.
- Untyped parameters, broad catch-all types, unstructured payload bags, and call-site casts do not satisfy the contract. Use the language's type declarations or the project's checked JSDoc for JavaScript.
- The request boundary validates input, applies required access rules, and maps it into typed operation data or resolves server-side models. Pass business data rather than the HTTP request object. Types alone do not validate data or establish permission.

Follow documented project layers. The request adapter delegates; the operation owns business decisions and uses the project's existing data-access approach. Keep operations focused and separately named. Keep List, Show, Create, Update, and Delete on their existing contracts instead of hiding a bespoke operation inside them.

## Keep methods small

Use the project's complexity tool and threshold. Otherwise the default maximum is 5: start at 1, then add 1 per conditional branch, loop, case/match arm, catch, boolean conjunction/disjunction, and ternary. Count constructs rather than comments, strings, or type syntax. Else/default, null coalescing, and optional access add nothing.

Above the threshold, extract named steps into private methods or unexported functions. Preserve public signatures, return types, error handling, and transaction ownership. Helpers share the owning operation's transaction context. Do not split a method at or below the threshold merely to add indirection.

## Review

Check the common contract and the stack conventions below together: operation scope, typed signature, DTO/model inputs, justified primitive/collection exceptions, stack-specific declarations, access rules, and persistence. Report the affected operation and smallest correction without extending the change to unrelated files.

## TanStack Start conventions

The server-function handler or server route is the callable request adapter. Its server-only service or typed operation function owns the business operation. Preserve that project convention rather than introducing an injectable Service class merely to match another stack's terminology.

### Typed operation inputs

- Use the project's existing server-function validator to validate network input. Map its validated data to the named DTO expected by the internal operation.
- A callable contract such as `updateUser(input: UpdateUserDto): Promise<User>` accepts concrete typed data. A named schema-output type may be the DTO; no extra class or validation library is required.
- Supply caller/domain context from trusted server code. A typed DTO does not establish authentication, authorization, or record ownership.
- Primitive/collection arguments are rare, explicitly typed exceptions. Collections declare their item type or shape. Do not replace validated types with `any` or a cast of untrusted data.

### Server boundary

Apply the required access checks in the handler or its applied server middleware. A protected client route is not proof that the independently callable server function is protected.

Keep server-only dependencies in the project's established server modules. Preserve its data-access, transaction context, query-update, and operation-naming conventions. Extract named private/unexported helpers while retaining the public typed contract.

### Example

Assume existing `User` and repository types, a `requireUser()` helper returning the authenticated `User`, and an `updateUserSchema` validating the allowed `name` field. Use the project's existing auth, validator, and data layer.

The internal operation receives a model and a named DTO:

```ts
// update-user.server.ts
import type { User } from './user.model';
import { users } from './user.repository';

export interface UpdateUserDto {
  readonly name: string;
}

export async function updateUser(
  user: User,
  input: UpdateUserDto,
): Promise<User> {
  return users.update(user, input);
}
```

The callable server function validates input and loads its server-only dependencies inside the handler:

```ts
// update-user.functions.ts
import { createServerFn } from '@tanstack/react-start';
import { updateUserSchema } from './update-user.schema';
import type { UpdateUserDto } from './update-user.server';

export const updateProfile = createServerFn({ method: 'POST' })
  .validator(updateUserSchema)
  .handler(async ({ data }) => {
    const { requireUser } = await import('@/lib/auth.server');
    const { updateUser } = await import('./update-user.server');
    const user = await requireUser();
    const input: UpdateUserDto = data;
    const updated = await updateUser(user, input);

    return { id: updated.id, name: updated.name };
  });
```

This uses `.validator(...)` as shown in the linked guide; match the validator API to the project's installed Start version. Only validated DTO data enters the business operation, and the model comes from trusted server context. Preserve any additional project policy and query-update requirements.

Reference: [TanStack Start server functions](https://tanstack.com/start/latest/docs/framework/react/guide/server-functions).
