"""The factory's job state machine, end to end, against a real git repo and a fake gh."""

import json
import unittest

from sandbox import Sandbox


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.setup_factory()

    def tearDown(self):
        self.s.cleanup()

    def refused(self, *args, contains):
        res = self.s.job(*args, check=False)
        self.assertNotEqual(res.returncode, 0, res.stdout)
        self.assertIn(contains, res.stderr)

    def test_happy_path_merges_with_documentation(self):
        s = self.s
        job_id = s.start_job()
        self.assertEqual(job_id, "001-add-a-subtract-function")
        self.assertTrue(s.worktree(job_id).is_dir())
        s.to_review(job_id)
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["pr"], job["agents"]), ("review", 100, {"reviewers": ["code"]}))

        s.review(job_id)
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["outcome"], "reviews passed")
        s.document(job_id)
        s.job("advance", job_id, "approve")
        job = s.job_json(job_id)
        self.assertEqual(job["doc"], "Shipped")
        self.assertEqual(s.git("rev-parse", f"origin/{job['branch']}", cwd=s.worktree(job_id)),
                         s.git("rev-parse", "HEAD", cwd=s.worktree(job_id)), "docs commit pushed")

        s.write(job_id, "decision.md", "APPROVE\n\n## Why\nGood.\n")
        s.job("merge", job_id)
        job = s.job_json(job_id)
        self.assertEqual(job["stage"], "merged")
        self.assertEqual(s.gh_state()["prs"]["100"]["state"], "MERGED")
        self.assertFalse(s.worktree(job_id).exists())
        self.assertTrue((s.job_dir(job_id) / "round-1" / "merge-checks.md").exists())

    def test_header_names_the_job_folder_skills_and_port(self):
        job_id = self.s.start_job()
        header = self.s.job("header", job_id, "builder").stdout.strip()
        self.assertTrue(header.startswith(f"Job: {job_id}. Job folder: {self.s.job_dir(job_id)}/."))
        self.assertIn(f"Skill catalog: {self.s.repo}/.ai/skills/catalog.md.", header)
        self.assertIn("references/skills.md.", header)
        self.assertTrue(header.endswith("Port: 7110."), header)
        self.assertTrue(self.s.job("header", job_id, "ui").stdout.strip().endswith("Port: 7112."))
        self.refused("header", job_id, "approver", contains="no port")

    def test_create_refuses_without_a_skill_catalog(self):
        (self.s.repo / ".ai" / "skills" / "catalog.md").unlink()
        self.refused("create", "12", contains="skill catalog")

    def test_create_refuses_unlabeled_issue(self):
        self.s.add_issue(13, "Unlabeled", [])
        self.refused("create", "13", contains="isn't labeled factory")

    def test_spec_with_unreadable_skill_is_refused(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id)
        s.route(job_id)
        s.job("advance", job_id, "spec")
        s.spec(job_id, skill_path="/nowhere/SKILL.md")
        self.refused("advance", job_id, "build", contains="can't be read: quality/review (/nowhere/SKILL.md)")

    def test_blocked_spec_goes_to_a_person(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id)
        s.route(job_id)
        s.job("advance", job_id, "spec")
        s.spec(job_id, status="BLOCKED")
        self.refused("advance", job_id, "build", contains="BLOCKED, not READY")
        s.job("advance", job_id, "needs-human")
        self.assertIn("nest/actions", (s.job_dir(job_id) / "decision.md").read_text())
        self.assertIn("factory:needs-human", s.gh_state()["issues"]["12"]["labels"])

    def test_feedback_on_a_blocked_spec_goes_back_to_the_spec_writer(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id)
        s.route(job_id)
        s.job("advance", job_id, "spec")
        s.spec(job_id, status="BLOCKED")
        s.job("advance", job_id, "needs-human")
        self.refused("advance", job_id, "build", contains="use `job feedback`")
        out = s.job("feedback", job_id, input="I installed nest/actions.\n").stdout
        self.assertIn("feedback-1.md, back to the spec-writer", out)
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["round"]), ("spec", 0))
        self.assertNotIn("factory:needs-human", s.gh_state()["issues"]["12"]["labels"])
        s.spec(job_id)
        s.job("advance", job_id, "build")
        self.assertEqual(s.job_json(job_id)["round"], 1)

    def test_builder_may_not_touch_documentation(self):
        s = self.s
        job_id = s.start_job()
        s.build(job_id, path="Documentation/Subtract.md")
        self.refused("advance", job_id, "gate", contains="the builder changed Documentation/")

    def test_unpushed_build_is_refused(self):
        s = self.s
        job_id = s.start_job()
        s.commit(job_id, "subtract.txt", "subtract\n", push=False)
        s.write(job_id, "build.md", "STATUS: READY\n")
        self.refused("advance", job_id, "gate", contains="isn't pushed")

    def test_reviewer_that_changes_the_branch_is_refused(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id)
        s.commit(job_id, "extra.txt", "x\n", push=False)
        self.refused("advance", job_id, "document", contains="a reviewer changed the branch")

    def test_documenter_must_stay_in_documentation(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id)
        s.job("advance", job_id, "document")
        self.refused("advance", job_id, "approve", contains="the documenter made no commit")
        s.document(job_id, extra="stray.txt")
        self.refused("advance", job_id, "approve", contains="outside Documentation/: stray.txt")

    def test_changes_on_the_last_round_are_documented_not_shipped(self):
        s = self.s
        path = s.repo / "factory" / "config.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), "max_rounds": 1}))
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id, verdict="CHANGES")
        self.refused("advance", job_id, "build", contains="round 1 of 1: go to document")
        s.job("advance", job_id, "document")
        job = s.job_json(job_id)
        self.assertEqual(job["outcome"], "not shipped, build rounds ran out")
        s.document(job_id, status="Shipped")
        self.refused("advance", job_id, "approve", contains="go to needs-human")
        self.refused("advance", job_id, "needs-human", contains="says Shipped, but the job wasn't shipped")
        s.git("reset", "--hard", "HEAD~1", cwd=s.worktree(job_id))
        s.document(job_id, status="Not shipped")
        s.job("advance", job_id, "needs-human")
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["doc"]), ("needs-human", "Not shipped"))
        self.assertIn("Build rounds ran out", (s.job_dir(job_id) / "decision.md").read_text())
        pr = s.gh_state()["prs"]["100"]
        self.assertFalse(pr["isDraft"])
        self.assertIn("Documentation on the branch: Not shipped.", pr["comments"][-1]["body"])

    def test_changes_before_the_last_round_go_back_to_the_builder(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id, verdict="CHANGES")
        self.refused("advance", job_id, "document", contains="go to build")
        s.job("advance", job_id, "build")
        self.assertEqual(s.job_json(job_id)["round"], 2)

    def test_blocked_builder_is_documented_then_escalated(self):
        s = self.s
        job_id = s.start_job()
        s.build(job_id, status="BLOCKED")
        self.refused("advance", job_id, "gate", contains="not STATUS: READY")
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["outcome"], "not shipped, the builder is blocked")
        s.document(job_id, status="Not shipped")
        s.job("advance", job_id, "needs-human")
        self.assertIn("The spec contradicts itself.", (s.job_dir(job_id) / "decision.md").read_text())
        comments = s.gh_state()["issues"]["12"]["comments"]
        self.assertIn("needs a human", comments[-1]["body"])

    def test_feedback_starts_a_new_round(self):
        s = self.s
        job_id = s.start_job()
        s.build(job_id, status="BLOCKED")
        s.job("advance", job_id, "document")
        s.document(job_id, status="Not shipped")
        s.job("advance", job_id, "needs-human")
        out = s.job("feedback", job_id, input="Use a plain function.\n").stdout
        self.assertIn("feedback-1.md, round 2", out)
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["round_limit"]), ("build", 4))

    def test_approver_that_changes_the_branch_is_refused(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id)
        s.job("advance", job_id, "document")
        s.document(job_id)
        s.job("advance", job_id, "approve")
        s.commit(job_id, "late.txt", "x\n", push=False)
        s.write(job_id, "decision.md", "APPROVE\n")
        self.refused("merge", job_id, contains="the approver changed the branch")

    def test_queue_lists_new_issues_within_concurrency(self):
        self.s.add_issue(13, "Add multiply", ["factory"])
        path = self.s.repo / "factory" / "config.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), "concurrency": 1}))
        rows = [line.split("\t") for line in self.s.job("queue").stdout.splitlines()]
        self.assertEqual([r[:2] for r in rows], [["new", "12"], ["hold", "13"]])


if __name__ == "__main__":
    unittest.main()
