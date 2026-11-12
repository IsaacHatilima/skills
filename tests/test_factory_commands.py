"""The job script's other commands: cost, summary, reject, and the needs-info round trip."""

import json
import re
import unittest

from sandbox import Sandbox


class CommandsTest(unittest.TestCase):
    def setUp(self):
        self.s = Sandbox()
        self.s.setup_factory()

    def tearDown(self):
        self.s.cleanup()

    def transcript(self, job_id, entries):
        project = re.sub(r"[^A-Za-z0-9]", "-", str(self.s.repo))
        path = self.s.tmp / "claude" / "projects" / project / "session-1" / "subagents" / "agent-1.jsonl"
        path.parent.mkdir(parents=True)
        header = self.s.job("header", job_id).stdout.strip()
        lines = [{"message": {"content": [{"type": "text", "text": header + " Build round 1."}]}}] + entries
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")

    def test_cost_prices_the_job_s_transcripts_and_skips_unknown_models(self):
        job_id = self.s.start_job()
        usage = {"input_tokens": 1_000_000, "output_tokens": 100_000, "cache_read_input_tokens": 1_000_000,
                 "cache_creation_input_tokens": 1_000_000, "cache_creation": {"ephemeral_1h_input_tokens": 0}}
        self.transcript(job_id, [
            {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5-5", "usage": usage}},
            {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5-5", "usage": usage}},
            {"type": "assistant", "message": {"id": "m2", "model": "some-new-model", "usage": usage}},
            "not json",
        ])
        self.s.job("sync", job_id)
        # 1M input $4 + 0.1M output $2 + 1M cache read $0.20 + 1M 5m cache write $5, counted once per message id.
        self.assertEqual(self.s.job_json(job_id)["cost_usd"], 11.2)

    def rollout(self, name, mentions, *, cwd=None, parent="orchestrator", model="gpt-test"):
        """A Codex session log; `mentions` maps job ids to how often its commands name their folders."""
        day = self.s.job_json(next(iter(mentions)))["started"][:10].replace("-", "/")
        path = self.s.tmp / "codex" / "sessions" / day / f"rollout-{name}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"id": name, "cwd": str(cwd or self.s.repo), **({"parent_thread_id": parent} if parent else {})}
        lines = [{"type": "session_meta", "payload": meta},
                 {"type": "turn_context", "payload": {"model": model}},
                 {"type": "response_item", "payload": {"type": "agent_message",
                                                       "content": [{"type": "encrypted_content"}]}}]
        for job_id, count in mentions.items():
            folder = f"{self.s.repo}/factory/jobs/{job_id}/"
            lines += [{"type": "response_item", "payload": {"type": "function_call", "arguments": f"cat {folder}spec.md"}}
                      ] * count
        total = {"input_tokens": 1_000_000, "cached_input_tokens": 600_000, "output_tokens": 100_000,
                 "total_tokens": 1_100_000}
        lines += [{"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
                      "input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 1, "total_tokens": 11}}}},
                  {"type": "event_msg", "payload": {"type": "token_count", "info": None}},
                  {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": total}}}]
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")

    def test_cost_counts_codex_subagents_by_the_job_folder_they_work_in(self):
        s = self.s
        job_id = s.start_job()
        s.add_issue(13, "Add multiply", ["factory"])
        other = s.job("create", "13").stdout.strip()
        path = s.repo / "factory" / "config.json"
        config = json.loads(path.read_text())
        config["prices_usd_per_mtok"]["gpt-test"] = {"input": 2.0, "output": 10.0, "cache_read": 0.5}
        path.write_text(json.dumps(config))
        self.rollout("builder", {job_id: 2})
        self.rollout("unpriced", {job_id: 2}, model="gpt-unknown")
        self.rollout("orchestrator", {job_id: 2}, parent=None)
        self.rollout("another-repo", {job_id: 2}, cwd=s.tmp / "another-repo")
        self.rollout("mostly-the-other-job", {job_id: 1, other: 3})
        s.job("sync", job_id)
        s.job("sync", other)
        # A priced session: 0.4M uncached input $0.80 + 0.6M cached $0.30 + 0.1M output $1.00 = $2.10.
        # Unpriced models add tokens but no dollars; orchestrators and other repositories don't count.
        self.assertEqual((s.job_json(job_id)["cost_usd"], s.job_json(job_id)["tokens"]), (2.1, 2_200_000))
        self.assertEqual((s.job_json(other)["cost_usd"], s.job_json(other)["tokens"]), (2.1, 1_100_000))
        self.assertRegex(s.job("summary", job_id).stdout, rf"{job_id}.*\$2\.10\s+2\.2M")

    def test_summary_lists_stage_docs_and_cost(self):
        job_id = self.s.start_job()
        out = self.s.job("summary").stdout
        self.assertRegex(out, r"job\s+issue\s+stage\s+round\s+pr\s+docs\s+cost\s+tokens\s+time")
        self.assertRegex(out, rf"{job_id}\s+#12\s+build\s+1\s+-\s+-\s+\$0\.00\s+0")
        self.assertIn("total $0.00", out)

    def test_reject_closes_the_pr_and_clears_labels(self):
        s = self.s
        path = s.repo / "factory" / "config.json"
        path.write_text(json.dumps({**json.loads(path.read_text()), "max_rounds": 1}))
        job_id = s.start_job()
        s.to_review(job_id)
        s.review(job_id, verdict="CHANGES")
        res = s.job("reject", job_id, input="Not now.\n", check=False)
        self.assertIn("not needs-info or needs-human", res.stderr)
        s.job("advance", job_id, "document")
        s.document(job_id, status="Not shipped")
        s.job("advance", job_id, "needs-human")
        self.assertIn("rejected", s.job("reject", "12", input="Not now.\n").stdout)
        gh = s.gh_state()
        self.assertEqual(gh["prs"]["100"]["state"], "CLOSED")
        self.assertEqual(gh["issues"]["12"]["labels"], [])
        self.assertIn("Not now.", gh["issues"]["12"]["comments"][-1]["body"])
        self.assertEqual(s.job_json(job_id)["stage"], "rejected")
        self.assertFalse(s.worktree(job_id).exists())

    def test_needs_info_waits_for_the_author_then_resumes(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id, decision="NEEDS-INFO")
        s.job("advance", job_id, "needs-info")
        self.assertIn("factory:needs-info", s.gh_state()["issues"]["12"]["labels"])
        self.assertEqual(s.job("queue").stdout.split("\t")[0], "wait")
        state = s.gh_state()
        state["issues"]["12"]["comments"].append(
            {"author": {"login": "alice"}, "body": "Integers only.", "createdAt": "2026-11-12T01:00:00Z"})
        s.state_file.write_text(json.dumps(state))
        self.assertEqual(s.job("queue").stdout.split("\t")[:5], ["resume", "12", job_id, "needs-info", "author replied\n"])
        s.job("advance", job_id, "intake")
        self.assertTrue((s.job_dir(job_id) / "intake-1.md").exists())
        self.assertIn("Integers only.", (s.job_dir(job_id) / "issue.md").read_text())

    def test_accept_survives_a_failed_comment_and_comments_once(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id)
        s.route(job_id)
        res = s.job("advance", job_id, "spec", check=False, env={"FAKE_GH_FAIL": "issue comment"})
        self.assertIn("failing `issue comment` on purpose", res.stderr)
        self.assertEqual(s.job_json(job_id)["stage"], "intake")
        s.job("advance", job_id, "spec")
        self.assertEqual(s.job_json(job_id)["stage"], "spec")
        self.assertTrue(s.worktree(job_id).is_dir())
        comments = [c for c in s.gh_state()["issues"]["12"]["comments"] if "Factory intake" in c["body"]]
        self.assertEqual(len(comments), 1)

    def test_resuming_after_a_failed_label_change_does_not_crash(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id, decision="NEEDS-INFO")
        s.job("advance", job_id, "needs-info")
        res = s.job("advance", job_id, "intake", check=False, env={"FAKE_GH_FAIL": "issue edit"})
        self.assertIn("failing `issue edit` on purpose", res.stderr)
        self.assertTrue((s.job_dir(job_id) / "intake.md").exists(), "nothing moved before the refusal")
        s.job("advance", job_id, "intake")
        self.assertTrue((s.job_dir(job_id) / "intake-1.md").exists())
        self.assertEqual(s.job_json(job_id)["stage"], "intake")

    def test_surfaces_none_in_any_case_routes_only_the_code_reviewer(self):
        job_id = self.s.job("create", "12").stdout.strip()
        self.s.intake(job_id, surfaces="None")
        self.assertIn("reviewers code\n", self.s.route(job_id).stdout)

    def test_rejected_at_intake_removes_the_queue_label(self):
        s = self.s
        job_id = s.job("create", "12").stdout.strip()
        s.intake(job_id, decision="REJECT")
        s.job("advance", job_id, "rejected")
        self.assertEqual(s.gh_state()["issues"]["12"]["labels"], [])
        rows = s.job("queue").stdout
        self.assertEqual(rows, "", "a rejected issue without the label drops out of the queue")

    def test_a_pr_merged_by_hand_finishes_the_job(self):
        s = self.s
        job_id = s.start_job()
        s.to_review(job_id)
        state = s.gh_state()
        state["prs"]["100"]["state"] = "MERGED"
        s.state_file.write_text(json.dumps(state))
        s.job("queue")
        self.assertEqual(s.job_json(job_id)["stage"], "merged")


if __name__ == "__main__":
    unittest.main()
