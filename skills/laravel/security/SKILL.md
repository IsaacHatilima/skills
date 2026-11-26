---
name: security
description: "Use when adding or reviewing Laravel authorization, policies, authentication, API tokens, CORS, CSRF exceptions, file uploads, raw queries, HTML output, rate limits, or production configuration, or before deploying a Laravel application."
---

# Security

Applies to: `app/Policies/**`, `app/Http/**`, `app/Repositories/**`, `app/Providers/**`, `bootstrap/app.php`, `config/**`, `routes/**`.

Middleware, CSRF, and proxies are configured in `bootstrap/app.php`. Gates and rate limiters are registered in `AppServiceProvider::boot()`.

## Authorization

- Every model a user can act on has a policy in `app/Policies/` with one method per ability (`viewAny`, `view`, `create`, `update`, `delete`, `restore`, `forceDelete`). Rely on policy discovery; when names don't follow convention, add `#[UsePolicy(UserPolicy::class)]` to the model.
- Policy methods return `bool` from the user, the model, and its loaded attributes. A check that needs a query, such as team membership, calls an injected action backed by a repository; neither the policy nor the action queries directly (see `architecture`, `repositories`).
- Use a guest-nullable `?User $user` parameter only for abilities that guests may hold.
- In a project using `spatie/laravel-permission`, the FormRequest uses the package's permission API or the project's established permission helper, as `requests` describes; without it, use Gate and model policies. A direct `hasPermissionTo()` check bypasses `Gate::before()`: preserve approved guard, team and super-admin semantics in the existing permission helper explicitly, without inventing new grants or silently substituting Gate. Do not install the package just for authorization.
- On the Gate/policy path, an approved `before()` override returns `true` to grant and `null` to fall through. Returning `false` denies the ability instead of continuing the normal check.
- Authorize in the FormRequest's `authorize()`. Without a FormRequest, use the project's permission-aware controller check for Spatie projects, or `#[Authorize]` for the Gate/policy path (see `requests`, `controllers`). A permission alone does not establish record ownership or tenant access. Route-model binding finds a record; nested routes use `scopeBindings()`, and repositories preserve the caller's allowed record scope.

## Privileged fields and mass assignment

- Keep privileged columns out of `#[Fillable]`: role, admin and verification flags, owner, tenant, and team IDs. Never unguard the model.
- Never take those values from request input. The action passes the authenticated actor or trusted parent to the repository, which sets those columns through scoped relationship creation or explicit attribute assignment.
- Hide secrets from serialization with `#[Hidden]`: password, remember token, two-factor secrets and recovery codes. Resources remain the output contract; `#[Hidden]` is the backstop.
- Use `encrypted` casts for sensitive values stored at rest. Rotate `APP_KEY` with `APP_PREVIOUS_KEYS` so existing encrypted values stay readable.

## Queries and output

- Repositories pass user input to queries only as bindings: `whereRaw('email = ?', [$email])`, never interpolated into `whereRaw`, `selectRaw`, `orderByRaw`, `DB::statement`, or `DB::select`.
- Column names can't be bound. The FormRequest allowlists user-chosen sort and filter values, and the repository maps those keys to real columns (see `requests`, `repositories`).
- In Blade, `{{ }}` escapes and `{!! !!}` does not. Use `{!! !!}` only for HTML the application generated or sanitized with an allowlist sanitizer such as HTMLPurifier. Use `@js()` to put data into a script context.
- In React, JSX escapes by default. `dangerouslySetInnerHTML` takes only server-sanitized HTML.

## Authentication and sessions

- Starter kits and Fortify already regenerate the session on login, and invalidate it and regenerate the CSRF token on logout. Custom authentication controllers do the same.
- Configure password strength once with `Password::defaults()` in `AppServiceProvider` (for example `Password::min(12)->uncompromised()`), then use `Password::defaults()` in every password rule.
- Sanctum tokens get an `expiration` and the narrowest abilities, such as `posts:read`. Routes enforce them with the `abilities`/`ability` middleware aliases. Use Passport only when third-party OAuth clients are required.
- CORS lists explicit origins. `supports_credentials` is `true` only for a first-party SPA, and is never combined with `'*'` origins.

## CSRF and webhooks

- Exclude only stateless endpoints that verify their own signature, such as payment-provider webhooks: `$middleware->validateCsrfTokens(except: ['stripe/*'])`. Never exclude `api/*` wholesale; stateful Sanctum SPA routes rely on CSRF.
- A webhook controller verifies the provider signature before invoking any action.

## Rate limiting

- Define named limiters in `AppServiceProvider` with `RateLimiter::for()`. Key them by user ID, falling back to IP. Apply them with `throttle:<name>`.
- Login, registration, password reset, two-factor, and upload routes always have a stricter limiter than general API routes.
- Let 429 responses flow through the central exception handling (see `api-responses`) instead of building JSON inside the limiter.

## File uploads

- Inspect the uploaded bytes. Client filenames and `Content-Type` headers are untrusted: a shell payload named `mypic.sh.png` with an `image/png` header must fail an image upload. The name alone neither proves nor disproves that its contents are an image.
- Allowlist the formats the endpoint actually needs, and check content, extension and size. Laravel's `File::types()` and `mimes` infer MIME type from content; `extensions` checks the filename separately. For images, start with `File::image()`, an explicit extension allowlist, a byte limit and dimension limits. Leave SVG disabled unless its active content has an explicitly designed sanitization and serving policy.
- MIME/signature checks are preliminary checks, not proof that a file is safe or a complete image. Decode image bytes with the project's maintained image library and reject unsupported, malformed, truncated or undecodable input. Enforce byte, width, height, pixel/frame and processing-resource limits before and during decoding; a small compressed upload can expand dramatically. Never execute an upload to identify it.
- For publicly served raster images, encode a fresh image in an allowed output format and serve that result with its matching MIME type and generated extension, removing unnecessary metadata. Keep the original private only if the feature needs it. Decoding and rewriting reduce risk; they do not guarantee removal of all malicious content. Non-image documents need checks appropriate to their format and the project's malware-scanning policy.
- Store private files on a non-public disk under generated names, outside executable paths. Never use the client filename as a storage path or enable script execution in an upload directory.
- Serve private files only after authorizing the download. Then stream with `Storage::download()` or redirect to a short-lived `Storage::temporaryUrl()` on disks that support it.

Upload tests use actual byte fixtures, not just fake filenames or declared MIME values: a valid allowed image; shell bytes disguised as `mypic.sh.png`; a spoofed MIME header; a corrupt/truncated image; a forbidden format; excessive bytes or decoded dimensions; and a forbidden download. Check that rejected input is not published and that an accepted public image is the newly encoded output.

## Production configuration

- `APP_DEBUG=false`, `APP_KEY` set, `SESSION_SECURE_COOKIE=true`, and HTTPS enforced at the proxy or with `URL::forceScheme('https')`.
- Trust only the load balancer's address ranges: `$middleware->trustProxies(at: [...])`. Never trust `'*'` on a host reachable directly.
- Call `env()` only inside `config/*.php`. After `config:cache`, `env()` elsewhere returns null.
- Set security headers in middleware: `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and a Content-Security-Policy with `frame-ancestors`. Use `Vite::useCspNonce()` when the CSP blocks inline scripts. Omit the deprecated `X-XSS-Protection`.
- Commit `composer.lock` and run `composer audit` in CI.
- Log security events (failed logins, role and permission changes, token creation) to a dedicated channel with the actor ID and IP. Never log passwords, tokens, or full request bodies.

Adapted from [laravel-security](https://github.com/affaan-m/everything-claude-code/blob/main/skills/laravel-security/SKILL.md) in everything-claude-code.

Upload guidance follows [Laravel file validation](https://laravel.com/docs/13.x/validation#validating-files), [OWASP's upload controls](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), and the decoder's documented failure behaviour, such as [PHP GD](https://www.php.net/manual/en/function.imagecreatefromstring.php). Check the installed package version for [Spatie's direct-permission and super-admin behaviour](https://spatie.be/docs/laravel-permission/v8/basic-usage/super-admin).
