"""./install: one copy of every skill in .ai/skills, command pointers, agents, and instruction blocks."""

import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install"
ROLES = ["approver", "builder", "documenter", "intake", "reviewer-code", "reviewer-security",
         "reviewer-ui", "reviewer-ux", "spec-writer"]
BLOCK = re.compile(r"<!-- skills:start -->.*?<!-- skills:end -->", re.S)


def source_fields(role):
    text = (ROOT / "agents" / "factory" / f"{role}.md").read_text()
    head = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in head.splitlines())


def claude_frontmatter(path):
    head = re.match(r"---\n(.*?)\n---\n", path.read_text(), re.S).group(1)
    return {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in head.splitlines()
            if not line.startswith(" ") and ":" in line}


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="factory-install-")).resolve()
        self.project = self.tmp / "app"
        self.project.mkdir()
        self.skills = self.project / ".ai" / "skills"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def install(self, *args, check=True, home=None):
        env = {**os.environ, "HOME": str(home or self.tmp / "home")}
        res = subprocess.run([str(INSTALL), *args], capture_output=True, text=True, env=env)
        if check:
            self.assertEqual(res.returncode, 0, res.stderr)
        return res

    # ---- one copy

    def test_every_skill_and_the_factory_have_one_copy_in_ai_skills(self):
        self.install("all", "--project", str(self.project))
        installed = {p.parent.name for p in self.skills.glob("*/SKILL.md")}
        library = {f"{p.parent.parent.name}-{p.parent.name}" for p in (ROOT / "skills").glob("*/*/SKILL.md")}
        self.assertEqual(installed, library)
        self.assertTrue((self.skills / "catalog.md").is_file())
        for folder in (self.project / ".claude" / "skills", self.project / ".agents" / "skills"):
            self.assertEqual([p.name for p in folder.iterdir()], ["factory"], f"{folder} holds only the pointer")

    def test_the_factory_bundle_is_complete_and_runnable(self):
        self.install("basic", "--project", str(self.project), "--host", "claude")
        factory = self.skills / "factory"
        for rel in ("AGENT.md", "LICENSE", "references/skills.md", "bin/factorylib/transitions.py",
                    "templates/config.json", "templates/dashboard.html"):
            self.assertTrue((factory / rel).is_file(), rel)
        for rel in ("bin/job", "bin/gate", "bin/route", "templates/checks.sh"):
            self.assertTrue(os.access(factory / rel, os.X_OK), rel)
        self.assertFalse(list(factory.rglob("__pycache__")))
        res = subprocess.run([str(factory / "bin/job"), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("job header <job>", res.stdout)

    def test_command_pointers_name_the_one_factory(self):
        self.install("basic", "--project", str(self.project))
        for pointer in (self.project / ".claude/skills/factory/SKILL.md", self.project / ".agents/skills/factory/SKILL.md"):
            text = pointer.read_text()
            self.assertIn("name: factory\n", text)
            self.assertIn("disable-model-invocation: true", text)
            self.assertIn("Read `.ai/skills/factory/AGENT.md`", text)
        self.assertIn("allow_implicit_invocation: false",
                      (self.project / ".agents/skills/factory/agents/openai.yaml").read_text())

    def test_skills_are_renamed_with_their_group(self):
        self.install("basic", "--project", str(self.project))
        self.assertRegex((self.skills / "quality-review/SKILL.md").read_text(), r"(?m)^name: quality-review$")
        self.assertRegex((self.skills / "brand-identity/SKILL.md").read_text(), r"(?m)^name: brand-identity$")
        self.assertTrue((self.skills / "brand-identity/kolors/system.py").is_file())
        self.assertTrue((self.skills / "quality-security-review/references/LICENSE").is_file())
        self.assertFalse((self.skills / "nest-actions").exists())

    def test_bundles_combine_and_include_each_other(self):
        self.install("web", "laravel", "--project", str(self.project))
        for native in ("frontend-overlays", "next-actions", "javascript-domain-driver", "laravel-actions", "laravel-api-responses",
                       "quality-simplicity", "typescript-best-practices"):
            self.assertTrue((self.skills / native / "SKILL.md").is_file(), native)
        self.assertTrue((self.skills / "laravel-api-responses/templates/ApiResponse.php").is_file())

    # ---- agents

    def test_agents_keep_their_models_effort_and_tools(self):
        self.install("basic", "--project", str(self.project))
        for role in ROLES:
            src = source_fields(role)
            claude = claude_frontmatter(self.project / ".claude/agents" / f"{role}.md")
            self.assertEqual((claude["name"], claude["model"], claude["tools"], claude["effort"]),
                             (role, src["claude-model"], src["claude-tools"], src["claude-effort"]), role)
            codex = tomllib.loads((self.project / ".codex/agents" / f"{role}.toml").read_text())
            self.assertEqual((codex["name"], codex["model"], codex["model_reasoning_effort"]),
                             (role, src["codex-model"], src["codex-reasoning-effort"]), role)
            self.assertIn("## ", codex["developer_instructions"])

    def test_builder_hook_runs_the_gate_from_ai_skills(self):
        self.install("basic", "--project", str(self.project))
        builder = (self.project / ".claude/agents/builder.md").read_text()
        self.assertIn("""command: '"$CLAUDE_PROJECT_DIR"/.ai/skills/factory/bin/gate --hook'""", builder)
        self.assertNotIn("hooks:", (self.project / ".claude/agents/reviewer-code.md").read_text())

    # ---- instruction files

    def test_instruction_files_point_at_the_skills_and_keep_their_text(self):
        (self.project / "AGENTS.md").write_text("# App\n\nRun pnpm test.\n")
        self.install("laravel", "--project", str(self.project))
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.project / name).read_text()
            self.assertEqual(len(BLOCK.findall(text)), 1, name)
            self.assertIn("Agent skills live in `.ai/skills/`", text)
            self.assertIn("| `laravel-actions` | creating, refactoring, or reviewing a Laravel action", text)
            self.assertIn("`.ai/skills/factory/AGENT.md`", text)
            self.assertNotIn("| `factory` |", text)
        self.assertTrue((self.project / "AGENTS.md").read_text().startswith("# App\n\nRun pnpm test.\n\n<!-- skills:start -->"))

    def test_reinstalling_replaces_the_block_and_lists_every_installed_skill(self):
        self.install("basic", "--project", str(self.project))
        self.assertIn("0 of", self.install("basic", "--project", str(self.project)).stdout)
        self.install("api", "--project", str(self.project))
        text = (self.project / "AGENTS.md").read_text()
        self.assertEqual(len(BLOCK.findall(text)), 1)
        self.assertIn("| `nest-actions` |", text)
        self.assertIn("| `brand-identity` |", text)

    def test_a_claude_md_that_imports_agents_md_gets_no_second_block(self):
        (self.project / "CLAUDE.md").write_text("@AGENTS.md\n")
        self.install("basic", "--project", str(self.project), "--host", "claude")
        self.assertEqual((self.project / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        self.assertEqual(len(BLOCK.findall((self.project / "AGENTS.md").read_text())), 1)

    def test_one_host_writes_only_its_instruction_file(self):
        self.install("basic", "--project", str(self.project), "--host", "codex")
        self.assertTrue((self.project / "AGENTS.md").is_file())
        self.assertFalse((self.project / "CLAUDE.md").exists())
        self.assertFalse((self.project / ".claude").exists())
        self.assertTrue((self.project / ".codex/agents/builder.toml").is_file())

    def test_user_install_uses_home_paths(self):
        home = self.tmp / "home"
        home.mkdir()
        self.install("basic", home=home)
        self.assertTrue((home / ".ai/skills/quality-review/SKILL.md").is_file())
        self.assertIn("Read `~/.ai/skills/factory/AGENT.md`", (home / ".claude/skills/factory/SKILL.md").read_text())
        self.assertIn('"$HOME"/.ai/skills/factory/bin/gate --hook', (home / ".claude/agents/builder.md").read_text())
        for path in (home / ".claude/CLAUDE.md", home / ".codex/AGENTS.md"):
            self.assertIn("Agent skills live in `~/.ai/skills/`", path.read_text(), path)

    # ---- the rest

    def test_conflicts_need_force_but_instruction_files_merge(self):
        self.install("basic", "--project", str(self.project))
        agent = self.project / ".claude/agents/builder.md"
        agent.write_text("mine\n")
        (self.project / "AGENTS.md").write_text("# Changed by hand\n")
        res = self.install("basic", "--project", str(self.project), check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn(str(agent), res.stderr)
        self.assertNotIn("AGENTS.md", res.stderr)
        self.assertEqual(agent.read_text(), "mine\n")
        self.install("basic", "--project", str(self.project), "--force")
        self.assertIn("name: builder", agent.read_text())
        self.assertTrue((self.project / "AGENTS.md").read_text().startswith("# Changed by hand\n"))

    def test_list_shows_the_bundles(self):
        out = self.install("--list").stdout
        for name in ("basic", "web", "laravel", "api", "all"):
            self.assertRegex(out, rf"(?m)^  {name}\s+\d+ skills")

    def test_a_bundle_is_required(self):
        res = self.install("--project", str(self.project), check=False)
        self.assertEqual(res.returncode, 2)
        self.assertIn("name at least one bundle", res.stderr)

    def test_unknown_bundle_is_refused(self):
        res = self.install("rails", "--project", str(self.project), check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("unknown bundle 'rails'; have: all, api, basic, laravel, web", res.stderr)


if __name__ == "__main__":
    unittest.main()
