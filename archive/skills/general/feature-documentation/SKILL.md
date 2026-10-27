---
name: feature-documentation
description: Write or update feature documentation that separates intended behaviour, demonstrated behaviour, and unresolved limitations.
---

# Document the demonstrated feature

Read the workflow's brief, implementation/test evidence, outstanding findings, and existing documentation. Explain behaviour for the product's users; API-only features may be documented for API clients.

Expected describes the requested capability. Actual describes what the evidence establishes now, with unresolved limitations in plain language. Preserve existing documented capabilities when extending a page.

Use the invoking workflow's page shape, status names, and index contract. A prepared branch document does not establish that code was merged, deployed, or made available to production users. Say which stage the evidence covers.

If a required criterion is unverified or a blocker remains, report that limitation using the workflow's incomplete/non-shipped status and explain the missing behaviour or prerequisite. Do not turn a source check into a claim about an unobserved interaction.

When maintaining dated feature pages, preserve Created and update Modified using the current date. Update only the relevant index entries and preserve unrelated content. Links and code-folder references must resolve.

Keep implementation details out of product-facing prose unless they help an API client use the capability. Put technical check evidence in the report assigned by the workflow.

Write only the files the invoking workflow assigns. Create a commit only when that workflow authorizes one, using its reporting and completion contract.

