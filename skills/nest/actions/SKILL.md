---
name: actions
description: Use when creating, refactoring, or reviewing a NestJS action or service that performs one business operation, or deciding its typed input, actor, transaction, side effects, or return value.
---

# Actions

Applies to: `src/**/services/*.service.ts`, or `src/**/*.action.ts` in a project that uses that name. Project guidance and existing conventions win over these defaults.

An action is one business operation in its own class. domain-driver generates it as `services/CreateProject.service.ts` with `CreateProjectService.handle()`. A project that names them `CreateProjectAction` follows the same rules.

## Class shape

- An `@Injectable()` class with one public `async handle()`, named verb, noun, then class type: `ArchiveProjectService`.
- A new operation is a new class (`npx domain-driver make:action projects/Project archiveProject`), never a new method on another action or a branch inside List or Show.
- Inject repositories, other actions, and queues through the constructor. Keep per-call state in local variables.

## Inputs

- Request data arrives as the schema's inferred type, such as `CreateProject`, already validated and normalized (see `dtos`). Never accept a request object, `any`, or a loose record.
- Pass the actor explicitly, as in `handle(actor: AuthPrincipal, data: CreateProject)`. Route ids arrive as typed parameters.
- Owner, tenant, and team ids come from the actor or a loaded parent, never from input. Every read is scoped to records the actor may see (see `security`).

## Persistence and transactions

- Repositories run the queries and own transactions (see `database`); the action makes the decisions. An action never touches the database client, a schema table, or a transaction.
- An action calls one flow repository for its write. When the write spans several statements, such as a project and its owner membership, that repository commits them together in one method. The action may also read through shared repositories directly; don't add forwarding methods to hide them.
- Hash passwords and call external services before calling the repository that writes.
- Jobs, events, and mail that depend on the write start after that call returns, once the write has committed (see `jobs`). When losing them is unacceptable, the repository writes an outbox row in the same transaction instead.

## Results and failures

- Return what the caller needs, typed: usually the output type the repository mapped (see `dtos`). Deletes return `void`, and checks return `boolean`. Never return a database row.
- Broken business rules throw the project's coded error, such as `notFound('Project')` when a scoped lookup returns `null`. The exception filter renders it (see `api-responses`).

## Example

```ts
@Injectable()
export class CreateProjectService {
  constructor(
    private readonly createProject: CreateProjectRepository,
    @InjectQueue('projects') private readonly queue: Queue,
  ) {}

  async handle(actor: AuthPrincipal, data: CreateProject): Promise<Project> {
    const project = await this.createProject.handle({ name: data.name, ownerId: actor.userId });

    await this.queue.add('index', { projectId: project.id }, { jobId: `index-${project.id}` });

    return project;
  }
}
```

`CreateProjectRepository.handle()` inserts the project and its owner membership in one transaction and returns the mapped `Project`. The job is queued only after that commit.

## Verify

Unit tests fake the repositories and the queue, and cover each branch and error. E2e tests prove the writes commit and roll back together (see `tests`).
