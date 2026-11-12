"""The gate, reviewer routing, and `job init`."""

import json
import unittest

from sandbox import BIN, Sandbox


class GateTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.setup_factory(checks='echo "base=$FACTORY_BASE"\nexit ${FAKE_CHECKS_EXIT:-0}\n')
        self.job_id = self.s.start_job()
        self.s.build(self.job_id)
        self.s.job("advance", self.job_id, "gate")

    def tearDown(self):
        self.s.cleanup()

    def checks_md(self):
        return (self.s.job_dir(self.job_id) / "round-1" / "checks.md").read_text()

    def test_pass_records_the_commit_and_the_base(self):
        out = self.s.gate(self.job_id).stdout
        self.assertIn("GATE: PASS", out)
        head = self.s.git("rev-parse", "HEAD", cwd=self.s.worktree(self.job_id))
        self.assertTrue(self.checks_md().startswith(f"GATE: PASS\nCOMMIT: {head}\n"))
        self.assertIn("base=origin/main", self.checks_md())

    def test_failing_checks_fail_the_gate_and_send_the_job_back(self):
        res = self.s.gate(self.job_id, check=False, env={"FAKE_CHECKS_EXIT": "3"})
        self.assertEqual(res.returncode, 1)
        self.assertIn("failed with exit 3", self.checks_md())
        res = self.s.job("advance", self.job_id, "review", check=False)
        self.assertIn("the gate didn't pass", res.stderr)
        self.s.job("advance", self.job_id, "build")
        self.assertEqual(self.s.job_json(self.job_id)["round"], 2)

    def test_changing_a_protected_path_fails_the_gate(self):
        s = self.s
        s.git("add", "factory/checks.sh", "factory/config.json")
        s.git("commit", "-m", "Set up the factory")
        s.git("push", "origin", "main")
        wt = s.worktree(self.job_id)
        s.git("fetch", "origin", cwd=wt)
        s.git("merge", "--no-edit", "origin/main", cwd=wt)
        self.assertEqual(s.gate(self.job_id).returncode, 0, "an unchanged protected file passes")
        (wt / "factory" / "checks.sh").write_text("exit 0\n")
        s.git("commit", "-am", "Weaken checks", cwd=wt)
        res = s.gate(self.job_id, check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("protected paths changed: M factory/checks.sh", res.stdout)
        self.assertIn("- M factory/checks.sh", self.checks_md())

    def test_hook_ignores_prompts_without_a_job(self):
        transcript = self.s.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"message": {"content": "Just build something."}}) + "\n")
        event = json.dumps({"agent_transcript_path": str(transcript), "cwd": str(self.s.repo)})
        res = self.s.run("bash", "-c", f"echo '{event}' | {BIN / 'gate'} --hook", check=False)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_hook_blocks_a_failing_builder(self):
        header = self.s.job("header", self.job_id, "builder").stdout.strip()
        transcript = self.s.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"message": {"content": header + " Build round 1."}}) + "\n")
        event = json.dumps({"agent_transcript_path": str(transcript), "cwd": str(self.s.repo)})
        res = self.s.run("bash", "-c", f"echo '{event}' | {BIN / 'gate'} --hook",
                         check=False, env={"FAKE_CHECKS_EXIT": "1"})
        self.assertEqual(res.returncode, 2)
        self.assertIn("checks.sh fails in your worktree", res.stderr)


class RouteTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.setup_factory()
        self.job_id = self.s.job("create", "12").stdout.strip()

    def tearDown(self):
        self.s.cleanup()

    def test_surfaces_add_their_reviewers_in_order(self):
        self.s.intake(self.job_id, risk="medium", surfaces="ui, security")
        out = self.s.route(self.job_id).stdout
        self.assertIn("reviewers code, ux, ui, security", out)
        self.assertEqual(self.s.job_json(self.job_id)["agents"], {"reviewers": ["code", "ux", "ui", "security"]})

    def test_unknown_risk_is_refused(self):
        self.s.intake(self.job_id, risk="extreme")
        res = self.s.route(self.job_id, check=False)
        self.assertIn("risk 'extreme' isn't in config.json routing", res.stderr)

    def test_spec_needs_routing_first(self):
        self.s.intake(self.job_id)
        res = self.s.job("advance", self.job_id, "spec", check=False)
        self.assertIn("route the job first", res.stderr)


class InitTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()

    def tearDown(self):
        self.s.cleanup()

    def test_init_writes_files_once_and_ignores_runtime_paths(self):
        s = self.s
        out = s.job("init", "--no-labels").stdout
        self.assertIn("wrote     factory/config.json", out)
        config = json.loads((s.repo / "factory" / "config.json").read_text())
        self.assertEqual((config["base_branch"], config["skills"]["catalog"]), ("main", ".ai/skills/catalog.md"))
        (s.repo / "factory" / "checks.sh").write_text("exit 0\n")
        out = s.job("init", "--no-labels").stdout
        self.assertIn("kept      factory/checks.sh", out)
        self.assertEqual((s.repo / "factory" / "checks.sh").read_text(), "exit 0\n")
        gitignore = (s.repo / ".gitignore").read_text()
        self.assertEqual(gitignore.count("/factory/jobs/"), 1)
        self.assertEqual(s.git("check-ignore", "factory/jobs/x", ".worktrees/x").splitlines(),
                         ["factory/jobs/x", ".worktrees/x"])

    def test_init_creates_labels(self):
        self.s.job("init")
        self.assertEqual(sorted(self.s.gh_state()["labels"]), ["factory", "factory:needs-human", "factory:needs-info"])

    def test_init_reports_a_missing_catalog(self):
        (self.s.repo / ".ai" / "skills" / "catalog.md").unlink()
        res = self.s.job("init", "--no-labels", check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("MISSING   skill catalog", res.stdout)

    def test_commands_other_than_init_need_setup(self):
        res = self.s.job("queue", check=False)
        self.assertIn("run `/factory setup`", res.stderr)


if __name__ == "__main__":
    unittest.main()
