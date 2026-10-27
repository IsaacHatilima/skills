---
name: actions
description: Use when creating, refactoring, or reviewing a Next.js Server Action, route handler, or the server-only operation behind it.
---

# Next actions

The common contract applies first, then Next conventions.

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

## Next conventions

A framework Server Action or route handler is a callable request boundary. The business operation is the project's server-only service or typed function; it follows the same common contract as an Action class without requiring a particular class name or dependency-injection pattern.

### Typed operation inputs

- Validate FormData or other untrusted arguments at the boundary and map the validated result to a named DTO before invoking the operation.
- Use a concrete callable contract such as `updateUser(input: UpdateUserDto): Promise<User>`. The DTO may be a class, interface, named type, or the named output type of the project's existing schema.
- Obtain caller identity from trusted server context. Resolve any domain model on the server before passing it into the operation; transport data is not a model merely because it was cast to that type.
- Primitive/collection inputs remain rare exceptions with concrete declared types and item/shape information. Do not use `any` or unchecked casts to bypass the contract.

### Server boundary

Keep server-only operation/data dependencies outside the client module graph. Apply required access checks at the callable boundary or its trusted server policy path; a page/layout check alone does not establish authorization for a Server Action.

Preserve the project's operation naming, data-access, transaction, and revalidation conventions. Reuse an existing service/function instead of creating an Action-to-Service wrapper to imitate another stack.

### Example

Assume existing `User` and repository types, a `requireUser()` helper returning the authenticated `User`, and an `updateUserSchema` that validates the allowed `name` field. Use the project's actual auth, validator, and persistence modules.

The internal operation stays in a server-only module:

```ts
// update-user.server.ts
import 'server-only';
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

The Server Action authenticates the caller, validates transport input, and passes a typed DTO to that operation:

```ts
// actions.ts
'use server';

import { requireUser } from '@/lib/auth';
import { updateUserSchema } from './update-user.schema';
import { updateUser, type UpdateUserDto } from './update-user.server';

export async function updateProfile(formData: FormData) {
  const user = await requireUser();
  const input: UpdateUserDto = updateUserSchema.parse({
    name: formData.get('name'),
  });
  const updated = await updateUser(user, input);

  return { id: updated.id, name: updated.name };
}
```

The target model comes from trusted auth context, and the response projects public fields instead of serializing the entire model. Preserve any additional policy checks and revalidation the project requires.

Reference: [Next server boundaries and data security](https://nextjs.org/docs/app/guides/data-security).
