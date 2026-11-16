# Learning skill and Factory teacher

Status: design for implementation; no learning workflow has been implemented.

## Intent

Keep the reasoning behind verified fixes available to future agents. A login review may uncover a request race, permission error, query problem, or inaccessible form interaction. The next agent working on registration should find the applicable lesson before repeating the mistake.

Primary readers are agents. Success means agents retrieve relevant, evidence-backed lessons before specification, implementation and review, with fewer repeated findings. A knowledge entry never substitutes for checking the current code.

## Decisions settled in the conversation

1. Provide a reusable learning skill, callable outside Factory, and a dedicated Factory teacher that uses it.
2. Keep feature documentation with the existing documenter. The teacher writes reusable engineering knowledge.
3. Group the index by technical area: UI/UX, Database and Queries, Hooks and State, Authentication and Security, APIs and Integrations, Testing, and other areas when lessons justify them. Do not create empty categories.
4. Give each entry a title, short applicability description, tags and a link to its lesson. Use one primary category and tags for other relevant areas.
5. Capture lessons after a fix is confirmed by review, making them available to subsequent rounds. Update an existing lesson when the same issue recurs.

The operational choices below are proposed implementation details, not additional decisions attributed to the user.

## Approaches considered

- **Add lessons to feature documentation:** little new machinery, but the documenter deliberately describes product behaviour and omits review history and implementation detail. This makes reusable technical lessons hard to retrieve.
- **Write lessons once at the end of a job:** fewer teacher calls, but no new lessons reach the current job's later rounds.
- **Dedicated teacher after confirmed fixes:** selected. Batch confirmed fixes after a review round, preserve feature documentation's purpose, and make knowledge available before another build starts. Avoid one teacher invocation per individual finding.

## Learning skill and knowledge files

Proposed skill location: `skills/knowledge/learning/SKILL.md`, installed as `knowledge-learning`. Include it in `all` and in the core bundle used by Factory; allow a knowledge-only bundle so another workflow can use it independently.

The skill covers two operations: retrieve lessons relevant to the current task, and record or revise lessons from verified outcomes. The invoking workflow supplies evidence, write scope and ownership. The skill itself neither starts Factory nor changes application code.

Default project storage:

```text
Knowledge/
  index.md
  ui-ux/
    preserve-form-feedback-during-submission.md
  hooks-and-state/
    ignore-responses-from-previous-sessions.md
  database-and-queries/
    serialize-conflicting-state-transitions.md
```

These are illustrative paths, not lessons to create without evidence. Prefer an existing project knowledge location when project guidance names one. Keep the collection project-local initially.

`index.md` uses category headings and small tables:

```markdown
## Hooks and State

| Lesson | Use when | Tags |
|---|---|---|
| [Ignore responses from previous sessions](hooks-and-state/ignore-responses-from-previous-sessions.md) | Async requests can finish after account or session changes. | async-state, sessions, authentication |
```

Each lesson contains:

- Stable identifier, primary category, tags, last verification date and status.
- Applicability and prerequisites, including relevant framework or library versions when they matter.
- The concrete failing scenario and root cause.
- The accepted fix and why it works; rejected alternatives only when the reason is useful for future decisions.
- Prevention guidance and the regression check that demonstrates the fix.
- Limits and cases where the solution should not be reused.
- Durable provenance: repository, issue or PR, original finding, fix commit, verification commit and relevant code/test paths.

Summarise the evidence in the lesson. Local `factory/jobs/` reports are useful inputs but are ignored by Git and cannot be the sole evidence available to a future checkout. Do not store credentials, private fixture contents, or entire transcripts.

## What counts as a lesson

Reviewers explicitly identify resolved findings, referencing the original review round and finding identifier. They confirm the fix against the current reviewed commit and state the evidence and its limits. An overall CHANGES verdict can still confirm one earlier fix while another finding remains open.

The teacher reads earlier findings, the builder's per-round log, code changes, gate results and the explicit resolution. A builder's claim, a missing finding in the next report, or an overall PASS alone does not establish the resolution of a particular finding.

Capture a lesson only when it provides reusable reasoning beyond a mechanical edit. Unresolved findings remain job work. A dismissed finding can become a lesson about why that scenario was not a defect, provided the rejection has an explicit, evidenced resolution; never describe it as a repaired bug.

Do not generalise an application-specific choice into a universal rule. Source inspection, focused tests, browser observation and broader runtime behaviour establish different things; preserve those limits in the lesson.

## Review and teaching flow

```text
specification -> build -> gate -> all routed reviews
                                  |
                   resolved findings since last teaching?
                         | yes                 | no
                         v                     |
                       teacher                 |
                         +---------------------+
                                  |
                      more fixes / document / human handoff
```

The existing gate-failure loop remains unchanged: no reviewer runs on a failing gate. Initially, teach review-confirmed fixes. Gate failures may appear in their evidence, but a green rerun by itself is not a separate automatic lesson trigger.

After every routed reviewer has finished, validate the reports and unchanged reviewed commit before entering teaching. If there are new explicit resolutions, run the teacher once for that batch. If not, preserve the existing transition without an extra agent call. A last allowed round may still have useful confirmed fixes even when the job goes to a person for remaining problems.

The teacher changes only the job worktree's `Knowledge/` files and its own round report, for example `round-N/teach.md`. It updates existing matching lessons and the index, commits only knowledge changes, and leaves a clean worktree. It never edits product code, tests, feature documentation, skills, other agents' reports or another checkout. Scripts own job state and pushing.

Teaching has a distinct, resumable stage. Store the reviewed code commit separately from the resulting knowledge commit. Validate that every change between them is an ordinary Markdown file under the approved knowledge root; refuse symlinks or changes outside that scope. The existing check that reviewers changed neither HEAD nor the worktree still runs before the teacher can write. Never rewrite a gate receipt to claim it covered the later knowledge commit.

Preserve the review result, remaining round budget and intended next stage across teaching. A teacher no-op is valid when the evidence yields no reusable lesson. Record processed finding identifiers and the teacher's result so resuming the stage cannot create duplicate lessons or commits. Refuse an invalid teaching result and use the existing bounded retry/handoff behaviour rather than advancing silently.

When another build is needed, establish its round baseline after the teacher's commit. The builder reads the new lessons before making further changes. The documenter's baseline likewise starts after teaching, preserving its existing restriction to feature documentation. Final approval and branch merging retain their current checks.

## Finding and using lessons

Spec writers, builders and reviewers read the index and select lessons by applicability, tags and the actual touched behaviour. Search across categories: a registration task can need a login lesson under Hooks and State. Read only matching entries, not the entire collection.

Record selected lesson identifiers and paths with the spec or role report so use can be checked. Builders refresh the selection on later rounds when new teaching has happened. Reviewers use the lessons as evidence-backed references and still prove a finding against the current requirements and code. Project instructions and the current contract take precedence over historical advice.

An empty or absent collection means there are no lessons yet. It does not block a new project. A stale reference is reported and checked against current code, not applied mechanically or treated by itself as a product defect.

## Visibility, maintenance and concurrency

Lessons are available immediately on the job branch after teaching. They become shared project knowledge when that branch merges. Already-running jobs do not automatically receive another branch's new files; they see lessons after their normal base update. Do not claim that every active job instantly shares knowledge.

Each teacher writes only its own branch. Concurrent jobs can update the index independently; merge handling must preserve both additions and reconcile duplicate or conflicting lessons without replacing the current implementation's rules with stale advice. Do not introduce a shared writable knowledge directory outside Git.

Keep fixes on unmerged branches distinguishable from adopted project behaviour in their provenance. A failed or abandoned job does not publish knowledge automatically. A future explicit extraction can preserve a verified lesson from that job without carrying its unfinished product changes.

Revise a lesson when its advice changes, preserving the reason and relevant evidence. Mark replaced lessons as superseded and link the replacement. Do not append another near-identical entry for every recurrence. Promote a lesson to a shared skill only through a separate deliberate change when it applies across projects.

## Verification and completion criteria

Implementation should establish:

1. The learning skill installs independently and through `all`; Factory installs the teacher with explicit host model/tool settings.
2. Original finding -> fix -> explicit reviewer resolution produces a lesson with durable provenance. Open or merely omitted findings do not.
3. Partial resolutions can be taught while unrelated CHANGES remain; a clean first round and repeated resume do not create unnecessary teacher calls or duplicate entries.
4. Teaching cannot alter product code, overwrite another role's artifacts, bypass review completion, consume an extra build round, or weaken the checked-commit invariant.
5. Later rounds find their newly recorded lesson, and a later feature on the merged base retrieves it by applicability across feature names and categories.
6. Two branches' knowledge changes can be reconciled without dropping lessons; unmerged work is never represented as shipped behaviour.
7. Existing Factory transitions, feature documentation ownership and human escalation still work.

Use isolated temporary repositories and fake provider calls for transition and installation checks. Also exercise one small realistic two-feature scenario: a confirmed login defect becomes a lesson, and registration's spec and builder read it before implementation. That proves retrieval and adherence in that scenario; reduced review rounds across real work remains something to measure.

Choices left to implementation: the teacher's exact host model settings, finding-identifier syntax, compact round-report fields and matching heuristics. Start with Markdown, the grouped index and ordinary repository search; no embedding service or separate database is required.
