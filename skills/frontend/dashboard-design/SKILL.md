---
name: dashboard-design
description: Use when designing, building, or reviewing a dashboard, admin panel, data table, activity or audit log, share/settings popover, or first-run experience, especially when the UI looks fine but feels generic, cluttered, or hard to use.
---

# Dashboard design

A dashboard exists to display data. Three things separate one that was used from one that was only drawn: the data shapes the UI, each action is placed by how often it is needed, and the UI users can't see at first glance is designed too.

## 1. Let the data shape the form

Choose each presentation from the data, not from the component you reached for first.

| Data | Present it as |
|---|---|
| Small closed set: department, status, severity, category | Chip with a coloured dot or icon plus text |
| Numbers: counts, amounts, durations | Right-aligned with tabular numerals, so digits line up by place value |
| Long text: emails, descriptions | Truncated, with the full value on hover |
| Inactive, archived, or deactivated records | Kept in place, row dimmed |
| People: actor, owner, reporter | Avatar plus name; faces are recognised faster than names are read |
| Events ordered in time: history, audit log, activity, approvals | A timeline, not a table, in a side panel or a second column beside the main table |
| Records whose volume over time users track: incidents, sign-ups, orders | A summary chart of counts over time above the table, with the total |

Colour comes from the data: status, severity, category, urgency. Keep chrome such as headers, tabs, and borders neutral. Pair every colour with text or an icon.

## 2. Place every action on the spectrum of explicitness

Rank each action by frequency and importance, then place it:

| Explicitness | Placement | Examples |
|---|---|---|
| Highest | Always visible, labelled | Primary Add, Share button |
| High | Visible icon with tooltip | Sort, filter, search |
| Medium | Popover or drawer opened in place, not a new page | Share settings, record details |
| Low | Revealed on row hover and keyboard focus, with tooltip | Copy cell, remove member, comment |
| Lowest | Overflow menu, destructive items confirmed or undoable | Archive, delete |

Inside a popover, put the primary action at the top, ready to use, such as the invite field in a share popover. Anything revealed on hover must also appear on focus and stay reachable on touch through a menu or swipe.

Onboarding is the same idea over time. Start with one pointer to the single most important action. After the user completes it, reveal the next step or a checklist with progress, such as "4 of 6 complete".

## 3. Design the UI you can't see

Before calling a dense component done, specify its hidden layer:

- A tooltip on every icon-only control and every ambiguous label or abbreviation.
- Hover and focus affordances: copy on cells, comment indicators and threads, row actions.
- Every popover, drawer, and modal, with its empty, loading, error, and no-permission states.
- Rare moments: new-feature announcements, the first-run checklist, empty states.

A new feature often belongs in one of these layers rather than on a new page.

## Common mistakes

| Mistake | Fix |
|---|---|
| History or audit log built as a table tab | Timeline in a drawer or side column |
| Numbers left-aligned; status and category as plain text | Right-aligned numerals; chips |
| Inactive rows look identical to active ones | Dim them |
| Time-stamped records with no overview | Summary chart above the table |
| Accent colours on headers and tabs | Neutral chrome; colour only for data |
| A permanent Remove button on every row of a member list | Reveal it on hover and focus, with a tooltip |
| Several onboarding tips or a feature modal shown at once | One pointer, then the next step or a checklist |
| Icon buttons without tooltips | A tooltip on every icon-only control |

Source: Kole Jain, [The 3 dashboard UI flaws that give away you've NEVER built one](https://youtu.be/Ksx9C2-3yMo). Reference designs are in the [Figma file](https://www.kolejain.com/resources?scrollTo=dashboard-flaws).
