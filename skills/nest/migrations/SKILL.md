---
name: migrations
description: Use when adding or changing a table, column, index, relation, or constraint in a NestJS app, writing a backfill, or running migrations locally, in CI, or in production. Drizzle Kit by default; a project already on Prisma keeps Prisma Migrate.
---

# Migrations

Applies to: `src/database/schema/**`, `drizzle/**`, `drizzle.config.ts`. Project guidance and existing conventions win over these defaults.

## Rules

- Change the table in `src/database/schema/` first, following the conventions in `database`. Then generate the migration with the project's script, such as `pnpm db:generate --name add_project_archived_at`, or `npx drizzle-kit generate --name add_project_archived_at`.
- Commit the schema change, the new `drizzle/<index>_<name>.sql`, and the `drizzle/meta/` journal and snapshot together. Never edit the `meta/` files by hand.
- Read the generated SQL before committing.
- Drizzle Kit stops to ask whether a column or table is new or renamed. Don't guess at that prompt: avoid renames in feature work (see **Expand and contract**), and when one is required, ask the person who owns the schema.
- Backfills and SQL the schema can't express go in an empty migration made with `npx drizzle-kit generate --custom --name backfill_project_slugs`, which you then fill in.
- Never edit a migration that has run outside your machine; add a new one.
- `drizzle-kit push` is for throwaway prototypes only. A project with a `drizzle/` folder always generates and applies migrations.
- CI and production apply pending migrations with `drizzle-kit migrate`, or `migrate()` from `drizzle-orm/node-postgres/migrator`, as a deploy step before the new version starts, not at application boot on every replica. Drizzle records applied migrations in `drizzle.__drizzle_migrations`.

## Expand and contract

A rename, a type change, or a new required column spans separate deploys, because the old version keeps running while the new one rolls out:

1. Expand: add the new column or table, nullable or with a default.
2. Backfill it, and have the code write both shapes.
3. Switch reads to the new shape.
4. Contract: make it required, and drop the old column in a later migration.

Never add a required column without a default to a table that has rows, or drop a column the running version still reads.

## Verify

- `npx drizzle-kit check` reports no inconsistent or colliding migrations.
- The e2e suite runs against a test database built from the real migrations (see `tests`).

## Prisma projects

Change `prisma/schema.prisma`, then run `npx prisma migrate dev --name add_project_archived_at` against your local database and `npx prisma generate` afterwards, because Prisma 7's `migrate dev` no longer regenerates the client. Commit the schema with `prisma/migrations/<timestamp>_<name>/migration.sql`. Use `--create-only` when the SQL needs editing: a renamed field generates a drop and an add, which loses data, so edit it into `RENAME COLUMN` or keep the column and rename only the field with `@map`. `migrate dev`, `migrate reset`, and `db push` are for local databases; CI and production run `npx prisma migrate deploy`, and `npx prisma migrate status` shows nothing pending.

Adapted in part from [nestjs-best-practices](https://github.com/IsaacHatilima/agent-nestjs-skills/tree/main/skills/nestjs-best-practices) (MIT).
