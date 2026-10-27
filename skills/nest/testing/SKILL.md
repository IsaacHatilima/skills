---
name: testing
description: Use when writing unit or e2e tests for NestJS code: building a TestingModule, overriding providers, guards, or pipes, resolving request-scoped providers, running supertest against the app, isolating the e2e database, or faking HTTP clients and third-party SDKs.
---

# Testing

Applies to: `src/**/*.spec.ts`, `test/**`, `jest.config.*`, `vitest.config.*`.

Use the project's runner. `@nestjs/testing` works with Jest and Vitest; examples use `jest.fn()` (`vi.fn()` under Vitest).

## Rules

- Unit tests build the provider through `Test.createTestingModule({ providers: [Target, { provide: Dep, useValue: fake }] })` and `module.get(Target)`, so tokens and `@Inject` wiring are exercised. Do not hand-construct with `new Service(fake as any)`.
- Test the business operation (`actions`) against a faked repository provider. Fake the same token production injects: the repository class, `getRepositoryToken(Entity)` for TypeORM, or the Prisma service class.
- A fake keeps the real contract: same return shapes, `null` where the real one returns `null`, the same thrown error types. A lenient fake hides bugs that only appear against the real implementation.
- `.useMocker((token) => ...)` auto-fakes dependencies a test does not care about.
- Request-scoped and transient providers cannot be fetched with `module.get()`; it throws. Use `await module.resolve(Provider)`.
- Unit-test a guard, pipe, or filter only for its own branching. Cover how it is wired (order, `@Public()`, global registration) through e2e.
- e2e tests start from `Test.createTestingModule({ imports: [AppModule] })`, replace external dependencies with `.overrideProvider(TOKEN).useValue(fake)` (also `overrideGuard`, `overridePipe`, `overrideInterceptor`, `overrideFilter`), then `createNestApplication()`, `await app.init()`, and `await app.close()` in `afterAll`.
- Setup done only in `main.ts` (`useGlobalPipes`, `useGlobalFilters`, `setGlobalPrefix`, `enableVersioning`) does not exist in a test app, so e2e would accept input production rejects. Put it in `AppModule` providers (`APP_PIPE`, `APP_FILTER`) or in one `configureApp(app)` function called by both `main.ts` and tests. Do not re-declare a different `ValidationPipe` per suite.
- Drive the app with supertest on `app.getHttpServer()` and assert status and body for: validation 400 including an unknown field, 401 without a token, 403 for the wrong role, the mapped domain error code, and absence of secret fields (`password`, `passwordHash`) in responses (`security`, `api`).
- Use a dedicated test database, such as a container or a separate schema, never a shared or development database. Apply the real migrations so they are tested (`data`), then truncate tables or roll back a per-test transaction. Do not rely on `synchronize`.
- Fake at a boundary you own. Wrap third-party SDKs and HTTP calls in your own provider behind a token (`architecture`) and override it. Never call real payment, mail, queue, or network services in tests; override a queue with `getQueueToken('name')`.
- `HttpService` from `@nestjs/axios` returns Observables. Fake with `of({ data, status: 200, statusText: 'OK', headers: {}, config: {} })` and `throwError(() => error)`. Cover timeout, 429, and 5xx paths, not only success.
- Use fake timers for expiry and scheduling logic, and restore real timers after each test.

## Example

```ts
let app: INestApplication;

beforeAll(async () => {
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
    .overrideProvider(PAYMENT_GATEWAY)
    .useValue({ charge: jest.fn().mockResolvedValue({ id: 'ch_test' }) })
    .compile();

  app = moduleRef.createNestApplication();
  configureApp(app); // the same function main.ts calls
  await app.init();
});

afterAll(() => app.close());

it('rejects unknown fields', () =>
  request(app.getHttpServer())
    .post('/users')
    .send({ email: 'a@example.com', isAdmin: true })
    .expect(400));
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
