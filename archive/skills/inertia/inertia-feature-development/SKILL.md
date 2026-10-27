---
name: inertia-feature-development
description: Plan, implement, or review Inertia page props, navigation, forms, and server validation when the task touches an Inertia application.
---

# Build and review Inertia features

Confirm the installed server adapter, client adapter, and Inertia version, then inspect existing pages and visits. In a Laravel/React app, compose Laravel, React, and this skill; React by itself is not evidence of Inertia.

Use the existing Inertia form and navigation APIs rather than introducing a second fetch/SPA layer. Match the server route, HTTP method, redirect, and page-prop contract already used by the application.

Follow the project's server validation and redirect/error-bag flow. Do not impose a generic JSON-422 response handler on a standard Inertia form. Use the installed adapter's form error state for the matching fields.

Show processing and failure states, prevent duplicate submission with the established form workflow, and preserve/reset form values, focus, and scroll according to the existing interaction.

Authorize in the server action or policy before returning records, shared props, or capabilities. Everything serialized to page props is available to the client; hiding the component does not protect those fields.

Check successful visits, refused actions, field validation, redirect destinations, and back-navigation behaviour with the project's test harness. State which interactions were observed at runtime.

References: Inertia's [forms](https://inertiajs.com/forms) and [validation](https://inertiajs.com/validation) documentation. Use the version matching the installed adapters.

