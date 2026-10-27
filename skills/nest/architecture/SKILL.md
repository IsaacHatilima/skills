---
name: architecture
description: Use when creating or restructuring NestJS modules, sharing providers across modules, debugging "Nest can't resolve dependencies" or circular import errors, choosing a provider scope, injecting an interface, or decoupling features with events.
---

# Architecture

Applies to: `src/**/*.module.ts`, `src/app.module.ts`, `src/**/*.service.ts`, `src/**/*.repository.ts`.

Business operations, typed inputs, and transaction ownership are defined in `actions`. This skill covers how modules and providers are wired.

## Rules

- Organize by feature: `src/<feature>/` holds the module, controller, services, repository, DTOs, and entities. No top-level `controllers/` or `services/` folders. `AppModule` imports feature modules and root infrastructure modules only.
- A provider is listed in exactly one module's `providers`. Other modules import that module, which must `exports` the provider. The same class in two `providers` arrays creates two instances with separate state.
- Export only what other modules consume. Use `@Global()` just for config, logging, and database connection modules; global providers hide dependencies and complicate module tests.
- Keep services focused on one business operation or capability, per `actions`. A controller delegates to one operation; it does not orchestrate several services.
- Use constructor injection with `private readonly`. Property injection is only for a subclass that would otherwise forward parameters through `super()`. Mark optional dependencies with `@Optional()` on the constructor parameter.
- Interfaces and type aliases do not exist at runtime. Inject one through a `Symbol` token with `@Inject(TOKEN)`, or use an abstract class as both type and token. Export the token from the providing module. Never pick the implementation from `process.env.NODE_ENV` in a module; tests use `overrideProvider` (`testing`).
- Providers are singletons by default, so they must not keep per-request state in fields. Concurrent requests overwrite it.
- `Scope.REQUEST` bubbles up: every provider, controller, guard, or interceptor that injects a request-scoped provider, directly or transitively, becomes request-scoped and is rebuilt per request. Its own dependencies stay singletons. Avoid request scope; pass the actor or data as a parameter (`actions`), or use AsyncLocalStorage (`nestjs-cls`) for request ids and audit context.
- Lifecycle hooks do not run for request-scoped providers. `Scope.TRANSIENT` gives each consumer its own instance and does not bubble.
- `ModuleRef.get()` hides dependencies. Use it only to look up a handler at runtime (strategy by type, `resolve()` for scoped providers); declare everything else in the constructor.
- Circular imports have two forms. Module A importing B while B imports A: extract the shared part into a third module, or replace one direction with an event. File-level cycles through barrel `index.ts` files make a decorator argument `undefined` ("undefined at index [0]"): import from the defining file. `forwardRef(() => Module)` in both `imports` and `@Inject(forwardRef(() => Service))` is a last resort that hides the design problem.
- Use `@nestjs/event-emitter` (`EventEmitterModule.forRoot()` once) so side effects such as email, analytics, and audit do not make the triggering module import them. An event is a class with `readonly` fields and a constant name, handled with `@OnEvent`.
- Emit events only after the transaction commits (`data`). `emit()` does not await async listeners; `emitAsync()` does.
- `@OnEvent` handler errors are logged and swallowed by default (`suppressErrors: true`), so the emitter never sees them. A step whose failure must fail the request is a direct service call; one that needs retries is a queue job (`operations`).

## Workflow

For "Nest can't resolve dependencies of X (?, ...)":

1. The unresolved parameter position is the `?`. Confirm that provider is in a `providers` array of X's module, or exported by a module X's module imports.
2. For interface or string tokens, confirm `@Inject(TOKEN)` matches the `provide` value.
3. If the message says `undefined`, look for a circular file import before reaching for `forwardRef`.

## Example

```ts
export const PAYMENT_GATEWAY = Symbol('PAYMENT_GATEWAY');

export interface PaymentGateway {
  charge(amountMinor: number, currency: string): Promise<PaymentResult>;
}

@Module({
  providers: [{ provide: PAYMENT_GATEWAY, useClass: StripePaymentGateway }],
  exports: [PAYMENT_GATEWAY],
})
export class PaymentsModule {}

@Injectable()
export class CheckoutService {
  constructor(@Inject(PAYMENT_GATEWAY) private readonly payments: PaymentGateway) {}
}
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
