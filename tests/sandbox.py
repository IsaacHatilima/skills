"""A throwaway project for the factory's scripts: a git repo with a bare origin,
a fake `gh` on PATH, an installed skill catalog, and helpers that play each agent."""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "agents" / "factory" / "bin"
FAKE_GH = Path(__file__).resolve().parent / "fake_gh.py"


class Sandbox:
    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="factory-test-")).resolve()
        self.repo = self.tmp / "repo"
        self.state_file = self.tmp / "gh.json"
        self.env = self._env()
        self._init_git()
        self._init_gh()
        self._init_skills()

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- setup -------------------------------------------------------------

    def _env(self):
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(f"#!/bin/sh\nexec python3 {FAKE_GH} \"$@\"\n")
        (bin_dir / "gh").chmod(0o755)
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.test\n"
                             "[commit]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n")
        return {
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "HOME": str(self.tmp / "home"),
            "FAKE_GH_STATE": str(self.state_file),
            "CLAUDE_CONFIG_DIR": str(self.tmp / "claude"),
            "CODEX_HOME": str(self.tmp / "codex"),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
        }

    def _init_git(self):
        (self.tmp / "home").mkdir()
        origin = self.tmp / "origin.git"
        self.run("git", "init", "--bare", "-b", "main", str(origin), cwd=self.tmp)
        self.run("git", "clone", str(origin), str(self.repo), cwd=self.tmp)
        (self.repo / "README.md").write_text("# Calculator\n")
        (self.repo / "src.txt").write_text("add\n")
        self.git("add", "README.md", "src.txt")
        self.git("commit", "-m", "Initial commit")
        self.git("push", "-u", "origin", "main")
        self.git("remote", "set-head", "origin", "main")

    def _init_gh(self):
        state = {"calls": [], "labels": {}, "prs": {}, "issues": {}}
        self.state_file.write_text(json.dumps(state))
        self.add_issue(12, "Add a subtract function", ["factory"])

    def _init_skills(self):
        skills = self.repo / ".ai" / "skills"
        (skills / "quality-review").mkdir(parents=True)
        (skills / "catalog.md").write_text("# Shared skill catalog\n")
        self.skill_path = skills / "quality-review" / "SKILL.md"
        self.skill_path.write_text("---\nname: quality-review\ndescription: Review.\n---\n")

    # ---- running things ----------------------------------------------------

    def run(self, *cmd, cwd=None, check=True, input=None, env=None):
        res = subprocess.run(cmd, cwd=cwd or self.repo, capture_output=True, text=True,
                             input=input, env={**os.environ, **self.env, **(env or {})})
        if check and res.returncode != 0:
            raise AssertionError(f"{' '.join(map(str, cmd))} failed ({res.returncode}):\n{res.stdout}{res.stderr}")
        return res

    def git(self, *args, cwd=None):
        return self.run("git", *args, cwd=cwd).stdout.strip()

    def job(self, *args, check=True, input=None, env=None):
        return self.run(str(BIN / "job"), *args, check=check, input=input, env=env)

    def gate(self, *args, check=True, env=None):
        return self.run(str(BIN / "gate"), *args, check=check, env=env)

    def route(self, *args, check=True):
        return self.run(str(BIN / "route"), *args, check=check)

    # ---- GitHub and job state ----------------------------------------------

    def gh_state(self):
        return json.loads(self.state_file.read_text())

    def add_issue(self, number, title, labels):
        state = self.gh_state()
        state["issues"][str(number)] = {
            "title": title, "body": "Please add it.", "author": "alice", "labels": labels,
            "state": "OPEN", "url": f"https://example.test/issues/{number}", "comments": []}
        self.state_file.write_text(json.dumps(state))

    def setup_factory(self, checks="exit ${FAKE_CHECKS_EXIT:-0}\n", **config):
        self.job("init", "--no-labels")
        path = self.repo / "factory" / "config.json"
        merged = {**json.loads(path.read_text()), **config}
        path.write_text(json.dumps(merged, indent=2))
        (self.repo / "factory" / "checks.sh").write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + checks)

    def job_json(self, job_id):
        return json.loads((self.repo / "factory" / "jobs" / job_id / "job.json").read_text())

    def job_dir(self, job_id):
        return self.repo / "factory" / "jobs" / job_id

    def worktree(self, job_id):
        return Path(self.job_json(job_id)["worktree"])

    # ---- playing the agents ------------------------------------------------

    def write(self, job_id, name, text, append=""):
        path = self.job_dir(job_id) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip() + append)

    def intake(self, job_id, decision="ACCEPT", risk="low", surfaces="none"):
        self.write(job_id, "intake.md", f"""
            DECISION: {decision}
            RISK: {risk}
            SURFACES: {surfaces}
            RESCOPED: no

            ## Summary
            - Accepted.

            ## Scope
            Add subtract.
            """)

    def spec(self, job_id, status="READY", skill_path=None):
        path = skill_path or self.skill_path
        blocked = "\n## Blocked\nThe nest/actions skill isn't installed.\n" if status == "BLOCKED" else ""
        self.write(job_id, "spec.md", f"""
            # Subtract

            > Issue #12: Add a subtract function

            ## Summary
            - Spec.

            ## Project
            Shape: single project.

            ## Skills
            Status: {status}

            | Skill | Package or scope | Roles | Resolved path | Why |
            |---|---|---|---|---|
            | quality/review | . | reviewer-code | {path} | review |

            ## Acceptance criteria
            1. subtract works: run it.

            ## Documentation
            Doc: `Documentation/Subtract.md`
            Feature name: Subtract
            Expected: Users can subtract.
            """, append=blocked)

    def commit(self, job_id, path, text, message="Add subtract", push=True):
        wt = self.worktree(job_id)
        (wt / path).parent.mkdir(parents=True, exist_ok=True)
        (wt / path).write_text(text)
        self.git("add", path, cwd=wt)
        self.git("commit", "-m", message, cwd=wt)
        if push:
            self.git("push", "-u", "origin", self.job_json(job_id)["branch"], cwd=wt)

    def build(self, job_id, status="READY", path="subtract.txt", open_pr=True):
        if status == "READY":
            self.commit(job_id, path, "subtract\n")
            branch = self.job_json(job_id)["branch"]
            if open_pr and self.run("gh", "pr", "view", branch, check=False).returncode != 0:
                self.run("gh", "pr", "create", "--draft", "--base", "main", "--head", branch,
                         "--title", "Subtract", "--body", "Closes #12")
        blocked = "\n## Blocked\nThe spec contradicts itself.\n" if status == "BLOCKED" else ""
        self.write(job_id, "build.md", f"STATUS: {status}\n\n# Build: Subtract\n" + blocked)

    def review(self, job_id, verdict="PASS", lens="code"):
        n = self.job_json(job_id)["round"]
        self.write(job_id, f"round-{n}/review-{lens}.md", f"VERDICT: {verdict}\n\n## Findings\nNone.\n")

    def document(self, job_id, status="Shipped", extra=None):
        wt = self.worktree(job_id)
        (wt / "Documentation").mkdir(exist_ok=True)
        (wt / "Documentation" / "Subtract.md").write_text(f"# Subtract ({status})\n\nCreated: 12.11.2026\n")
        (wt / "Documentation" / "index.md").write_text("# Documentation\n")
        paths = ["Documentation/Subtract.md", "Documentation/index.md"]
        if extra:
            (wt / extra).write_text("oops\n")
            paths.append(extra)
        self.git("add", *paths, cwd=wt)
        self.git("commit", "-m", "docs: document Subtract", cwd=wt)

    def start_job(self, risk="low", surfaces="none"):
        """Create a job for issue #12 and take it to the build stage."""
        job_id = self.job("create", "12").stdout.strip()
        self.intake(job_id, risk=risk, surfaces=surfaces)
        self.route(job_id)
        self.job("advance", job_id, "spec")
        self.spec(job_id)
        self.job("advance", job_id, "build")
        return job_id

    def to_review(self, job_id):
        self.build(job_id)
        self.job("advance", job_id, "gate")
        self.gate(job_id)
        self.job("advance", job_id, "review")
