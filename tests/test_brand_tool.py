"""brand.py: picking library colours and building an audited system from them."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "skills" / "brand" / "identity" / "brand.py"
SPEC = {"slug": "fieldstone", "name": "Fieldstone", "character": "grounded, honest, alert",
        "uses": "agriculture platforms, field operations",
        "rationale": "A working green carries the interface and a red marks what needs attention.",
        "primary": "bold-avocado", "accent": "pickled-radish", "spark": "winter-willow-green", "ink": "river-styx"}


def rows(out):
    """The data rows of pick's table as dicts."""
    lines = [line.split(" | ") for line in out.strip().splitlines()]
    header = lines[0]
    return [dict(zip(header, line, strict=True)) for line in lines[2:]]


class BrandToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def brand(self, *args, check=True):
        res = subprocess.run(["python3", str(BRAND), *args], capture_output=True, text=True)
        if check:
            self.assertEqual(res.returncode, 0, res.stderr)
        return res

    def spec(self, **changes):
        path = self.tmp / "spec.json"
        path.write_text(json.dumps({**SPEC, **changes}))
        return str(path)

    # ---- pick

    def test_pick_by_family_and_role(self):
        greens = rows(self.brand("pick", "--family", "green", "--role", "primary", "--limit", "6").stdout)
        self.assertEqual(len(greens), 6)
        self.assertTrue(all(r["family"] == "green" and 0.2 <= float(r["L"]) <= 0.8 for r in greens))
        lightness = [float(r["L"]) for r in greens]
        self.assertEqual(lightness, sorted(lightness, reverse=True), "spread from light to dark")

    def test_gray_covers_every_neutral_and_inks_are_near_black(self):
        inks = rows(self.brand("pick", "--family", "grey", "--role", "ink").stdout)
        self.assertTrue(inks)
        self.assertTrue(all(r["family"] in {"black", "gray"} and float(r["L"]) <= 0.23 for r in inks))

    def test_pick_near_a_hex_orders_by_closeness(self):
        first = rows(self.brand("pick", "--near", "#027A2F", "--limit", "3").stdout)[0]
        self.assertEqual(first["hex"], "#027A2F")

    def test_pick_by_word(self):
        found = rows(self.brand("pick", "--like", "earthy", "--limit", "5").stdout)
        self.assertTrue(found and all("earthy" in r["character"] for r in found))

    def test_unknown_family_and_bad_hex_are_refused(self):
        res = self.brand("pick", "--family", "chartreuse-ish", check=False)
        self.assertIn("unknown families", res.stderr)
        res = self.brand("pick", "--near", "green", check=False)
        self.assertIn("--near takes a hex colour", res.stderr)

    # ---- build

    def test_check_builds_and_audits_without_writing(self):
        out = self.brand("build", self.spec(), "--check").stdout
        self.assertRegex(out, r"Fieldstone: primary #[0-9A-F]{6} / #[0-9A-F]{6}, .* \d+ contrast checks pass")
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["spec.json"])

    def test_build_writes_guidelines_tokens_and_the_starter_layer(self):
        out_dir = self.tmp / "brand"
        self.brand("build", self.spec(), "--out", str(out_dir), "--starter")
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()),
                         ["fieldstone.css", "fieldstone.md", "fieldstone.starter.css", "fieldstone.tokens.json"])
        guide = (out_dir / "fieldstone.md").read_text()
        for section in ("## Brand colours", "## Logo and icon colours", "## Tokens", "## Scales", "## Rules"):
            self.assertIn(section, guide)
        self.assertIn("A new combination from the colour library.", guide)
        self.assertIn("](https://github.com/IsaacHatilima/brand-colours/blob/main/colors/bold-avocado.md)", guide)
        for name in ("fieldstone.md", "fieldstone.css", "fieldstone.tokens.json"):
            text = (out_dir / name).read_text()
            self.assertNotIn(".png", text, name)
            self.assertNotIn("../colors/", text, name)
        tokens = json.loads((out_dir / "fieldstone.tokens.json").read_text())
        self.assertEqual(tokens["slug"], "fieldstone")

    def test_starter_layer_adds_accents_and_leaves_neutrals_alone(self):
        out_dir = self.tmp / "brand"
        self.brand("build", self.spec(), "--out", str(out_dir), "--starter")
        css = (out_dir / "fieldstone.starter.css").read_text()
        for line in ("  --color-brand-accent: var(--brand-accent);", ":root {", ".dark {"):
            self.assertIn(line, css)
        self.assertRegex(css, r"--primary: #[0-9A-F]{6};")
        for neutral in ("--background:", "--card:", "--sidebar:", "--border:", "--muted:"):
            self.assertNotIn(neutral, css)

    def test_a_spec_that_breaks_the_rules_says_why(self):
        res = self.brand("build", self.spec(accent="forest-bound"), "--check", check=False)
        self.assertEqual(res.returncode, 1)
        self.assertIn("primary and accent hues only", res.stderr)
        self.assertIn("Choose other library colours", res.stderr)

    def test_unknown_colours_and_missing_fields_are_refused(self):
        res = self.brand("build", self.spec(spark="not-a-colour"), "--check", check=False)
        self.assertIn("not in the colour library: not-a-colour", res.stderr)
        res = self.brand("build", self.spec(rationale=""), "--check", check=False)
        self.assertIn("the spec is missing rationale", res.stderr)

    def test_build_needs_an_output_or_check(self):
        res = self.brand("build", self.spec(), check=False)
        self.assertEqual(res.returncode, 2)
        self.assertIn("build needs --out", res.stderr)

    def test_no_bytecode_is_left_in_the_skill(self):
        self.brand("pick", "--family", "red", "--limit", "1")
        self.assertFalse(list(BRAND.parent.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
