"""The skill library stays consistent: catalog entries, skill names, bundles and factory assignments."""

import importlib.machinery
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load_installer():
    loader = importlib.machinery.SourceFileLoader("installer", str(ROOT / "install"))
    spec = importlib.util.spec_from_loader("installer", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def skill_dirs():
    return sorted(p.parent for p in SKILLS.glob("*/*/SKILL.md"))


class LibraryTest(unittest.TestCase):
    def test_every_skill_is_in_the_catalog_with_its_canonical_path(self):
        catalog = (SKILLS / "catalog.md").read_text()
        for skill in skill_dirs():
            skill_id = f"{skill.parent.name}/{skill.name}"
            self.assertIn(f"| {skill_id} | `{skill_id}/SKILL.md` |", catalog, skill_id)

    def test_every_skill_names_its_folder_and_describes_when_to_use_it(self):
        for skill in skill_dirs():
            head = re.match(r"---\n(.*?)\n---\n", (skill / "SKILL.md").read_text(), re.S)
            self.assertTrue(head, skill)
            fields = dict(line.split(": ", 1) for line in head.group(1).splitlines())
            self.assertEqual(fields["name"], skill.name, skill)
            self.assertIn("use when", fields["description"].lower(), skill)

    def test_relative_links_in_skills_resolve(self):
        for skill in skill_dirs():
            text = (skill / "SKILL.md").read_text()
            for target in re.findall(r"\]\(([^)#\s]+)\)", text):
                if not target.startswith("http"):
                    self.assertTrue((skill / target).exists(), f"{skill.name}: {target}")

    def test_factory_selection_names_only_catalog_skills(self):
        catalog = (SKILLS / "catalog.md").read_text()
        selection = (ROOT / "agents" / "factory" / "references" / "skills.md").read_text()
        for skill_id in re.findall(r"^\| `([a-z-]+/[a-z-]+)` \|", selection, re.M):
            self.assertIn(f"| {skill_id} |", catalog, skill_id)


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def use_bundles(self, bundles):
        path = Path(self.tmp.name) / "bundles.json"
        path.write_text(json.dumps(bundles))
        self.installer.BUNDLES = path

    def test_every_shipped_bundle_resolves(self):
        bundles = json.loads((ROOT / "bundles.json").read_text())
        for name in bundles:
            skills, _ = self.installer.resolve([name])
            self.assertTrue(skills, name)
        all_skills, workflows = self.installer.resolve(["all"])
        self.assertEqual(len(all_skills), len(skill_dirs()))
        self.assertEqual(workflows, ["factory"])

    def test_a_bundle_without_workflows_installs_no_factory(self):
        self.use_bundles({"brand": {"skills": ["brand/identity"]}})
        self.assertEqual(self.installer.resolve(["brand"]), (["brand/identity"], []))
        with tempfile.TemporaryDirectory() as root:
            files = self.installer.plan(Path(root), ("claude", "codex"), ["brand/identity"], [], user=False)
            self.assertFalse([p for p in files if "factory" in p.parts or "agents" == p.parent.name])

    def test_a_pattern_that_matches_nothing_is_refused(self):
        self.use_bundles({"typo": {"skills": ["qualty/*"]}})
        with self.assertRaisesRegex(self.installer.InstallError, "'qualty/\\*' matches nothing"):
            self.installer.resolve(["typo"])

    def test_include_cycles_are_refused(self):
        self.use_bundles({"a": {"include": ["b"]}, "b": {"include": ["a"]}})
        with self.assertRaisesRegex(self.installer.InstallError, "includes itself"):
            self.installer.resolve(["a"])


if __name__ == "__main__":
    unittest.main()
