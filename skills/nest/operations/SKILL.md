---
name: operations
description: Use when setting up NestJS environment configuration and startup validation, logging, lifecycle hooks and graceful shutdown, health and readiness endpoints, BullMQ background jobs, or microservice message and event handlers.
---

# Operations

Applies to: `src/main.ts`, `src/config/**`, `src/health/**`, `src/**/*.processor.ts`, `.env*`.

## Rules

- Load config with `ConfigModule.forRoot({ isGlobal: true, validate })` (a `validate` function using class-validator or zod, or `validationSchema` with Joi or a Standard Schema in v12). The app must refuse to boot on a missing or invalid required variable, and the validator converts types (`PORT` to a number).
- Application code never reads `process.env`. Use namespaced `registerAs('database', ...)` config injected as `@Inject(databaseConfig.KEY) cfg: ConfigType<typeof databaseConfig>`, or `ConfigService.getOrThrow()`. No `|| 'default'` fallbacks for secrets or required hosts.
- Module-level code and other modules' static `forRoot({ host: process.env.X })` arguments can run before `.env` is loaded. Configure them with `forRootAsync({ inject: [ConfigService], useFactory })`.
- Log through Nest `Logger` with a class context (`new Logger(Service.name)`), never `console.log`. Production logs are JSON: `new ConsoleLogger({ json: true })` (Nest 11+) passed as `logger` to `NestFactory.create`, or `nestjs-pino` (`bufferLogs: true`, then `app.useLogger(app.get(Logger))`) with `redact` for `req.headers.authorization`, cookies, and password fields. Do not hand-write a JSON logger.
- Never log credentials, tokens, request bodies, or PII (emails included); log ids. Carry the request id with AsyncLocalStorage (`nestjs-cls`), not a request-scoped logger (`architecture`).
- A lifecycle hook delays startup only if it returns its promise: `async onModuleInit() { await this.pool.connect(); }`. `onModuleInit() { this.connect(); }` lets the app start before the connection exists. Keep constructors synchronous. Use `onApplicationBootstrap` when you need other modules ready. Do not rely on hook order between unrelated providers; it changes across Nest majors.
- Call `app.enableShutdownHooks()` in `main.ts` (off by default). On a signal or `app.close()` the order is `onModuleDestroy`, `beforeApplicationShutdown`, HTTP server close (in-flight requests drain), `onApplicationShutdown`. Close pools, Redis clients, and sockets in these hooks.
- Do not add your own `process.on('SIGTERM')` with `server.close()` and `process.exit()`; it bypasses Nest's hooks. `server.setTimeout` is a socket timeout, not a shutdown timeout.
- Start failing readiness in `onModuleDestroy` or `beforeApplicationShutdown`. `onApplicationShutdown` runs after the server has closed, too late for the orchestrator to reroute traffic. Hooks do not run for request-scoped providers.
- Health uses `@nestjs/terminus` (`TerminusModule`, `@HealthCheck()`, `HealthCheckService.check([...])`). Liveness checks the process only; a dependency outage must not restart the pod. Readiness checks critical dependencies with timeouts and fails during shutdown. Redis is not HTTP, so do not `http.pingCheck` it.
- Custom indicators use `HealthIndicatorService`: `const s = this.indicators.check('redis'); ... return s.up()` or `s.down()` (v12 adds `.attempt(fn).withTimeout(ms)`). Extending `HealthIndicator` and throwing `HealthCheckError` is deprecated in v11 and removed in v12. Mark health routes `@Public()` and `@SkipThrottle()` (`security`).
- Queues use `@nestjs/bullmq`. Register `BullModule.forRoot({ connection, defaultJobOptions: { attempts, backoff, removeOnComplete, removeOnFail } })` with connection settings from config, and `registerQueue({ name })`. Producers inject `@InjectQueue('name') Queue`.
- A consumer is a class with `@Processor('name')` extending `WorkerHost` and implementing `process(job)`, switching on `job.name`. Listen with `@OnWorkerEvent('failed')`. `@Process`, `@OnQueueActive`, and `@OnQueueFailed` belong to `@nestjs/bull` and do not exist in `@nestjs/bullmq`.
- Move slow or fallible work (reports, email, file processing, webhooks) out of request handlers into jobs and return the job id. Keep payloads to ids, not entities.
- Jobs retry, so processors must be idempotent. Let errors throw so the retry happens; do not catch and ignore them. Recurring jobs use `queue.upsertJobScheduler(id, { pattern }, template)`, not `setInterval` or the old `repeat` option.
- Microservices: `@MessagePattern` is request-response and its return value is the reply; `@EventPattern` is fire-and-forget, its return value is ignored, and its failures never reach the sender, so handle them locally (log, retry, dead-letter). Throw `RpcException` from message handlers.
- `client.send()` is a cold Observable that sends nothing until subscribed: `await firstValueFrom(client.send(...))` (`toPromise()` is deprecated). `client.emit()` is hot.

## Example

```ts
@Processor('reports')
export class ReportsProcessor extends WorkerHost {
  private readonly logger = new Logger(ReportsProcessor.name);

  constructor(private readonly generateReport: GenerateReportService) {
    super();
  }

  async process(job: Job<GenerateReportDto>): Promise<void> {
    if (job.name !== 'generate') {
      throw new Error(`Unknown job ${job.name}`);
    }
    await this.generateReport.handle(job.data);
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error): void {
    this.logger.error(`Job ${job.id} failed: ${error.message}`, error.stack);
  }
}

// main.ts
const app = await NestFactory.create(AppModule, { logger: new ConsoleLogger({ json: true }) });
app.enableShutdownHooks();
await app.listen(app.get(ConfigService).getOrThrow<number>('PORT'));
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
