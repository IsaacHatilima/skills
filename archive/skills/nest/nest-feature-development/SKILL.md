---
name: nest-feature-development
description: Plan, implement, or review NestJS controllers, providers, validation, authorization, and persistence in a touched server package.
---

# Build and review Nest features

Read the package's Nest version, module layout, validation stack, authentication guards, and persistence adapter. Use its existing action conventions; importing Nest does not authorize replacing them.

Nest services/providers can implement the same business-operation role as Laravel Actions. Preserve that naming rather than adding a duplicate Action layer. Public operation methods take concrete DTOs and, where appropriate, typed domain/auth-context objects. Apply the shared `action-architecture` input contract; raw request objects and `any` do not satisfy it. Controller validation maps input to that contract before calling the service.

- Keep controllers thin and inject services/providers through the existing module boundary. Check that added controllers and providers are registered and exports/imports match the consumers; do not assume every generator registers them.

- Validate body, query, and route input with the project's actual pipe/schema setup, including runtime coercion and permitted fields. Do not replace a Zod-based project with class-validator, or assume TypeScript types validate requests.

- Follow the guard or service policy from the actual controller method to the changed record. A global authentication guard does not itself establish record ownership or tenant access.

- Keep persistence operations in the project's data layer. Preserve the installed adapter's transaction context across helper calls.

Where the project already uses `@Transactional()` on an action's public `handle`, leave that decorator on the public method when extracting private helpers. Do not introduce that decorator or a transaction package in a project that does not have it.

For example, inside an existing action whose DTO/auth types, imports, record lookup, and repository are already defined, the transaction stays on the operation:

```ts
@Transactional()
async handle(actor: AuthenticatedUser, input: ArchiveCommentDto): Promise<Comment> {
  const comment = await this.findComment(input.commentId);
  this.assertCanArchive(actor.id, comment);
  return this.repository.handle(input.commentId);
}

private assertCanArchive(userId: string, comment: CommentRow): void {
  if (userId !== comment.authorId && userId !== comment.postOwnerId) {
    throw new ForbiddenException();
  }
}
```

Here `actor` comes from trusted server authentication context, and `ArchiveCommentDto` declares a typed `commentId` field. Use the project's actual DTO and auth types; the names are illustrative. The permission helper remains inside the caller's transaction context; its presence does not replace the route's authentication.

Test the changed action through the project's test harness, including invalid input and allowed/refused callers. Check actual response serialization. A Nest service can also render templates; decide whether UI review applies from the changed response, rather than the framework label.

Use the docs for the installed version. References: [Nest providers/services](https://docs.nestjs.com/providers), [Nest validation](https://docs.nestjs.com/techniques/validation) and [Nest authorization source](https://github.com/nestjs/docs.nestjs.com/blob/master/content/security/authorization.md).

