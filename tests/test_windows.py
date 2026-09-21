"""Unit tests that need the Win32-backed modules (Windows only).

Run:  python -m unittest discover -s tests -p "test_windows.py" -v

Importing `dnaman.ops` / `dnaman.results` loads the Win32 layer, which is why
these live apart from the platform-free suite in `test_platform_free.py`.
No DNAMAN installation is required - nothing here launches the GUI.
"""

import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dnaman import ops, results, seqmath, skill

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEMO_SEQ = os.path.join(DATA_DIR, "demo.seq")


class TestSeqmathReExports(unittest.TestCase):
    """`ops` re-exports the platform-free helpers under their historical names."""

    def test_reexports_are_identical(self):
        self.assertIs(ops._sizes_from_cuts, seqmath.sizes_from_cuts)
        self.assertIs(ops._read_dnaman_seq, seqmath.read_dnaman_seq)
        self.assertIs(ops._restriction_fragments, seqmath.restriction_fragments)

    def test_demo_fixture_digest_via_ops(self):
        seq = ops._read_dnaman_seq(DEMO_SEQ)
        sites = ops._restriction_fragments(seq, ["EcoRI", "HindIII"], circular=False)
        frags = ops._sizes_from_cuts(len(seq), sites["EcoRI"] + sites["HindIII"],
                                     circular=False)
        self.assertEqual(frags, [51, 200, 49])


class TestTrim(unittest.TestCase):
    def test_trim_crops_borders(self):
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "img.png")
            im = Image.new("RGB", (200, 200), (255, 255, 255))
            ImageDraw.Draw(im).rectangle([80, 80, 120, 120], fill=(0, 0, 0))
            im.save(p)
            results.trim(p, margin=2)
            w, h = Image.open(p).size
            self.assertLess(w, 60)
            self.assertLess(h, 60)


class TestCloningOps(unittest.TestCase):
    def test_silent_mutation_region_params(self):
        import inspect

        sig = inspect.signature(ops.run_silent_mutation)
        self.assertIn("start", sig.parameters)
        self.assertIn("end", sig.parameters)

    def test_directed_mismatch_params(self):
        import inspect

        sig = inspect.signature(ops.run_directed_mismatch)
        self.assertIn("position", sig.parameters)
        self.assertIn("base", sig.parameters)

    def test_set_edit_value_helper(self):
        from dnaman.win32 import set_edit_value

        self.assertTrue(callable(set_edit_value))


class TestSkillInstall(unittest.TestCase):
    def test_bundled_skill_is_present(self):
        self.assertTrue(os.path.isfile(os.path.join(skill.DEFAULT_SOURCE, "SKILL.md")))

    def test_install_into_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = skill.install(dest=tmp)
            self.assertTrue(os.path.isfile(os.path.join(dest, "SKILL.md")))
            with self.assertRaises(FileExistsError):
                skill.install(dest=tmp)
            dest = skill.install(dest=tmp, force=True)
            self.assertTrue(os.path.isfile(os.path.join(dest, "SKILL.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
