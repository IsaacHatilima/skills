---
name: api
description: Use when adding NestJS exception filters or domain errors, handling fire-and-forget promises or event and scheduled-job failures, writing interceptors, binding params and query values with built-in pipes, or versioning an HTTP API.
---

# API

Applies to: `src/**/*.filter.ts`, `src/**/*.interceptor.ts`, `src/**/*.pipe.ts`, `src/**/*.controller.ts`, `src/main.ts`.

Body and query validation is in `security`; the business operation behind a route is in `actions`.

## Rules

- Services throw; controllers do not catch errors to build responses, and handlers do not return `{ error }` objects or use `@Res()` for failures.
- An HTTP-only service may throw `HttpException` subclasses (`NotFoundException`, `ConflictException`). If the same operation also runs from queues, events, RPC, or WebSocket handlers, throw domain error classes with a stable `code` and map them to HTTP in an exception filter (`@Catch(DomainError)`).
- Register filters that need dependencies with an `APP_FILTER` provider. `app.useGlobalFilters(new X())` runs outside the module context and cannot inject.
- Have one catch-all `@Catch()` filter. Log the full error and stack server-side; respond with a generic message for non-`HttpException` errors, never stacks, SQL, or ORM messages. Reply through `HttpAdapterHost.httpAdapter.reply()` so the filter works with Express and Fastify.
- A `@Catch()` filter matches every exception, and Nest tries later-registered filters first (route, then controller, then global). Register the catch-all before specific global filters or it shadows them; assert one specific error code in an e2e test.
- Nest awaits and handles errors from handler promises. It does not handle promises you detach. A fire-and-forget call needs `.catch()` with logging, or becomes a queue job (`operations`). Do not add a `process.on('unhandledRejection')` that only logs and continues.
- Event, scheduled, and queue code has no caller to report to: catch, log with context, then retry or dead-letter. Never swallow silently.
- Prefer built-in pipes: `ParseIntPipe`, `ParseUUIDPipe`, `ParseEnumPipe`, `ParseBoolPipe`, `ParseDatePipe`, `ParseArrayPipe`, `DefaultValuePipe`. Put `DefaultValuePipe` before the parse pipe. A comma-separated list is `new ParseArrayPipe({ items: String, separator: ',' })`; do not write a custom pipe that shadows the built-in name.
- Past two or three query values, use a query DTO class (`security`) instead of stacked `@Query('x', pipe)` parameters.
- Use interceptors for cross-cutting behavior around the handler: timing and request logging, a response envelope, `timeout()` mapped to `RequestTimeoutException`, caching. Register with `APP_INTERCEPTOR` when they need DI, or `@UseInterceptors()` for one controller or route.
- Interceptors do not apply to responses sent through `@Res()`. Do not map errors in an interceptor; that is the job of filters.
- If the project has a standard response envelope, apply it in one interceptor rather than wrapping in every handler.
- Version with the built-in feature: `app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' })`, then `@Controller({ path: 'users', version: '1' })`, `@Version('2')` on a route, or `VERSION_NEUTRAL`. Header, media type, and custom strategies are options of the same call. No hand-made `v1/` controller prefixes.
- Do not read a version header inside services to branch behavior. Keep one operation (`actions`) and map to per-version response classes in the controllers.
- Version only breaking contract changes. Signal retirement of an old version with `Deprecation` (RFC 9745) and `Sunset` (RFC 8594) headers from an interceptor on that controller.

## Example

```ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  constructor(private readonly adapterHost: HttpAdapterHost) {}

  catch(exception: unknown, host: ArgumentsHost): void {
    const isHttp = exception instanceof HttpException;
    const status = isHttp ? exception.getStatus() : HttpStatus.INTERNAL_SERVER_ERROR;
    const body = isHttp
      ? exception.getResponse()
      : { statusCode: status, message: 'Internal server error' };

    if (!isHttp) {
      this.logger.error(exception instanceof Error ? exception.stack : String(exception));
    }
    this.adapterHost.httpAdapter.reply(host.switchToHttp().getResponse(), body, status);
  }
}

// AppModule providers: { provide: APP_FILTER, useClass: AllExceptionsFilter }
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
