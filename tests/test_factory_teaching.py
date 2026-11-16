"""Confirmed review outcomes become bounded, resumable knowledge-writing work."""

import json
import unittest

from sandbox import Sandbox


class TeachingTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.setup_factory()

    def tearDown(self):
        self.s.cleanup()

    def refused(self, job_id, stage):
        result = self.s.job("advance", job_id, stage, check=False)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def review(self, job_id, *, verdict="PASS", lens="code", findings="None.", resolutions=None):
        n = self.s.job_json(job_id)["round"]
        self.s.write(job_id, f"round-{n}/review-{lens}.md",
                     f"VERDICT: {verdict}\n\n## Findings\n{findings}\n")
        if resolutions is not None:
            self.s.write(job_id, f"round-{n}/resolutions-{lens}.json", json.dumps(resolutions) + "\n")

    def second_review(self, *, verdict="PASS", surfaces="none", write_all=True):
        s = self.s
        job_id = s.start_job(surfaces=surfaces)
        s.to_review(job_id)
        self.review(job_id, verdict="CHANGES", findings=
                    "1. [code-r1-1] A previous session's login response restores stale private state.\n")
        for lens in s.job_json(job_id)["agents"]["reviewers"]:
            if lens != "code":
                self.review(job_id, lens=lens)
        s.job("advance", job_id, "build")
        s.commit(job_id, "subtract.txt", "response fenced by session generation\n")
        s.write(job_id, "build.md", "STATUS: READY\n\n## Log\nFixed code-r1-1 by fencing the response.\n")
        s.job("advance", job_id, "gate")
        s.gate(job_id)
        s.job("advance", job_id, "review")
        commit = s.git("rev-parse", "HEAD", cwd=s.worktree(job_id))
        resolution = {"finding": "code-r1-1", "outcome": "fixed", "commit": commit,
                      "evidence": "The session-switch regression passes and the callback rejects old receipts.",
                      "limits": "Focused test and source evidence; no browser or live-service claim."}
        findings = "1. [code-r2-1] A different input case still fails.\n" if verdict == "CHANGES" else "None."
        self.review(job_id, verdict=verdict, findings=findings, resolutions=[resolution])
        if write_all:
            for lens in s.job_json(job_id)["agents"]["reviewers"]:
                if lens != "code":
                    self.review(job_id, lens=lens)
        return job_id, commit, resolution

    def report(self, job_id, commit, *, status="NO_CHANGE", findings="code-r1-1", lessons="none"):
        n = self.s.job_json(job_id)["round"]
        self.s.write(job_id, f"round-{n}/teach.md", f"""
            STATUS: {status}
            COMMIT: {commit}
            FINDINGS: {findings}
            LESSONS: {lessons}

            ## Summary
            Processed the confirmed outcome at the reviewed commit.

            ## Reasons
            code-r1-1 was checked. A no-change result means no reusable addition was needed.
            """)

    def record_lesson(self, job_id, reviewed_commit, *, root="Knowledge"):
        s = self.s
        wt = s.worktree(job_id)
        lesson = f"{root}/hooks-and-state/ignore-previous-session-responses.md"
        path = wt / lesson
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"""# Ignore responses from previous sessions

ID: ignore-previous-session-responses
Category: Hooks and State
Tags: authentication, async-state, sessions, forms
Verified: 2026-11-16
Status: verified-on-branch

## Use when
Login or registration requests can finish after the active session changes.

## Problem
A response from an old session restored private state after a new sign-in.

## Cause
The callback trusted the session that existed when the request began.

## Solution
Capture the session generation and refuse receipts from an older generation.

## Prevention
Cover an account switch while the request is pending in tests/session-response.test.ts.

## Evidence
Repository: https://example.test/calculator/repository
PR: https://example.test/pr/100
Finding: code-r1-1, from review-code in round 1.
Fix commit: {reviewed_commit}
Reviewed commit: {reviewed_commit}
The focused session-switch regression passes. Source: subtract.txt.

## Limits
Verified on this branch. The mocked regression and source inspection do not prove browser or deployed behaviour.
""")
        (wt / root / "index.md").write_text("""# Knowledge

## Hooks and State

| Lesson | Use when | Tags |
|---|---|---|
| [Ignore responses from previous sessions](hooks-and-state/ignore-previous-session-responses.md) | Login or registration requests can finish after session changes. | authentication, async-state, sessions, forms |
""")
        s.git("add", f"{root}/index.md", lesson, cwd=wt)
        s.git("commit", "-m", "docs: record verified session-response lesson", cwd=wt)
        self.report(job_id, reviewed_commit, status="RECORDED", lessons=lesson)
        return lesson, s.git("rev-parse", "HEAD", cwd=wt)

    def seed_prior_lesson(self, *, relative="database-and-queries/stable-query-order.md",
                          title="Keep pagination order stable", category="Database and Queries"):
        s = self.s
        lesson = f"Knowledge/{relative}"
        path = s.repo / lesson
        path.parent.mkdir(parents=True, exist_ok=True)
        original = s.git("rev-parse", "HEAD")
        path.write_text(f"""# {title}

ID: prior-reviewed-lesson
Category: {category}
Tags: historical, verified
Verified: 2026-11-15
Status: verified-on-branch

## Use when
Working on the same established boundary described in this prior lesson.

## Problem
An earlier implementation violated that boundary.

## Cause
It relied on an assumption the regression case invalidated.

## Solution
Use the previously reviewed enforcement point for the stated case.

## Prevention
Keep the focused regression test when changing that boundary.

## Evidence
Repository: https://example.test/calculator/repository
PR: https://example.test/pr/99
Reviewed commit: {original}
The earlier focused regression and source review established this limited behaviour.

## Limits
Historical branch verification, not a claim about deployment or every later implementation.
""")
        (s.repo / "Knowledge/index.md").write_text(f"""# Knowledge

## {category}

| Lesson | Use when | Tags |
|---|---|---|
| [{title}]({relative}) | Reusing the earlier verified boundary. | historical, verified |
""")
        s.git("add", "Knowledge/index.md", lesson)
        s.git("commit", "-m", "docs: seed prior reviewed lesson fixture")
        s.git("push", "origin", "main")
        return lesson

    def test_no_confirmed_fix_keeps_the_existing_review_path(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        self.review(job_id, resolutions=[])
        self.refused(job_id, "teach")
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["outcome"], "reviews passed")
        self.assertFalse((s.worktree(job_id) / "Knowledge").exists())

    def test_pass_or_omission_does_not_infer_a_resolved_finding(self):
        job_id, _, _ = self.second_review()
        (self.s.job_dir(job_id) / "round-2/resolutions-code.json").unlink()
        self.s.job("advance", job_id, "document")
        self.assertEqual(self.s.job_json(job_id)["stage"], "document")
        self.assertFalse((self.s.job_dir(job_id) / "round-2/teach.md").exists())

    def test_confirmed_fix_forces_one_batch_before_the_next_build(self):
        s = self.s
        job_id, reviewed, _ = self.second_review(verdict="CHANGES")
        receipt = (s.job_dir(job_id) / "round-2/checks.md").read_bytes()
        self.refused(job_id, "build")
        s.job("advance", job_id, "teach")
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["round"], job["teaching"]["next_stage"]), ("teach", 2, "build"))
        self.assertEqual(job["teaching"]["reviewed_commit"], reviewed)
        self.assertIn(job_id, s.job("queue").stdout)
        self.assertIn("Knowledge", s.job("header", job_id).stdout)
        lesson, taught = self.record_lesson(job_id, reviewed)
        s.job("advance", job_id, "build")
        job = s.job_json(job_id)
        self.assertEqual((job["stage"], job["round"], job["round_base"]), ("build", 3, taught))
        self.assertEqual((s.job_dir(job_id) / "round-2/checks.md").read_bytes(), receipt)
        self.assertIn("code-r1-1", (s.worktree(job_id) / lesson).read_text())
        self.assertNotEqual(taught, reviewed)

    def test_one_round_batches_multiple_confirmed_fixes(self):
        s = self.s
        job_id, reviewed, resolution = self.second_review()
        original = s.job_dir(job_id) / "round-1/review-code.md"
        original.write_text(original.read_text() + "2. [code-r1-2] A duplicate request could publish twice.\n")
        self.review(job_id, resolutions=[resolution, {**resolution, "finding": "code-r1-2"}])
        s.job("advance", job_id, "teach")
        self.assertEqual(len(s.job_json(job_id)["teaching"]["resolutions"]), 2)
        self.report(job_id, reviewed, findings="code-r1-1, code-r1-2")
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["round"], 2)
        self.assertEqual(len(list(s.job_dir(job_id).glob("round-*/teach.md"))), 1)

    def test_no_change_result_is_resumable_without_new_commit_or_round(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        self.report(job_id, reviewed)
        before = s.job_json(job_id)["round"]
        self.assertIn("teach", s.job("queue").stdout)
        s.job("advance", job_id, "document")
        job = s.job_json(job_id)
        self.assertEqual((job["round"], job["doc_base"]), (before, reviewed))
        self.assertEqual(s.git("rev-parse", "HEAD", cwd=s.worktree(job_id)), reviewed)
        result = s.job("advance", job_id, "document", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(list(s.job_dir(job_id).glob("round-*/teach.md"))), 1)

    def test_last_round_teaches_confirmed_fixes_before_not_shipped_documentation(self):
        self.s.setup_factory(max_rounds=2)
        job_id, reviewed, _ = self.second_review(verdict="CHANGES")
        self.s.job("advance", job_id, "teach")
        self.assertEqual(self.s.job_json(job_id)["teaching"]["next_stage"], "document")
        self.report(job_id, reviewed)
        self.s.job("advance", job_id, "document")
        job = self.s.job_json(job_id)
        self.assertEqual((job["round"], job["round_limit"]), (2, 2))
        self.assertEqual(job["outcome"], "not shipped, build rounds ran out")

    def test_teaching_waits_for_all_reviewers(self):
        job_id, _, _ = self.second_review(surfaces="ui", write_all=False)
        self.refused(job_id, "teach")
        self.assertEqual(self.s.job_json(job_id)["stage"], "review")

    def test_teacher_cannot_hide_a_reviewer_commit_change(self):
        job_id, _, _ = self.second_review()
        self.s.commit(job_id, "unexpected.txt", "reviewer edit\n", push=False)
        self.refused(job_id, "teach")
        self.assertEqual(self.s.job_json(job_id)["stage"], "review")

    def test_only_explicit_supported_prior_finding_resolutions_are_accepted(self):
        s = self.s
        job_id, _, resolution = self.second_review()
        invalid = [
            {**resolution, "commit": "0" * 40},
            {**resolution, "finding": "security-r1-1"},
            {**resolution, "finding": "code-r1-99"},
            {**resolution, "finding": "code-r2-1"},
            {**resolution, "evidence": ""},
            {**resolution, "limits": ""},
            {**resolution, "outcome": "unresolved"},
        ]
        for record in invalid:
            with self.subTest(record=record):
                self.review(job_id, resolutions=[record])
                self.refused(job_id, "teach")
                self.assertEqual(s.job_json(job_id)["stage"], "review")
        s.write(job_id, "round-2/resolutions-code.json", "not json\n")
        self.refused(job_id, "teach")

    def test_original_finding_must_have_been_a_changes_report(self):
        job_id, _, _ = self.second_review()
        path = self.s.job_dir(job_id) / "round-1/review-code.md"
        path.write_text(path.read_text().replace("VERDICT: CHANGES", "VERDICT: PASS", 1))
        self.refused(job_id, "teach")

    def test_missing_learning_skill_cannot_start_the_teacher(self):
        job_id, _, _ = self.second_review()
        self.s.learning_skill_path.unlink()
        self.refused(job_id, "teach")
        self.assertEqual(self.s.job_json(job_id)["stage"], "review")

    def test_teacher_cannot_change_application_code_or_feature_documentation(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        _, taught = self.record_lesson(job_id, reviewed)
        for name in ("src.txt", "Documentation/Unexpected.md"):
            with self.subTest(path=name):
                path = s.worktree(job_id) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("outside teacher ownership\n")
                s.git("add", name, cwd=s.worktree(job_id))
                s.git("commit", "--amend", "--no-edit", cwd=s.worktree(job_id))
                self.refused(job_id, "document")
                self.assertEqual(s.job_json(job_id)["stage"], "teach")
                s.git("reset", "--hard", taught, cwd=s.worktree(job_id))

    def test_teacher_cannot_modify_prior_agent_reports(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        self.report(job_id, reviewed)
        (s.job_dir(job_id) / "build.md").write_text("STATUS: READY\n\nTeacher rewrote the evidence.\n")
        self.refused(job_id, "document")
        self.assertEqual(s.job_json(job_id)["stage"], "teach")

    def test_symlink_lesson_is_refused(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        lesson, _ = self.record_lesson(job_id, reviewed)
        path = s.worktree(job_id) / lesson
        path.unlink()
        external = s.tmp / "external-lesson.md"
        external.write_text("external content\n")
        path.symlink_to(external)
        s.git("add", lesson, cwd=s.worktree(job_id))
        s.git("commit", "--amend", "--no-edit", cwd=s.worktree(job_id))
        self.refused(job_id, "document")

    def test_builder_cannot_write_the_teachers_knowledge_files(self):
        s = self.s
        job_id = s.start_job()
        s.build(job_id, path="Knowledge/index.md")
        self.refused(job_id, "gate")
        self.assertEqual(s.job_json(job_id)["stage"], "build")

    def test_processed_finding_does_not_schedule_another_teacher_batch(self):
        s = self.s
        job_id, reviewed, resolution = self.second_review(verdict="CHANGES")
        s.job("advance", job_id, "teach")
        self.report(job_id, reviewed)
        s.job("advance", job_id, "build")
        s.commit(job_id, "subtract.txt", "all input cases now work\n")
        s.write(job_id, "build.md", "STATUS: READY\n\n## Log\nFixed code-r2-1.\n")
        s.job("advance", job_id, "gate")
        s.gate(job_id)
        s.job("advance", job_id, "review")
        current = s.git("rev-parse", "HEAD", cwd=s.worktree(job_id))
        self.review(job_id, resolutions=[{**resolution, "commit": current}])
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["taught_findings"], ["code-r1-1"])
        self.assertFalse((s.job_dir(job_id) / "round-3/teach.md").exists())

    def test_confirmed_dismissal_is_a_valid_outcome_without_claiming_a_repair(self):
        s = self.s
        job_id, reviewed, resolution = self.second_review()
        self.review(job_id, resolutions=[{**resolution, "outcome": "dismissed",
                                          "evidence": "The existing server boundary already rejects this case."}])
        s.job("advance", job_id, "teach")
        self.assertEqual(s.job_json(job_id)["teaching"]["resolutions"][0]["outcome"], "dismissed")
        self.report(job_id, reviewed)
        s.job("advance", job_id, "document")
        self.assertFalse((s.worktree(job_id) / "Knowledge").exists())

    def test_index_must_link_a_recorded_lesson_that_exists(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        self.record_lesson(job_id, reviewed)
        index = s.worktree(job_id) / "Knowledge/index.md"
        index.write_text(index.read_text().replace("ignore-previous-session-responses.md", "missing.md"))
        s.git("add", "Knowledge/index.md", cwd=s.worktree(job_id))
        s.git("commit", "--amend", "--no-edit", cwd=s.worktree(job_id))
        self.refused(job_id, "document")

    def test_teacher_index_must_preserve_unrelated_prior_entries(self):
        s = self.s
        prior = self.seed_prior_lesson()
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        self.record_lesson(job_id, reviewed)
        # The ordinary new-lesson fixture deliberately writes only its own row.
        self.assertTrue((s.worktree(job_id) / prior).is_file())
        self.assertNotIn("stable-query-order.md", (s.worktree(job_id) / "Knowledge/index.md").read_text())
        self.refused(job_id, "document")
        self.assertEqual(s.job_json(job_id)["stage"], "teach")

    def test_teacher_can_supersede_a_prior_lesson_with_a_linked_replacement(self):
        s = self.s
        prior = self.seed_prior_lesson(relative="hooks-and-state/check-session-at-dispatch.md",
                                       title="Check the session when dispatching a request", category="Hooks and State")
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        replacement, _ = self.record_lesson(job_id, reviewed)
        old = s.worktree(job_id) / prior
        text = old.read_text().replace("Status: verified-on-branch", "Status: superseded")
        text = text.replace("Verified: 2026-11-15", "Verified: 2026-11-16")
        text = text.replace("## Solution\n", "## Solution\nSuperseded by [the response-time session check]"
                            "(ignore-previous-session-responses.md).\n")
        text = text.replace("## Evidence\n", f"## Evidence\nFinding: code-r1-1. Reviewed commit: {reviewed}.\n")
        old.write_text(text)
        s.git("add", prior, cwd=s.worktree(job_id))
        s.git("commit", "--amend", "--no-edit", cwd=s.worktree(job_id))
        self.report(job_id, reviewed, status="RECORDED", lessons=f"{replacement}, {prior}")

        s.job("advance", job_id, "document")

        self.assertEqual(s.job_json(job_id)["stage"], "document")
        self.assertIn("Status: superseded", old.read_text())
        index = (s.worktree(job_id) / "Knowledge/index.md").read_text()
        self.assertIn("ignore-previous-session-responses.md", index)
        self.assertNotIn("check-session-at-dispatch.md", index)

    def test_lesson_metadata_cannot_claim_shipment_or_an_invalid_verification_date(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        lesson, valid = self.record_lesson(job_id, reviewed)
        path = s.worktree(job_id) / lesson
        original = path.read_text()
        for before, after in (("Status: verified-on-branch", "Status: shipped"),
                              ("Verified: 2026-11-16", "Verified: 2026-02-30")):
            with self.subTest(metadata=after):
                path.write_text(original.replace(before, after))
                s.git("add", lesson, cwd=s.worktree(job_id))
                s.git("commit", "--amend", "--no-edit", cwd=s.worktree(job_id))
                self.refused(job_id, "document")
                self.assertEqual(s.job_json(job_id)["stage"], "teach")
                s.git("reset", "--hard", valid, cwd=s.worktree(job_id))

    def test_knowledge_root_cannot_escape_into_other_directories(self):
        for root in ("../outside", "/tmp/outside", "Knowledge/../Other", ".ai/skills", "Documentation"):
            with self.subTest(root=root):
                self.s.setup_factory(knowledge={"root": root})
                result = self.s.job("create", "Registration", input="Add registration.\n", check=False)
                self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(list((self.s.repo / "factory/jobs").glob("*/job.json")))

    def test_report_cannot_claim_no_change_after_a_knowledge_commit(self):
        job_id, reviewed, _ = self.second_review()
        self.s.job("advance", job_id, "teach")
        self.record_lesson(job_id, reviewed)
        self.report(job_id, reviewed)
        self.refused(job_id, "document")

    def test_report_must_cover_the_confirmed_batch_and_commit(self):
        job_id, reviewed, _ = self.second_review()
        self.s.job("advance", job_id, "teach")
        for commit, findings in (("0" * 40, "code-r1-1"), (reviewed, "code-r1-99")):
            with self.subTest(commit=commit, findings=findings):
                self.report(job_id, commit, findings=findings)
                self.refused(job_id, "document")

    def test_documenter_baseline_starts_after_the_teacher_commit(self):
        s = self.s
        job_id, reviewed, _ = self.second_review()
        s.job("advance", job_id, "teach")
        _, taught = self.record_lesson(job_id, reviewed)
        s.job("advance", job_id, "document")
        self.assertEqual(s.job_json(job_id)["doc_base"], taught)
        s.document(job_id)
        s.job("advance", job_id, "approve")
        self.assertEqual(s.job_json(job_id)["doc"], "Shipped")

    def test_merged_lesson_is_available_to_a_later_feature_worktree(self):
        s = self.s
        first, reviewed, _ = self.second_review()
        s.job("advance", first, "teach")
        lesson, _ = self.record_lesson(first, reviewed)
        s.job("advance", first, "document")
        s.document(first)
        s.job("advance", first, "approve")
        # The fake provider stores PR state only; model its base-ref update locally.
        s.git("push", "origin", "HEAD:main", cwd=s.worktree(first))
        s.write(first, "decision.md", "APPROVE\n\n## Why\nAll criteria passed.\n")
        s.job("merge", first)

        registration = s.create("Add registration", "Allow account registration with pending form requests.\n")
        s.intake(registration)
        s.route(registration)
        s.job("advance", registration, "spec")
        wt = s.worktree(registration)
        index = (wt / "Knowledge/index.md").read_text()
        content = (wt / lesson).read_text()
        self.assertIn("registration", index.lower())
        self.assertIn("authentication", index)
        self.assertIn("code-r1-1", content)
        self.assertIn(reviewed, content)
        self.assertIn(str(wt / "Knowledge"), s.job("header", registration).stdout)
        s.spec(registration)
        with (s.job_dir(registration) / "spec.md").open("a") as spec:
            spec.write(f"\n## Knowledge\nignore-previous-session-responses: {wt / lesson}\n")
        s.job("advance", registration, "build")
        self.assertEqual(s.job_json(registration)["stage"], "build")
        self.assertIn("session generation", content)

    def test_configured_knowledge_root_is_used(self):
        self.s.setup_factory(knowledge={"root": "Engineering/Knowledge"})
        job_id, reviewed, _ = self.second_review()
        self.s.job("advance", job_id, "teach")
        self.record_lesson(job_id, reviewed, root="Engineering/Knowledge")
        self.s.job("advance", job_id, "document")
        self.assertFalse((self.s.worktree(job_id) / "Knowledge").exists())


if __name__ == "__main__":
    unittest.main()
