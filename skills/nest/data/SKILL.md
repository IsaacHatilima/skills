---
name: data
description: Use when writing NestJS persistence code with TypeORM or Prisma: wrapping multi-step writes in a transaction, loading relations or fixing N+1 queries, paginating or indexing, caching query results, or creating and running schema migrations.
---

# Data

Applies to: `src/**/*.repository.ts`, `src/**/*.entity.ts`, `src/**/migrations/**`, `src/data-source.ts`, `prisma/**`.

Repository providers, typed inputs, and transaction ownership follow `actions`. Follow the project's existing transaction mechanism (decorator, CLS-bound context); the shape below is the default when none exists.

## Rules

- Queries live in the repository provider. Services call intent-named methods (`findActiveWithMinOrders`), not ORM query-builder chains.
- The public operation owns the transaction: open it once with `dataSource.transaction(async (tx) => ...)` (TypeORM) or `prisma.$transaction(async (tx) => ...)`, and pass the handle (`EntityManager`, `Prisma.TransactionClient`) into repository methods. Repositories and extracted helpers never open a nested transaction.
- Inside a transaction callback, use only the transactional handle. Calling the injected repository or client instead runs outside the transaction without any error.
- Use `QueryRunner` only for manual control; always `release()` in `finally`.
- External effects (payment charge, email, event, job) do not roll back. Run them after commit, emit events after commit (`architecture`), or enqueue (`operations`).
- Avoid N+1: load relations in the repository query (`relations` or `leftJoinAndSelect`; Prisma `include` or `select`), never one query per item in a loop. Returning an entity whose lazy relations get serialized triggers one query per row.
- GraphQL field resolvers batch with DataLoader, one set of loaders per request. A request-scoped loader provider makes every resolver that uses it request-scoped (`architecture`).
- Turn on query logging in development (TypeORM `logging`, Prisma `log: ['query']`) to see N+1 and over-fetching.
- Select only the columns a response needs, use aggregates for counts instead of loading relation trees, index columns used in `where`, `join`, and `order` (composite indexes in query order), and paginate every list with a capped `limit` (`security`).
- Caching with `@nestjs/cache-manager`: TTLs are in milliseconds. `CacheInterceptor` keys by URL, so never use it on per-user responses, and a fixed `@CacheKey('x')` on a parameterized route serves one entry for every id. For anything else cache in the service with explicit keys and delete them after the write commits. Do not cache by default.
- Change schema only through committed migrations. `synchronize: true` can drop columns; keep it off outside a throwaway local database. Prisma: `migrate dev` locally, `migrate deploy` in CI and production, never `db push` on a shared database.
- Migration CLIs need a standalone `DataSource` file that reads the same validated env as the app (`operations`), not raw `process.env` with `parseInt`.
- Run migrations as a deploy step before the new version starts, not through `migrationsRun: true` on every replica's boot.
- Write `down` only when it truly reverses the change; say so in the migration when it cannot. Renames and drops are expand, backfill, switch code, contract, across separate deploys, not add, copy, and drop in one migration while old code still runs.

## Example

```ts
@Injectable()
export class CreateOrderService {
  constructor(
    private readonly dataSource: DataSource,
    private readonly orders: OrderRepository,
    private readonly events: EventEmitter2,
  ) {}

  async handle(actor: AuthenticatedUser, input: CreateOrderDto): Promise<Order> {
    const order = await this.dataSource.transaction((tx) =>
      this.orders.createWithItems(tx, actor.id, input),
    );
    this.events.emit('order.created', new OrderCreatedEvent(order.id)); // after commit
    return order;
  }
}

// OrderRepository
async createWithItems(tx: EntityManager, userId: string, input: CreateOrderDto): Promise<Order> {
  const order = await tx.save(Order, { userId, status: 'pending' });
  await tx.save(OrderItem, input.items.map((item) => ({ ...item, orderId: order.id })));
  return order;
}
```

Adapted from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
