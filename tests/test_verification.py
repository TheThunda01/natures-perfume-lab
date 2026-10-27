"""Independent-verifier contracts and tamper regressions."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from verify_results import (VerificationError, aligned_counts, equal,
                            independent_global_score, regular_bytes, strict_json,
                            verify_comparison, verify_results, verify_web_payload)


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def rehash_artifact(bundle, name):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    content = (bundle / name).read_bytes()
    for item in manifest["files"]:
        if item["path"] == name:
            item["sha256"] = hashlib.sha256(content).hexdigest()
            item["bytes"] = len(content)
            break
    else:
        raise AssertionError("Missing test artifact: " + name)
    write_json(bundle / "manifest.json", manifest)


def snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*") if p.is_file()}


class VerifierPrimitiveTests(unittest.TestCase):
    def test_json_rejects_duplicate_keys_and_all_nonfinite_spellings(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                    b'{"x":1e999}', b'{"x":[{"y":-1e999}]}', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises(VerificationError):
                strict_json(raw, "fixture")

    def test_boolean_is_not_an_integer_or_numeric_score(self):
        for expected in (1, 1.0):
            with self.subTest(expected=expected), self.assertRaises(VerificationError):
                equal(True, expected, "metric")

    def test_alignment_counts_use_columns_and_separate_gap_runs(self):
        counts = aligned_counts("AC--DEFGH", "ACWWD--GH")
        self.assertEqual(counts, {"columns": 9, "identities": 5,
                                  "mismatches": 0, "gap_columns": 4,
                                  "gap_runs": 2, "paired_columns": 5})
        self.assertEqual(aligned_counts("A-C", "AC-")["gap_runs"], 2)

    def test_double_gaps_bad_symbols_and_truncated_pairs_fail(self):
        for left, right in (("A--C", "AC-C"), ("A?C", "AAC"),
                            ("AC", "A"), ("", "")):
            with self.subTest(left=left, right=right), self.assertRaises(VerificationError):
                aligned_counts(left, right)

    def test_global_score_matches_hand_computed_affine_gap_examples(self):
        for left, right, expected in (("ACDE", "ACFE", 5.0), ("AAAAA", "AAA", -4.5),
                                      ("AC", "DE", -2.0), ("", "AAA", -11.0)):
            with self.subTest(left=left, right=right):
                self.assertEqual(independent_global_score(left, right), expected)

    def test_self_consistent_but_suboptimal_alignment_is_rejected(self):
        record = {"enzyme_a": "a", "enzyme_b": "b",
                  "scoring": {"match": 2, "mismatch": -1, "open_gap": -10, "extend_gap": -0.5},
                  "alignment_a": "A-C", "alignment_b": "AC-",
                  "alignment_columns": 3, "paired_residues": 1, "matches": 1,
                  "mismatches": 0, "gap_columns": 2,
                  "identity_percent": 100.0, "identity_all_columns_percent": 100 / 3,
                  "score": -18.0}
        with self.assertRaisesRegex(VerificationError, "optimal global"):
            verify_comparison(record, {"a": "AC", "b": "AC"})

    def test_member_paths_cannot_escape_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "member").write_bytes(b"test")
            self.assertEqual(regular_bytes(root, "member"), b"test")
            for path in ("../member", "/member", "dir/../member", "./member",
                         "dir\\member", "", "dir//member"):
                with self.subTest(path=path), self.assertRaises(VerificationError):
                    regular_bytes(root, path)
            try:
                (root / "alias").symlink_to(root / "member")
            except (OSError, NotImplementedError):
                self.skipTest("This environment cannot create symbolic links")
            with self.assertRaisesRegex(VerificationError, "Symlink"):
                regular_bytes(root, "alias")


class SavedResultVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.bundle = self.directory / "results"
        shutil.copytree(ROOT / "results", self.bundle)
        self.analysis = json.loads((self.bundle / "analysis.json").read_text(encoding="utf-8"))

    def verify(self):
        return verify_results(ROOT / "data", self.bundle)

    def replace_analysis(self, change):
        value = copy.deepcopy(self.analysis)
        change(value)
        write_json(self.bundle / "analysis.json", value)
        rehash_artifact(self.bundle, "analysis.json")

    def test_saved_case_passes_without_writing_sources_or_results(self):
        before_data, before_results = snapshot(ROOT / "data"), snapshot(self.bundle)
        result = verify_results(ROOT / "data", self.bundle, ROOT / "web")
        self.assertTrue(result["verified"])
        self.assertTrue(result["web_payload_checked"])
        self.assertEqual(result["enzyme_lengths"], {"limonene_synthase": 607, "linalool_synthase": 564})
        self.assertEqual(result["balanced_reactions_checked"], 2)
        self.assertEqual(result["experimental_structures_checked"], 1)
        self.assertEqual(before_data, snapshot(ROOT / "data"))
        self.assertEqual(before_results, snapshot(self.bundle))

    def test_alignment_metric_or_score_changes_fail_even_after_rehash(self):
        for field in ("matches", "mismatches", "gap_columns", "paired_residues", "alignment_columns",
                      "aligned_length", "identity_percent", "identity_all_columns_percent", "score"):
            self.replace_analysis(lambda value: value["sequence_comparison"].__setitem__(
                field, value["sequence_comparison"][field] + 1))
            with self.subTest(field=field), self.assertRaises(VerificationError):
                self.verify()

    def test_enzyme_identity_sequence_and_provenance_cannot_be_relabelled(self):
        for field, replacement in (("accession", "OTHER"), ("product_id", "linalool"),
                                   ("reviewed", False), ("sequence", "ACDE")):
            self.replace_analysis(lambda value: value["enzymes"][0].__setitem__(field, replacement))
            with self.subTest(field=field), self.assertRaises(VerificationError):
                self.verify()

    def test_chemical_graph_atom_map_and_stereochemistry_tampering_fail(self):
        mutations = [
            lambda molecule: molecule.__setitem__("formula", "C10H18"),
            lambda molecule: molecule["cip"].__setitem__("6", "S"),
            lambda molecule: molecule["carbon_bonds"][0].__setitem__("order", 3.0),
            lambda molecule: molecule["bonds"][0].__setitem__("end", 999),
            lambda molecule: molecule["atoms"][0].__setitem__("map_number", 1),
            lambda molecule: molecule["atoms"][0].__setitem__("symbol", "N"),
            lambda molecule: molecule.__setitem__("mapped_smiles", molecule["mapped_smiles"].replace("@@", "@")),
        ]
        for index, change in enumerate(mutations):
            self.replace_analysis(lambda value: change(value["chemistry"]["molecules"]["limonene"]))
            with self.subTest(mutation=index), self.assertRaises(VerificationError):
                self.verify()

    def test_balanced_flag_does_not_hide_fabricated_balances_or_changes(self):
        def falsify_balances(value):
            balance = value["chemistry"]["reactions"][0]["neutral_species_balance"]
            balance["reactant_elements"]["C"] = 11
            balance["product_elements"]["C"] = 11
        cases = [falsify_balances,
                 lambda value: value["chemistry"]["reactions"][0]["carbon_bond_changes"][0].__setitem__("after", 2.0),
                 lambda value: value["chemistry"]["reactions"][0]["carbon_balance"].__setitem__("product_carbons", 11)]
        for index, change in enumerate(cases):
            self.replace_analysis(change)
            with self.subTest(mutation=index), self.assertRaises(VerificationError):
                self.verify()

    def test_svg_halo_coordinates_must_be_finite_and_inside_viewbox(self):
        for axis, coordinate in (("x", -1), ("x", 601), ("y", 361), ("x", True),
                                 ("y", float("inf"))):
            value = copy.deepcopy(self.analysis)
            value["chemistry"]["molecules"]["limonene"]["atoms"][0]["svg_position"][axis] = coordinate
            # Deliberately allow Infinity to exercise the strict input parser.
            (self.bundle / "analysis.json").write_text(json.dumps(value, allow_nan=True), encoding="utf-8")
            rehash_artifact(self.bundle, "analysis.json")
            with self.subTest(axis=axis, coordinate=coordinate), self.assertRaises(VerificationError):
                self.verify()

    def test_structure_counts_are_recomputed_from_coordinates(self):
        self.replace_analysis(lambda value: value["structural_evidence"]["records"][0].__setitem__(
            "modeled_alpha_carbon_residues", 607))
        with self.assertRaisesRegex(VerificationError, "structural_evidence"):
            self.verify()

    def test_alignment_and_summary_exports_cannot_drift_after_rehash(self):
        cases = {"alignment.fasta": lambda text: text.replace(">limonene_synthase", ">invented_enzyme", 1),
                 "residue_alignment.csv": lambda text: text.replace("\n1,", "\n999,", 1),
                 "chemical_summary.csv": lambda text: text.replace("C10H16", "C10H18", 1)}
        for name, change in cases.items():
            original = (self.bundle / name).read_bytes()
            modified = change(original.decode("utf-8"))
            self.assertNotEqual(modified.encode("utf-8"), original)
            (self.bundle / name).write_text(modified, encoding="utf-8")
            rehash_artifact(self.bundle, name)
            with self.subTest(artifact=name), self.assertRaises(VerificationError):
                self.verify()
            (self.bundle / name).write_bytes(original)
            rehash_artifact(self.bundle, name)

    def test_source_rehashing_cannot_replace_the_pinned_case(self):
        data = self.directory / "data"
        shutil.copytree(ROOT / "data", data)
        path = data / "sources/uniprot_Q2XSC5.fasta"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(VerificationError, "fingerprint"):
            verify_results(data, self.bundle)
        manifest = json.loads((data / "provenance.json").read_text(encoding="utf-8"))
        for item in manifest["files"]:
            if item["path"] == "data/sources/uniprot_Q2XSC5.fasta":
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                item["bytes"] = len(path.read_bytes())
        write_json(data / "provenance.json", manifest)
        with self.assertRaisesRegex(VerificationError, "pinned case"):
            verify_results(data, self.bundle)

    def test_duplicate_result_inventory_and_unlisted_files_fail(self):
        manifest = json.loads((self.bundle / "manifest.json").read_text(encoding="utf-8"))
        manifest["files"].append(copy.deepcopy(manifest["files"][0]))
        write_json(self.bundle / "manifest.json", manifest)
        with self.assertRaisesRegex(VerificationError, "duplicate"):
            self.verify()
        manifest["files"].pop()
        write_json(self.bundle / "manifest.json", manifest)
        (self.bundle / "unlisted.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(VerificationError, "unlisted"):
            self.verify()

    def test_result_symlink_cannot_substitute_a_regular_artifact(self):
        path = self.bundle / "analysis.json"
        path.unlink()
        try:
            path.symlink_to(ROOT / "results/analysis.json")
        except (OSError, NotImplementedError):
            self.skipTest("This environment cannot create symbolic links")
        with self.assertRaisesRegex(VerificationError, "Symlink"):
            self.verify()

    def test_web_payload_must_match_exactly_even_below_numeric_tolerance(self):
        web = self.directory / "web"
        web.mkdir()
        changed = copy.deepcopy(self.analysis)
        changed["sequence_comparison"]["identity_percent"] += 1e-12
        (web / "data.js").write_text("window.PERFUME_DATA = " + json.dumps(changed) + ";\n", encoding="utf-8")
        with self.assertRaisesRegex(VerificationError, "Web payload differs"):
            verify_web_payload(web, self.analysis)
        (web / "data.js").write_text("window.PERFUME_DATA = " + json.dumps(self.analysis) + "; alert('extra');\n", encoding="utf-8")
        with self.assertRaises(VerificationError):
            verify_web_payload(web, self.analysis)

    def test_cli_reports_success_and_nonzero_failure_without_traceback(self):
        command = [sys.executable, str(ROOT / "verify_results.py"), "--results-dir", str(self.bundle), "--json"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["verified"])
        (self.bundle / "analysis.json").write_text("not JSON", encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Verification stopped", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
