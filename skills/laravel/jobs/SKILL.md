---
name: jobs
description: Use when adding or reviewing Laravel queued jobs, listeners, or background work such as exports, reports, webhooks, imports, and notifications, or when a request is slow because it does work the user doesn't need to wait for.
---

# Jobs

Applies to: `app/Jobs/**`, `app/Listeners/**`, `config/queue.php`.

## Rules

- Queue slow or external work that the response doesn't depend on: exports, reports, imports, outbound webhooks, third-party API calls, bulk notifications.
- A job is a transport like a controller. Its `handle()` resolves typed input and calls an injected action. The action owns the queries, writes, and transaction (see `actions`).
- Dispatch after commit when the job depends on a write. Use the queue's `afterCommit` behaviour or dispatch from `DB::afterCommit()` (see `actions`).
- Pass models or IDs, not large payloads. `SerializesModels` re-fetches the model when the job runs. Set `$deleteWhenMissingModels = true` when a deleted record should cancel the job.
- Make the work idempotent: a retry after a partial failure must not duplicate a charge, email, or row. The action checks, under a lock, for the state the job is meant to produce, or keys the external call with an idempotency key.
- Bound retries with `$tries` or `retryUntil()`, and set `$backoff` for external services. Implement `failed()` to record or alert on final failure.
- Use `ShouldBeUnique` or the `WithoutOverlapping` middleware when two copies running at once would conflict.
- Use the `RateLimited` middleware with a named limiter for jobs that call rate-limited APIs.
- Implement `ShouldBeEncrypted` when the payload carries personal or secret data. Encryption protects the payload at rest in the queue store.
- A queued listener handles one event and follows the same rules.

## Testing

- Feature tests for the dispatching action assert the job was pushed with `Queue::fake()` and `Queue::assertPushed()`.
- Separate tests run the job's `handle()` with real actions and faked external services. A queue fake proves intent, not execution (see `tests`).

### Example

```php
<?php

declare(strict_types=1);

namespace App\Jobs\Invoices;

use App\Actions\Invoices\DeliverInvoice;
use App\Models\Invoice;
use Illuminate\Contracts\Queue\ShouldBeEncrypted;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\Middleware\RateLimited;

final class SendInvoice implements ShouldQueue, ShouldBeEncrypted
{
    use Queueable;

    public int $tries = 5;

    /** @var list<int> */
    public array $backoff = [10, 60, 300];

    public bool $deleteWhenMissingModels = true;

    public function __construct(public Invoice $invoice) {}

    /** @return list<object> */
    public function middleware(): array
    {
        return [new RateLimited('mail-provider')];
    }

    public function handle(DeliverInvoice $deliver): void
    {
        $deliver->handle($this->invoice);
    }
}
```

The job only delegates. `DeliverInvoice` makes retries safe: inside its transaction it locks the invoice, returns early when `sent_at` is already set, and records `sent_at` with the delivery.

Adapted in part from [laravel-security](https://github.com/affaan-m/everything-claude-code/blob/main/skills/laravel-security/SKILL.md) and [laravel-patterns](https://github.com/affaan-m/everything-claude-code/blob/main/skills/laravel-patterns/SKILL.md) in everything-claude-code.
