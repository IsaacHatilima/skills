"""scripts/sync-brand-colours against a local brand-colours checkout."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync-brand-colours"
SKILL = ROOT / "skills" / "brand" / "identity"
MODULES = ("colormath", "scales", "status", "system", "checks", "describe", "render_md", "render_tokens", "specs")


def write_color(source, slug, name, hex_):
    (source / "colors").mkdir(parents=True, exist_ok=True)
    (source / "colors" / f"{slug}.md").write_text(
        f"## {name}\n\n![{name}](./images/{slug}.png)\n\n- HEX: {hex_}\n- Character: calm, precise\n"
        "- Suggested uses: banks, clinics\n")


def write_system(source, slug, name):
    folder = source / "palettes" / slug
    folder.mkdir(parents=True)
    swatch = lambda colour, hex_: {"name": colour, "hex": hex_, "file": f"../../colors/{colour.lower()}.md"}  # noqa: E731
    tokens = {"name": name, "slug": slug, "character": "calm, precise", "uses": "banks, clinics",
              "logo": {"primary": swatch("Navy", "#1C273E"), "accent": swatch("Brass", "#C39545"),
                       "spark": swatch("Sky", "#70C6E2"), "ink": swatch("Ink", "#11141B")}}
    (folder / f"{slug}.tokens.json").write_text(json.dumps(tokens))
    (folder / f"{slug}.css").write_text(":root { --primary: #1C273E; }\n")
    (folder / f"{slug}.md").write_text(
        f"# {name}\n\n![{name} sheet]({slug}.png)\n\n- Primary: [Navy](../../colors/navy.md)\n")


class BrandSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.source, self.target = self.tmp / "brand-colours", self.tmp / "identity"
        write_color(self.source, "navy", "Navy", "#1c273e")
        write_color(self.source, "brass", "Brass", "#C39545")
        (self.source / "colors" / "index.md").write_text("# Colours\n")
        (self.source / "tools").mkdir()
        for module in MODULES:
            (self.source / "tools" / f"{module}.py").write_text(f"# {module}\n")
        (self.source / "tools" / "render_sheet.py").write_text("from PIL import Image\n")
        write_system(self.source, "midnight-brass", "Midnight Brass")
        write_system(self.source, "aegean-pop", "Aegean Pop")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sync(self, check=True):
        res = subprocess.run([str(SYNC), "--source", str(self.source), "--target", str(self.target)],
                             capture_output=True, text=True)
        if check:
            self.assertEqual(res.returncode, 0, res.stderr)
        return res

    def test_writes_the_library_the_generator_and_the_systems(self):
        out = self.sync().stdout
        self.assertIn("2 library colours; 9 generator modules changed; 2 reference systems (2 added", out)
        library = json.loads((self.target / "library" / "colors.json").read_text())
        self.assertEqual(library["count"], 2)
        self.assertEqual(library["colors"][1], {"slug": "navy", "name": "Navy", "hex": "#1C273E",
                                                "character": "calm, precise", "uses": "banks, clinics"})
        self.assertEqual(sorted(p.stem for p in (self.target / "kolors").glob("*.py")), sorted(MODULES))
        self.assertFalse((self.target / "kolors" / "render_sheet.py").exists(), "the PIL renderer stays out")

    def test_points_system_links_at_the_repository(self):
        self.sync()
        page = (self.target / "systems" / "midnight-brass" / "midnight-brass.md").read_text()
        self.assertIn("](https://raw.githubusercontent.com/IsaacHatilima/brand-colours/main/palettes/midnight-brass/midnight-brass.png)", page)
        self.assertIn("](https://github.com/IsaacHatilima/brand-colours/blob/main/colors/navy.md)", page)
        index = (self.target / "systems" / "index.md").read_text()
        self.assertIn("| [Aegean Pop](aegean-pop/aegean-pop.md) | Navy `#1C273E` | Brass `#C39545` | ", index)

    def test_resync_reports_changes_and_removes_deleted_systems(self):
        self.sync()
        self.assertIn("0 generator modules changed; 2 reference systems (0 added or changed, 0 removed)", self.sync().stdout)
        shutil.rmtree(self.source / "palettes" / "aegean-pop")
        (self.source / "palettes" / "midnight-brass" / "midnight-brass.css").write_text(":root { --primary: #000; }\n")
        self.assertIn("1 reference systems (1 added or changed, 1 removed)", self.sync().stdout)
        self.assertFalse((self.target / "systems" / "aegean-pop").exists())

    def test_refuses_a_folder_that_isnt_brand_colours(self):
        shutil.rmtree(self.source / "colors")
        res = self.sync(check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("has no colors/ folder", res.stderr)

    def test_the_shipped_copy_is_complete(self):
        library = json.loads((SKILL / "library" / "colors.json").read_text())
        self.assertEqual(library["count"], len(library["colors"]))
        self.assertGreater(library["count"], 100)
        for module in MODULES:
            self.assertTrue((SKILL / "kolors" / f"{module}.py").is_file(), module)
        systems = SKILL / "systems"
        for slug in (p.name for p in systems.iterdir() if p.is_dir()):
            for name in (f"{slug}.md", f"{slug}.css", f"{slug}.tokens.json"):
                self.assertTrue((systems / slug / name).is_file(), f"{slug}/{name}")


if __name__ == "__main__":
    unittest.main()
