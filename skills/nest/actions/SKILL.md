---
name: actions
description: Use when creating, refactoring, or reviewing a NestJS service or provider that performs a business operation, or deciding its typed DTO inputs and actor context.
---

# Nest actions

The common contract applies first, then Nest conventions.

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

## Nest conventions

Use the project's service/provider as the business-operation implementation. Preserve existing method names such as `handle` or `execute`, provider registration, and dependency injection. A separate Action wrapper is unnecessary when the service already owns that operation.

### Typed operation inputs

- The controller or transport handler performs runtime validation with the project's existing pipe/schema setup and passes a concrete DTO to the service.
- A DTO may be the project's class, interface, or named schema-output type. Its fields have concrete types. Runtime validation is still required at the network boundary.
- Pass an additional typed domain/auth-context object when the operation needs one, for example `handle(actor: AuthenticatedUser, input: ArchiveCommentDto): Promise<Comment>`. Resolve the actor through trusted authentication context.
- Primitive/collection arguments remain rare, explicitly typed exceptions. Use concrete item types such as `ItemDto[]`, not `any[]`, an untyped request object, or a loosely shaped payload.

### Scope and transactions

Follow the project's operation-per-class or service-module convention. Keep the requested operation focused, and extract implementation steps into private helpers rather than unrelated new public methods.

Preserve an existing transaction decorator/context on the public operation when extracting helpers. Do not introduce a transaction package just to match an example. The controller's validation and the service's types do not replace server authorization.

### Example

Assume the project already defines a `User` model, an `UpdateUserDto` with a typed `name` field, and a registered `UserRepository` provider. The controller validates the DTO and authorizes the model before calling this service.

```ts
import { Injectable } from '@nestjs/common';
import type { User } from './user.model';
import type { UpdateUserDto } from './update-user.dto';
import { UserRepository } from './user.repository';

@Injectable()
export class UpdateUserService {
  constructor(private readonly users: UserRepository) {}

  async handle(user: User, input: UpdateUserDto): Promise<User> {
    return this.users.update(user, input);
  }
}
```

The service receives concrete business data, not a request object or loose payload. Keep any additional operation-level policy checks and transaction boundary required by the project.

Reference: [Nest providers and services](https://docs.nestjs.com/providers).
