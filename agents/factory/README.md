# Factory

Factory turns GitHub issues into reviewed, documented pull requests. Label an issue `factory`, run `/factory run`, and agents decide whether it's worth building, write a spec with the skills each role must read, build it, test it with the project's own checks, review it, document it, and open a PR that closes the issue. The approver merges what it's sure of and hands a person the rest.

```text
/factory setup        prepare a project once: config, checks, labels, AGENTS.md
/factory run          drain the queue: every open `factory` issue, `concurrency` at a time; also resumes
/factory run <n>      run one issue now
/factory grill <n>    grill you about issue #<n> and record the decisions before it runs
/factory <anything>   ask about jobs, give feedback, reject a job, or file a new feature
```

Claude Code runs it as `/factory`. Codex has no per-skill slash commands, so there it is `$factory` (or pick it from `/skills`). [AGENT.md](AGENT.md) is the orchestrator; [SKILL.md](SKILL.md) is the thin command adapter both hosts load.

## The loop

```text
issues labeled `factory`
        │
        ▼
intake ──── NEEDS-INFO → asks the author on the issue, waits for a reply
        │   REJECT     → says why on the issue, removes the label
        ▼ ACCEPT, maybe rescoped; rates risk + surfaces
route (script)     picks the reviewers from config.json
        ▼
spec-writer → spec.md: packages, stacks, selected skills, contract, permissions, criteria
        ▼            BLOCKED (missing skill or prerequisite) → a person
builder → commits, pushes, opens a draft PR "Closes #n"
        ▼            ▲
gate (script) ─FAIL──┤  factory/checks.sh; no reviewer runs on a failing build
        ▼ PASS       │
reviewers ─CHANGES───┘  code, + ux & ui on UI changes, + security on security changes
        ▼ all PASS, or the build is blocked or out of rounds
documenter → Documentation/<Feature>.md and Documentation/index.md, one commit on the branch
        ▼ shipped                                 not shipped → a person
approver ── APPROVE  → sync with the base, gate again, gh pr merge
         └─ ESCALATE → PR ready for a person, issue labeled factory:needs-human
```

Before a job starts, the orchestrator can grill you with the `planning/grilling` skill (adapted from Matt Pocock's `grill-me`): rounds of questions, each with a recommended answer, until no decision is left assumed. It does this for a vague `/factory <feature>` request and for `/factory grill <n>`, then writes the result into the issue as **Decisions** that intake and the spec-writer build on. Agents inside a job never ask; intake's NEEDS-INFO questions to an issue's author use the same one-round, recommended-answer format.

One session orchestrates every job, `concurrency` at a time (default 3). Each job gets its own worktree at `.worktrees/<job-id>` on `factory/<job-id>`. All state lives in `factory/jobs/`, so if the session dies, `/factory run` picks every job back up. A person approves an escalated job by merging its PR, or sends it back with `/factory <feedback>`.

## Agents

Each role is one file here, with the model, reasoning effort and tools for both hosts in its frontmatter. The installer renders them into `.claude/agents/<name>.md` and `.codex/agents/<name>.toml`; the orchestrator never overrides a model.

| Role | Writes | Claude Code | Codex | Runs |
|---|---|---|---|---|
| [intake](intake.md) | `intake.md` | fable, high | gpt-6-astra, high | every issue |
| [spec-writer](spec-writer.md) | `spec.md` | opus, high | gpt-6-astra, high | every accepted job |
| [builder](builder.md) | code, PR, `build.md` | opus, high | gpt-6-sol, high | every round |
| [reviewer-code](reviewer-code.md) | `review-code.md` | sonnet, high | gpt-6-sol, high | every round that passes the gate |
| [reviewer-security](reviewer-security.md) | `review-security.md` | opus, high | gpt-6-astra, high | `security` surface |
| [reviewer-ux](reviewer-ux.md) | `review-ux.md` | sonnet, medium | gpt-6-luna, medium | `ui` surface |
| [reviewer-ui](reviewer-ui.md) | `review-ui.md` | sonnet, medium | gpt-6-luna, medium | `ui` surface |
| [documenter](documenter.md) | `Documentation/` commit | sonnet, high | gpt-6-sol, high | once the build ends |
| [approver](approver.md) | `decision.md` | opus, high | gpt-6-astra, high | shipped jobs |

Source frontmatter keys are `name`, `description`, `claude-model`, `claude-tools`, `claude-effort`, `codex-model` and `codex-reasoning-effort`. The builder also has `claude-stop-hook`, which the installer turns into a Claude Code `Stop` hook that runs the checks before the builder finishes, as a nudge; the gate still decides.

## Scripts

The deterministic stages are Python 3.10+ standard library, in `bin/`:

- `bin/job` is the only writer of `job.json`. `advance` refuses illegal moves and checks each agent stayed in its lane: the builder pushed, opened the PR and left `Documentation/` alone; reviewers and the approver changed nothing; the documenter committed only under `Documentation/` and its page's status matches the outcome; every skill the spec selected is still readable. It also owns the GitHub side effects of each move, the merge, `init`, and the prompt header (`job header <id> [builder|ux|ui]`).
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
| `.claude/skills/factory/SKILL.md`, `.claude/agents/*.md` | Claude Code: the `/factory` pointer and the nine agents |
| `.agents/skills/factory/SKILL.md`, `.codex/agents/*.toml` | Codex: the `$factory` pointer and the nine agents |
| A block in `AGENTS.md` and `CLAUDE.md` | where every agent finds the skills |

Every bundle in `bundles.json` that lists the `factory` workflow installs it, with the skills its roles select. The installer never overwrites a file that differs without `--force`, and writes nothing when any would be.

Then, in each project, run `/factory setup` (`$factory setup` in Codex) once. It needs a GitHub `origin`, an authenticated `gh` that can push and manage labels, and `python3`. It writes `factory/config.json`, `factory/checks.sh` and `factory/dashboard.html`, ignores `factory/jobs/` and `.worktrees/`, creates the labels, fills `checks.sh` with the project's real lint, typecheck, test and build commands, adds a Software factory section to `AGENTS.md` (project purpose, security hot spots, design system, users, what a person must always see), verifies, and commits on the current branch. Push that commit before the first run: jobs branch from `origin/<base>`.

## Dashboard

```bash
cd factory && python3 -m http.server
```

Open <http://localhost:8000/dashboard.html>. Each job is a card with its issue and PR, gate and review chips per round, its documentation status, risk, cost and time. Click a card to read every file the job wrote. Cost is the API-equivalent price of the job's Claude Code agents, read from Claude Code's transcripts and priced with `prices_usd_per_mtok`; Codex runs aren't counted.

## Cost and safety

- It opens and merges real PRs. Start with `concurrency: 1` and read every PR until you trust it.
- Intake runs on Fable once per issue. Depending on your plan, Fable can bill to usage credits rather than the plan's included usage.
- Only issues labeled `factory` run, and only people with triage or write access can add labels. Issue text reaches the agents as quoted data, never as their instructions.
- The factory pushes only `factory/*` branches, merges only through `gh pr merge`, and never deploys.

## Tests

```bash
python3 -m unittest discover -s tests
```

The tests run the scripts against a throwaway git repository with a bare origin and a fake `gh`, through every stage and refusal, and install into temporary projects and homes.

## License and credit

The workflow, scripts and dashboard are adapted from the [ZazenCodes software factory v2](https://github.com/zazencodes/zazencodes-season-3/tree/main/src/software-factory-claude-code-v2) and are licensed under the [GNU GPLv3](LICENSE), like the original. This version adds the documenter stage, skill selection and checking, the scaffold strategy, a project-or-user installer for Claude Code and Codex, and per-agent models in place of routed ones.
