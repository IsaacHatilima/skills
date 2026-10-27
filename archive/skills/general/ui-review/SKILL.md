---
name: ui-review
description: Review target screens against an existing product's components, design tokens, layout, and responsive behaviour in a change or audit.
---

# Review visual consistency

Identify the visual surfaces in the requested scope. For a change review, inspect the changed routes, templates, components, and styles; for an audit, inspect the named existing screens. Server-rendered pages count. A framework name alone cannot justify a not-applicable or no-visual-change verdict.

Read the project's theme, tokens, global styles, component library, and neighbouring screens before judging the result. Use the existing product as the reference. Do not redesign the system during a feature review.

- Check colours, type scale, spacing, surfaces, borders, and radii against the project's tokens and shared controls.

- Look for inconsistent one-off styles where a maintained component or theme value exists. Respect intentional exceptions already present in the product.

- Check hierarchy, alignment, long labels and content, empty/error states, and horizontal overflow at desktop and narrow widths.

- Check readable contrast and visible interaction/focus states using the actual rendered colours when runtime inspection is available.

Use the invoking workflow's browser permissions and screenshot procedure. Separate a visual observation from an inference based on source. Report unvisited protected pages as a coverage limit.

Write findings for visible breakage or in-scope inconsistencies with a route or file and a concrete correction. Place matters of taste under Notes. Preserve shared component primitives unless changing them is part of the authorized task.

