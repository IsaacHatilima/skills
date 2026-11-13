---
name: database
description: "Use when writing NestJS persistence code: the Drizzle module and schema, repository queries, fixing N+1 queries or over-fetching, transactions, translating database errors, or paginating a list. Drizzle by default; a project already on Prisma keeps it."
---

# Database

Applies to: `src/database/**`, `drizzle.config.ts`, `src/**/repositories/*.repository.ts`. Project guidance and existing conventions win over these defaults.

Use Drizzle with node-postgres. A project already on Prisma keeps Prisma: never switch ORMs inside a feature, and see **Prisma projects** at the end.

## Setup

- Install `drizzle-orm` and `pg`, with `drizzle-kit` and `@types/pg` as dev dependencies.
- A `@Global()` `DatabaseModule` provides a `pg` `Pool` built from validated config under a `PG_POOL` token, and `drizzle(pool, { schema })` under a `DRIZZLE` token. It ends the pool in `onApplicationShutdown`, after Nest has closed HTTP connections.
- `src/database/database.tokens.ts` exports the tokens and three types: `Database` (`NodePgDatabase<typeof schema>`), `Transaction` (the callback argument of `Database['transaction']`), and `Executor` (`Database | Transaction`).
- Repositories inject `@Inject(DRIZZLE) private readonly db: Database`. Nothing else injects the database.

## Schema

- One file per table in `src/database/schema/`, re-exported by `schema/index.ts`. `drizzle.config.ts` and `drizzle(pool, { schema })` both read that index.
- Tables are plural snake_case (`pgTable('projects', …)`), with camelCase properties and explicit column names: `ownerId: uuid('owner_id')`.
- Ids are `uuid('id').primaryKey().defaultRandom()`. Timestamps are `timestamp('created_at', { withTimezone: true }).notNull().defaultNow()`. Updates set `updatedAt: new Date()` explicitly, unless the column declares `.$onUpdate(() => new Date())`.
- Every foreign key states its delete rule: `.references(() => users.id, { onDelete: 'restrict' })` by default, `'cascade'` only for truly dependent rows, `'set null'` on optional keys. Index every foreign key in the table's extra-config callback, because PostgreSQL doesn't.
- Store money as integer minor units, never `real` or `doublePrecision`. Declare uniqueness with `.unique()` or `uniqueIndex()`, so the database decides races. Closed value sets are a `pgEnum`.
- Export the row types beside the table: `export type ProjectRow = typeof projects.$inferSelect`, and `$inferInsert` when inserts need it.

## Repositories

- A repository owns the SQL it runs. Services never import `Database`, `DRIZZLE`, a schema table, or a `drizzle-orm` operator.
- domain-driver generates one repository per action, such as `CreateProject.repository.ts` with one `handle()`. SQL that several flows need goes in a shared repository, such as `<area>/shared/repositories/Project.repository.ts`, with named methods that take domain arguments only: `findById(id)`, never `findById(db, id)`. Pass two or more ids, or any flag, as one object, `handle({ ownerId, id })` or `list({ ownerId, includeArchived })`, so a swapped pair can't compile into a wrong query.
- Shared repositories return table rows. The flow's repository maps rows to the feature's types (see `dtos`), translates database errors, and opens transactions.
- Select only what the caller maps: `db.select({ id: projects.id, name: projects.name })` or the relational API with `columns`. Load related rows with a join or `with`, and counts with `count()` and `groupBy`, never with a query inside a loop.
- Write each column explicitly: `.values({ name: input.name, ownerId })`, `.set({ name: input.name, updatedAt: new Date() })`. Never spread a DTO into `.values()` or `.set()`.
- Single-row reads end in `.limit(1)` and return `row ?? null`. Writes use `.returning()` with the columns the caller needs.
- Scope in the same statement: an update or delete of another owner's row matches nothing, so `where(and(eq(projects.id, id), eq(projects.ownerId, ownerId)))` returns no row, and the action answers 404 (see `security`).
- Translate expected errors where they happen. The Postgres SQLSTATE is the error's `code`, or its `cause`'s `code` when Drizzle wraps the driver error, so read it through one small helper in `src/database/pg-errors.ts` that exports `pgCodeOf(error)` and named checks such as `isUniqueViolation(error)`. `23505` is a unique violation and `23503` a foreign-key violation. Rethrow anything else.

## Transactions

- The repository that owns a write spanning several statements opens `this.db.transaction(async (tx) => …)` and passes `tx` to every statement and shared-repository call inside. Services and controllers never open one.
- A shared-repository method that runs inside a caller's transaction takes a trailing `on: Executor = this.db`. A call that leaves it out silently runs outside the transaction, and nothing fails until a rollback, so add the parameter only to methods that need it.
- Keep slow work out of the callback: hash passwords and call external services before the transaction opens.
- For read-modify-write, use atomic SQL (`.set({ stock: sql\`${products.stock} - 1\` })`) or a conditional update with the expected state in `where` and `.returning()`, then check that a row came back. Serialize work per key with `pg_advisory_xact_lock` inside the transaction.
- Under `serializable` or `repeatable read` isolation, retry the whole transaction a bounded number of times on `40001` and `40P01`.

## Pagination

Every list has a capped `limit`. Large lists page by keyset: order by a unique tuple such as `(createdAt, id)`, select `limit + 1` rows to know whether more exist, and return `{ items, nextCursor }`. Never page large tables with `offset`.

## Example

```ts
@Injectable()
export class CreateProjectRepository {
  constructor(@Inject(DRIZZLE) private readonly db: Database) {}

  async handle(input: NewProject): Promise<Project> {
    try {
      const [row] = await this.db
        .insert(projects)
        .values({ name: input.name, ownerId: input.ownerId })
        .returning(projectColumns);
      return toProject({ ...row, taskCount: 0 });
    } catch (error) {
      if (isUniqueViolation(error)) throw projectNameTaken();
      throw error;
    }
  }
}
```

`projectColumns` and `toProject` come from the feature's mapper (see `dtos`), `isUniqueViolation` from `src/database/pg-errors.ts`, and `projectNameTaken()` is the project's coded 409 error (see `api-responses`).

## Prisma projects

The rules above hold with Prisma's names. A global `DatabaseModule` exports `PrismaService`, which extends `PrismaClient` with a driver adapter (`new PrismaPg({ connectionString })`) and disconnects on shutdown. Run `npx prisma generate` after every schema change. Select with `select`, load relations with nested `select`, and count with `_count`. The repository that owns a multi-statement write opens `this.prisma.$transaction(async (tx) => …)`, and methods used inside one take a trailing `db: Prisma.TransactionClient = this.prisma`. `P2002` is a unique violation, `P2003` a foreign-key violation, and `P2025` a missing record; catch them as `Prisma.PrismaClientKnownRequestError`.

Adapted in part from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
