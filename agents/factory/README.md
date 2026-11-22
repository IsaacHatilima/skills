# Factory

Factory turns a description into a reviewed, documented pull request. Run `/factory add a login page` and it creates a local job, checks the scope, writes a spec with the skills each role must read, builds it, tests it with the project's own checks, reviews it, records reusable lessons from confirmed fixes and documents the feature. The approver merges what it approves and hands a person the rest. GitHub provides branches and pull requests; no GitHub issue or label is needed.

```text
/factory <description>         create a local job and build it
/factory setup                 prepare a project once: config, checks, AGENTS.md
/factory run                   drain and resume the local queue
/factory run <job>             start or resume one local job
/factory mitarbo <task-key>    read one named Mitarbo task and build its request
/factory <feedback>            ask about jobs, answer questions, give feedback or reject a job
```

Claude Code runs it as `/factory`. Codex has no per-skill slash commands, so there it is `$factory` (or pick it from `/skills`). [AGENT.md](AGENT.md) is the orchestrator; [SKILL.md](SKILL.md) is the thin command adapter both hosts load.

## The loop

```text
description or explicitly named external task
        │
        ▼
intake ──── NEEDS-INFO → questions shown in the conversation, waits for an answer
        │   REJECT     → records the reason locally
        ▼ ACCEPT, maybe rescoped; rates risk + surfaces
route (script)     picks the reviewers from config.json
        ▼
spec-writer → spec.md: packages, stacks, selected skills, contract, permissions, criteria
        ▼            BLOCKED (missing skill or prerequisite) → a person
builder → commits, pushes, opens a draft PR referencing the local Factory job
        ▼            ▲
gate (script) ─FAIL──┤  factory/checks.sh; no reviewer runs on a failing build
        ▼ PASS       │
reviewers ─CHANGES───┘  code, + ux & ui on UI changes, + security on security changes
        ▼ completed review round with newly confirmed earlier findings
teacher → one batched update to project lessons, then the saved build/document step
        ▼ all PASS, or the build is blocked or out of rounds
documenter → Documentation/<Feature>.md and Documentation/index.md, one commit on the branch
        ▼ shipped                                 not shipped → a person
approver ── APPROVE  → sync with the base, gate again, gh pr merge
         └─ ESCALATE → PR ready for a person, local job waits in needs-human
```

Brainstorming and grilling are standalone conversations outside Factory. Use the combined `planning-brainstorming` skill to explore an idea and settle its decisions, then supply the agreed design with a feature request if you want Factory to build it. Factory has no grilling command or interactive planning stage. Intake still records blocking NEEDS-INFO questions for the orchestrator to show in the conversation, and waits for locally recorded answers.

One session orchestrates every job, `concurrency` at a time (default 3). Each job gets its own worktree at `.worktrees/<job-id>` on `factory/<job-id>`. All state lives in `factory/jobs/`, so if the session dies, `/factory run` picks every job back up. A person approves an escalated job by merging its PR, or sends it back with `/factory <feedback>`.

Builders commit completed, independently reviewable implementation steps as they go, keeping each change with its related tests. Large features are split into separable steps, with focused checks per chunk and the final gate at the end. Commit boundaries follow the work's purpose, without a fixed line-count target.

## Learning between review rounds

The reusable [learning skill](../../skills/knowledge/learning/SKILL.md), installed as `knowledge-learning`, retrieves and records project engineering knowledge. Spec-writer, builder and reviewers search the grouped index and read relevant lessons before their work, recording IDs and paths or `None applicable`. A login lesson can therefore inform registration through tags and applicability rather than a shared feature name.

The [teacher](teacher.md) runs once for the completed round's batch of explicitly confirmed earlier findings. Reviewers give findings stable IDs and write their verified `fixed` or `dismissed` outcomes in `resolutions-<lens>.json`; PASS or omission alone creates no lesson. The teacher can capture a confirmed repair while another finding remains CHANGES. It updates an existing lesson when the cause recurs, or records no change when there is no reusable conclusion.

Knowledge defaults to `Knowledge/`, with `index.md` grouped by populated technical area and one file per lesson. `factory/config.json` may set `knowledge.root` to a safe repository-relative location. Each lesson explains applicability, the problem/cause, solution, prevention, evidence and limits. The teacher commits knowledge only; the documenter continues to write feature behaviour under `Documentation/`. Teaching preserves the gate/review code commit, has its own validated report and consumes no build round.

No collection is seeded by installation. New lessons help later rounds on that branch and reach other jobs through normal merging and base updates. The skill also works outside Factory: `./install knowledge` installs it without the workflow. A historical lesson informs a review; it never lowers the proof required for a finding or overrides current requirements.

## Request sources and local job ids

Plain descriptions work in any project with Factory set up. Jobs have ids such as `004-dark-mode`; commands also accept their local sequence number (`4`). `/factory run` resumes the saved local queue. It does not discover work by listing GitHub issues or external tasks.

Mitarbo is optional. `/factory mitarbo MDE-21` asks the host's connected Mitarbo `get_task` tool for that one task, saves its returned description and context in the local request, and records its key and link. It never imports a task backlog or silently substitutes another task source. If the read tool is unavailable, paste the description instead. A task read does not authorize status updates, comments or replies; those need a separate explicit request and must follow the connected tool's requirements.

Mitarbo jobs include the task key in lowercase in their job id and branch, even when the title omits it. For example, `MDE-21` with title `Registration` can create `factory/001-mde-21-registration`. The script assigns the name, keeps an existing task-key prefix only once, and all agents retain that assigned branch.

When intake needs a decision, the orchestrator shows its questions in the conversation. Your answer is saved through `job answer <job>` and intake resumes when a slot is available. Feedback and rejection are recorded locally; PR state still comes from GitHub. The original description remains available in `request.md`, including any source snapshot and recorded answers.

## Agents

Each role is one file here, with the model, reasoning effort and tools for both hosts in its frontmatter. The installer renders them into `.claude/agents/<name>.md` and `.codex/agents/<name>.toml`; the orchestrator never overrides a model.

| Role | Writes | Claude Code | Codex | Runs |
|---|---|---|---|---|
| [intake](intake.md) | `intake.md` | fable, high | gpt-6-astra, high | every request |
| [spec-writer](spec-writer.md) | `spec.md` | opus, high | gpt-6-astra, high | every accepted job |
| [builder](builder.md) | code, PR, `build.md` | opus, high | gpt-6-sol, high | every round |
| [reviewer-code](reviewer-code.md) | `review-code.md` | sonnet, high | gpt-6-sol, high | every round that passes the gate |
| [reviewer-security](reviewer-security.md) | `review-security.md` | opus, high | gpt-6-astra, high | `security` surface |
| [reviewer-ux](reviewer-ux.md) | `review-ux.md` | sonnet, medium | gpt-6-luna, medium | `ui` surface |
| [reviewer-ui](reviewer-ui.md) | `review-ui.md` | sonnet, medium | gpt-6-luna, medium | `ui` surface |
| [teacher](teacher.md) | project knowledge Markdown, `teach.md` | sonnet, high | gpt-6-sol, high | completed review round with new confirmed resolutions |
| [documenter](documenter.md) | `Documentation/` commit | sonnet, high | gpt-6-sol, high | once the build ends |
| [approver](approver.md) | `decision.md` | opus, high | gpt-6-astra, high | shipped jobs |

Source frontmatter keys are `name`, `description`, `claude-model`, `claude-tools`, `claude-effort`, `codex-model` and `codex-reasoning-effort`. The builder also has `claude-stop-hook`, which the installer turns into a Claude Code `Stop` hook that runs the checks before the builder finishes, as a nudge; the gate still decides.

## Scripts

The deterministic stages are Python 3.10+ standard library, in `bin/`:

- `bin/job` is the only writer of `job.json`. `advance` refuses illegal moves and checks each agent stayed in its lane: the builder pushed, opened the PR and left `Documentation/` alone; reviewers and the approver changed nothing; the documenter committed only under `Documentation/` and its page's status matches the outcome; every skill the spec selected is still readable. It also owns local request/answer records, PR side effects, the merge, `init`, and the prompt header (`job header <id> [builder|ux|ui]`).
- `bin/gate` runs the main checkout's `factory/checks.sh` in the job's worktree, with `FACTORY_BASE` set, and fails a branch that modifies `protected_paths`.
- `bin/route` maps intake's risk and surfaces to reviewers through `config.json`.

The scripts find the project from the current directory (the main checkout, even from inside a worktree), so they work from a project install or a user install alike. `templates/` holds what `job init` copies into a project: `config.json`, `checks.sh` and the `dashboard.html` board.

## Skills

The factory reads the shared [catalog](../../skills/catalog.md) named in the project's `factory/config.json` and applies its [selection rules](references/skills.md). The spec-writer records each selected skill's absolute path and the roles that read it in `spec.md`; the scripts refuse to start a stage while one of those files is missing. Scaffolding follows the project: Artisan in Laravel apps, including their React frontend; domain-driver only in JavaScript packages that use it; otherwise an explicit manual strategy.

## Install

From this repository's root:

```bash
./install basic                                # the factory and core skills, for your account
./install web api                              # several bundles install their union
./install basic --project ~/code/app --host claude   # into one project, Claude Code only
```

| Installed at `<root>` (`~` by default, or the project with `--project`) | For |
|---|---|
| `.ai/skills/factory/` | the one copy of the factory: AGENT.md, bin/, templates/, references/ |
| `.ai/skills/catalog.md`, `.ai/skills/<group>-<name>/` | the bundle's shared skills, one copy each |
| `.claude/skills/factory/SKILL.md`, `.claude/agents/*.md` | Claude Code: the `/factory` pointer and the ten agents |
| `.agents/skills/factory/SKILL.md`, `.codex/agents/*.toml` | Codex: the `$factory` pointer and the ten agents |
| A block in `AGENTS.md` and `CLAUDE.md` | where every agent finds the skills |

Every bundle in `bundles.json` that lists the `factory` workflow installs it, with the skills its roles select. The installer never overwrites a file that differs without `--force`, and writes nothing when any would be.

Then, in each project, run `/factory setup` (`$factory setup` in Codex) once. It needs a GitHub `origin`, an authenticated `gh` that can push branches and open pull requests, and `python3`. It writes `factory/config.json`, `factory/checks.sh` and `factory/dashboard.html`, ignores `factory/jobs/` and `.worktrees/`, fills `checks.sh` with the project's real lint, typecheck, test and build commands, adds a Software factory section to `AGENTS.md` (project purpose, security hot spots, design system, users, what a person must always see), verifies, and commits on the current branch. Push that commit before the first run: jobs branch from `origin/<base>`.

## Dashboard

```bash
cd factory && python3 -m http.server
```

Open <http://localhost:8000/dashboard.html>. Each job is a card with its request source and PR, gate and review chips per round, its documentation status, risk, cost and time. Click a card to read every file the job wrote. Cost and tokens cover the job's subagents in both tools, read from Claude Code's transcripts and Codex's session logs. Dollars are API-equivalent for models priced in `prices_usd_per_mtok`; add your Codex models there to count theirs, since unpriced models add tokens only.

## Cost and safety

- It opens and merges real PRs. Start with `concurrency: 1` and read every PR until you trust it.
- Intake runs on Fable once per request. Depending on your plan, Fable can bill to usage credits rather than the plan's included usage.
- Only descriptions and external tasks explicitly submitted by the user become jobs. Request and external-task text reaches agents as quoted data in `request.md`, never as instructions that control their tools or verdicts.
- The factory pushes only `factory/*` branches, merges only through `gh pr merge`, and never deploys.

## Tests

```bash
python3 -m unittest discover -s tests
```

The tests run the scripts against a throwaway git repository with a bare origin and a fake `gh`, through every stage and refusal, and install into temporary projects and homes.

## License and credit

The workflow, scripts and dashboard are adapted from the [ZazenCodes software factory v2](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code-v2) and are licensed under the [GNU GPLv3](LICENSE), like the original. This version adds the documenter stage, skill selection and checking, the scaffold strategy, a project-or-user installer for Claude Code and Codex, and per-agent models in place of routed ones.
