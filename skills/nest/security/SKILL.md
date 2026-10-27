---
name: security
description: Use when adding or reviewing NestJS request validation, DTOs, authentication or authorization guards, JWT or refresh-token handling, rate limiting, or any response that returns entities or database rows to clients.
---

# Security

Applies to: `src/main.ts`, `src/app.module.ts`, `src/**/*.dto.ts`, `src/**/*.guard.ts`, `src/auth/**`, `src/**/*.controller.ts`.

Controller validation and types do not replace authorization inside the operation (`actions`). Secrets come from validated config (`operations`).

## Rules

- Register one global `ValidationPipe` with `whitelist: true`, `forbidNonWhitelisted: true`, and `transform: true`. Provide it through `APP_PIPE` (not only `app.useGlobalPipes` in `main.ts`) so e2e apps built from `AppModule` validate identically (`testing`).
- `whitelist` strips any property without a validator decorator. Give every DTO field at least one decorator (`@IsOptional()` or `@Allow()` when no other check applies), and use `@ValidateNested()` with `@Type(() => Child)` for nested objects.
- A DTO checked by `ValidationPipe` must be a class; interfaces vanish at runtime and are never validated. If the project validates with schemas (zod, valibot), use its pipe instead (`StandardSchemaValidationPipe` in v12).
- Query and path values arrive as strings. Use `@Type(() => Number)` with `@IsInt()`, or the parse pipes in `api`. Do not enable `transformOptions.enableImplicitConversion`: it coerces booleans with `Boolean(value)`, so `"false"` becomes `true`.
- Never accept `@Body() body: any` or `@Query() query: any`.
- Authenticate and authorize with guards, not `if (!req.user)` in handlers. Register authentication as a global `APP_GUARD` (default deny) with a `@Public()` opt-out, then a roles or permissions guard. `APP_GUARD` providers run in registration order, after middleware and before interceptors and pipes.
- Read guard metadata with `Reflector.getAllAndOverride` over `[context.getHandler(), context.getClass()]`. Prefer `Reflector.createDecorator<T>()` over string-keyed `SetMetadata`.
- A roles guard also runs on `@Public()` routes, where `request.user` is undefined. Return early when no role is required and deny, never throw a `TypeError`, when the user is missing.
- A role guard does not stop tenant A reading tenant B's record. Check ownership where the entity is loaded, inside the operation.
- Health and metrics endpoints need `@Public()` and `@SkipThrottle()`.
- JWT: the secret comes from config (`getOrThrow`), never a literal. Use short-lived access tokens, set and verify `issuer` and `audience`, and keep the payload to `sub` and minimal claims, never password hashes or PII. The signature prevents tampering; the risk is staleness, so claims such as roles are old until expiry. Load the user in the strategy's `validate()` when role changes or deactivation must apply immediately, and reject tokens issued before `passwordChangedAt`.
- Refresh tokens are random opaque values (`randomBytes(32)`), stored hashed (SHA-256 suffices for 256-bit random tokens), rotated on use, and revoked on logout and password change.
- Rate limit with `@nestjs/throttler` as a global `APP_GUARD`. `ttl` is in milliseconds. Tighten login, password reset, OTP, and payment routes with `@Throttle({ default: { limit: 5, ttl: 60_000 } })`; the key must name a configured throttler.
- Throttler `limit` and `ttl` accept functions of `ExecutionContext`; customize the key by overriding `getTracker()`. Multiple instances need shared (Redis) storage, and behind a proxy set `trust proxy` or every client shares one IP.
- Never return entities or ORM rows from a controller. Use a response class with an allowlist: class-level `@Exclude()` with `@Expose()` on each exposed field, plus `@SerializeOptions({ type: UserResponse })`, and `ClassSerializerInterceptor` as a global `APP_INTERCEPTOR`.
- `@Exclude()` on an entity is a denylist, so a new sensitive column leaks by default. It also does nothing for plain objects (Prisma results, raw queries), which have no class metadata; `type` converts them into the response class first.
- `@Res()` switches the route to library mode and bypasses interceptors, including serialization. Return values instead.
- Add `helmet`. JSON APIs rarely need output escaping; where user HTML is stored or served, sanitize with an allowlist library (`sanitize-html`) and never interpolate user input into HTML responses.

## Example

```ts
@Module({
  providers: [
    { provide: APP_PIPE, useValue: new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }) },
    { provide: APP_GUARD, useClass: ThrottlerGuard }, // cheap rejection before auth work
    { provide: APP_GUARD, useClass: JwtAuthGuard },   // default deny, honors @Public()
    { provide: APP_GUARD, useClass: RolesGuard },
    { provide: APP_INTERCEPTOR, useClass: ClassSerializerInterceptor },
  ],
})
export class AppModule {}

@Exclude()
export class UserResponse {
  @Expose() id: string;
  @Expose() email: string;
}

@Get(':id')
@SerializeOptions({ type: UserResponse })
findOne(@Param('id', ParseUUIDPipe) id: string): Promise<User> {
  return this.users.findById(id);
}
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
