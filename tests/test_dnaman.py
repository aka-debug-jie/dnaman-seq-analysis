"""Unit tests for the dnaman toolkit.

Run:  python -m unittest discover -s tests -v
"""

import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dnaman import commands, config, ops, report, results

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEMO_SEQ = os.path.join(DATA_DIR, "demo.seq")


class TestConfig(unittest.TestCase):
    def test_exe_path(self):
        self.assertTrue(config.EXE.endswith("DNAMAN.EXE"))
        self.assertTrue(config.EXE.startswith(config.DN_DIR))

    def test_seq_path_relative_and_absolute(self):
        rel = config.seq_path("insert.seq")
        self.assertEqual(rel, os.path.join(config.SEQ_DIR, "insert.seq"))
        abs_path = os.path.join(config.SEQ_DIR, "insert.seq")
        self.assertEqual(config.seq_path(abs_path), abs_path)


class TestCommands(unittest.TestCase):
    def test_known_ids(self):
        self.assertEqual(commands.CMD["composition"], 251)
        self.assertEqual(commands.CMD["restriction"], 325)
        self.assertEqual(commands.CMD["align_two"], 315)
        self.assertEqual(commands.CMD["load_multiple"], 228)
        self.assertEqual(commands.CMD["silent_mutation"], 347)
        self.assertEqual(commands.CMD["map_reconstruction"], 340)
        self.assertEqual(commands.CMD["pcr_primers"], 430)

    def test_no_duplicate_ids(self):
        ids = list(commands.CMD.values())
        self.assertEqual(len(ids), len(set(ids)), "duplicate command ids")

    def test_dialog_ids_present(self):
        for key in ("file_name_edit", "ok", "wizard_next", "select_all", "genbank_list"):
            self.assertIn(key, commands.DLG)


class TestMetricExtraction(unittest.TestCase):
    def test_composition(self):
        text = ("SEQ  demo: 1500 bp;\n"
                "Composition  350  A; 393  C; 451  G; 306  T; 0 OTHER\n")
        m = report._extract(text)
        self.assertEqual(m["length_bp"], 1500)
        self.assertEqual((m["A"], m["C"], m["G"], m["T"]), (350, 393, 451, 306))

    def test_orf(self):
        text = ("Possible Open Reading Frame in demo_cds(1-1563)\n"
                "Strand  RF  AA Num  Position    Sequence\n"
                " Plus    2   464      2-1396    ...tgctaTGAtgtgt\n")
        m = report._extract(text)
        self.assertEqual(m["longest_orf_aa"], 464)
        self.assertEqual(m["longest_orf_pos"], "2-1396")

    def test_restriction(self):
        text = ("Restriction analysis on vector\n"
                "Screened with 11 enzymes, 9 sites found\n"
                "BamHI       1     G/GATCC\n"
                "                  251   \n"
                "EcoRI       1     G/AATTC\n"
                "                  230   \n")
        m = report._extract(text)
        self.assertEqual(m["sites_found"], 9)
        self.assertEqual(m["enzymes_cut"], "BamHI, EcoRI")

    def test_primer_pairs(self):
        text = ("PCR primer list\n"
                "  27 AGCACAGAGCCTCGCCTTT  62.6C and  440 ATCTTCTCGCGGTTGGCCT  64.4C\n"
                "  27 AGCACAGAGCCTCGCCTTT  62.6C and  445 GGGTCATCTTCTCGCGGTT  62.5C\n")
        self.assertEqual(report._extract(text)["pcr_pairs"], 2)

    def test_identity(self):
        text = "query:product identity= 99%\n"
        self.assertEqual(report._extract(text)["identity_pct"], 99)


class TestFragmentMath(unittest.TestCase):
    def test_circular_two_cuts(self):
        self.assertEqual(sorted(ops._sizes_from_cuts(1000, [100, 300], circular=True)),
                         [200, 800])

    def test_linear_two_cuts(self):
        self.assertEqual(ops._sizes_from_cuts(1000, [100, 300], circular=False),
                         [99, 200, 701])

    def test_no_cuts(self):
        self.assertEqual(ops._sizes_from_cuts(500, [], circular=True), [500])

    def test_common_vector_double_digest(self):
        # 2686 bp vector, EcoRI and HindIII sites 51 bp apart -> 51 + 2635 bp
        both = ops._sizes_from_cuts(2686, [230, 281], circular=True)
        self.assertEqual(sorted(both), [51, 2635])

    def test_demo_fixture_digest(self):
        seq = ops._read_dnaman_seq(DEMO_SEQ)
        sites = ops._restriction_fragments(seq, ["EcoRI", "HindIII"], circular=False)
        # Biopython reports the cut position (site start + 1 for EcoRI/HindIII)
        self.assertEqual(sites["EcoRI"], [52])
        self.assertEqual(sites["HindIII"], [252])
        frags = ops._sizes_from_cuts(len(seq), sites["EcoRI"] + sites["HindIII"],
                                     circular=False)
        self.assertEqual(frags, [51, 200, 49])


class TestReadSequence(unittest.TestCase):
    def test_read_dnaman_seq(self):
        seq = ops._read_dnaman_seq(DEMO_SEQ)
        self.assertEqual(len(seq), 300)
        self.assertTrue(set(seq) <= set("ACGTN"))


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


class TestReportCollect(unittest.TestCase):
    def test_collect_and_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            tdir = os.path.join(tmp, "topic_a")
            os.makedirs(tdir)
            with open(os.path.join(tdir, "text.txt"), "w", encoding="utf-8") as fh:
                fh.write("SEQ  X: 10 bp;\nComposition  3  A; 2  C; 2  G; 3  T; 0 OTHER\n")
            rows = report.collect(tmp)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["metrics"]["length_bp"], 10)

            out = os.path.join(tmp, "summary.xlsx")
            path, files, topics = report.build_excel(out, tmp)
            self.assertTrue(os.path.exists(path))
            self.assertEqual((files, topics), (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
