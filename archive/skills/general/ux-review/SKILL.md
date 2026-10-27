---
name: ux-review
description: Review user flows, role-specific paths, states, copy, and accessibility within a change or audit of an existing product.
---

# Review the user flow

Identify the user-facing flows in the requested scope. For a change review, inspect the changed pages and dependencies; for an audit, inspect the named existing routes and states. Include templates, server-rendered HTML, navigation, and API-backed states; a Node or Nest label does not mean there are no screens. If the scope has no user-facing flow, use the invoking workflow's not-applicable/no-change report.

Trace the requested flow from entry to completion for each relevant role. Look for dead ends, controls the role cannot use, missing confirmation or recovery, and errors that silently lose user input.

Check loading, empty, validation, refused, failed, and success states relevant to the change. Distinguish missing data from data the caller cannot see; a scoped response does not prove that another person or record was deleted.

Use the app's language and established interaction patterns. Copy should describe what happened and what a person can do next. Reuse the project's controls and form conventions.

Check semantic buttons and links, accessible names and labels, keyboard operation, focus after opening/closing an overlay, and whether errors are associated with their fields. Examine the changed flow at narrow and desktop widths.

Use the role's permitted browser workflow where available. Record which routes, states, and roles were actually observed. Review protected flows in source when interaction is unavailable, and label that limit rather than implying an authenticated runtime pass.

Return actionable findings tied to the requested scope: affected user, route or file, observed problem, and expected behaviour. Use the invoking workflow's findings format and keep tastes and out-of-scope suggestions separate. Required flows without evidence remain subject to its verification contract.

