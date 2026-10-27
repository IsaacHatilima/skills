---
name: access-control-review
description: Implement or review server-side permissions, trusted caller identity, and scoped data access for changed feature actions.
---

# Trace access control per action

Take the requested permission matrix one action at a time. When no matrix is supplied, derive the actions and allowed callers from the stated review scope and the project's existing policies, and record that basis. Identify its public entry point, caller authentication, authorization decision, data query or mutation, and returned fields. Reuse the project's policy and tenant model.

- Obtain the caller from trusted session/authentication context. Caller identity must not be taken from a body, query, or path field. Distinguish the caller from legitimate target fields such as an assignee; target selection still requires validation and authorization.

- Check permission for the particular record and tenant, including read/list operations. A valid identifier or successful route-model lookup does not establish ownership. Scope queries as well as controls.

- Validate at the server boundary with the project's existing mechanism. Use parameterized data access and the existing safe handling of files, commands, and templates.

- Check the server's serialized output, shared page props, logs, and errors for fields the caller cannot read. UI omission is not a server filter. Preserve framework escaping when rendering user content.

- Follow actual server handlers, including Server Actions and server functions. A protected page or layout is not evidence that a separately callable mutation is protected. In a monorepo, inspect the package that owns enforcement.

Check allowed callers and refused callers with the project's test setup. For an external API, document which guarantees cannot be established in this repository. Client permission gates remain presentation.

Use the invoking workflow's review scope and severity contract. For a change review, compare with the base and distinguish introduced/worsened problems from pre-existing concerns. For an audit of existing code, report reachable vulnerabilities in the requested scope even when they predate a change. Include the action, affected caller, path, and impact. A permission check that exists only in the client cannot satisfy a server permission requirement.

Use the selected stack skill for the framework's enforcement points; do not add a second, competing authentication mechanism.

