"""Behavioral checks for chemical identity, conservation and display provenance."""
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from rdkit import Chem

from perfume_lab.chemistry import analyze_chemistry, write_molecule_svgs
from perfume_lab.pipeline import run


ROOT = Path(__file__).resolve().parents[1]


class ChemistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = analyze_chemistry(ROOT)

    def copy_inputs(self, destination):
        root = Path(destination)
        shutil.copytree(ROOT / "data", root / "data")
        return root

    def edit_curated(self, root, mutate):
        path = root / "data/curated/chemistry.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_exact_enantiomers_formulas_and_ring_topology(self):
        expected = {"gpp": ("C10H20O7P2", 0, {}),
                    "limonene": ("C10H16", 1, {"6": "R"}),
                    "linalool": ("C10H18O", 0, {"3": "R"})}
        for identifier, (formula, rings, cip) in expected.items():
            with self.subTest(compound=identifier):
                molecule = self.analysis["molecules"][identifier]
                self.assertEqual(molecule["formula"], formula)
                self.assertEqual(molecule["ring_count"], rings)
                self.assertEqual(molecule["cip"], cip)
                self.assertEqual(molecule["carbon_count"], 10)
                self.assertEqual(sorted(a["map_number"] for a in molecule["atoms"]
                                        if a["symbol"] == "C"), list(range(1, 11)))
        # The source diphosphate geometry is E; carbon labels must not alter it.
        source = Chem.MolFromSmiles(self.analysis["molecules"]["gpp"]["smiles"])
        self.assertIn(Chem.BondStereo.STEREOE, [b.GetStereo() for b in source.GetBonds()])

    def test_ring_closure_and_acyclic_allylic_rearrangement_are_distinct(self):
        limonene, linalool = self.analysis["reactions"]
        self.assertEqual([r["atoms"] for r in limonene["carbon_bond_changes"]
                          if r["before"] == 0], [[1, 6]])
        self.assertFalse(any(r["before"] == 0 or r["after"] == 0
                             for r in linalool["carbon_bond_changes"]))
        self.assertEqual(linalool["neutral_equation"]["reactants"], {"gpp": 1, "water": 1})
        for reaction in self.analysis["reactions"]:
            balance = reaction["neutral_species_balance"]
            self.assertEqual(balance["reactant_elements"], balance["product_elements"])
            self.assertEqual(balance["reactant_charge"], balance["product_charge"])

    def test_coordinate_and_svg_outputs_are_traceable_and_stereochemically_consistent(self):
        for record in self.analysis["molecules"].values():
            self.assertIn("atom-0", record["svg"])
            self.assertIn("<svg", record["svg"])
            self.assertIn("not an experimental", record["computed_conformer"]["scope"])
            self.assertTrue(all(math.isfinite(a[axis]) for a in record["atoms"] for axis in ("x", "y", "z")))
            x0, y0, width, height = map(float, ET.fromstring(record["svg"]).attrib["viewBox"].split())
            for atom in record["atoms"]:
                position = atom["svg_position"]
                self.assertTrue(all(math.isfinite(position[axis]) for axis in ("x", "y")))
                self.assertTrue(x0 <= position["x"] <= x0 + width)
                self.assertTrue(y0 <= position["y"] <= y0 + height)
            # Re-infer stereochemistry from the generated heavy-atom coordinates.
            molecule = Chem.MolFromSmiles(record["mapped_smiles"])
            for atom in molecule.GetAtoms():
                atom.SetAtomMapNum(0)
            conformer = Chem.Conformer(molecule.GetNumAtoms())
            for atom in record["atoms"]:
                conformer.SetAtomPosition(atom["index"], (atom["x"], atom["y"], atom["z"]))
            molecule.AddConformer(conformer)
            Chem.AssignAtomChiralTagsFromStructure(molecule, replaceExistingTags=True)
            Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
            actual = {str(record["atoms"][a.GetIdx()]["map_number"]): a.GetProp("_CIPCode")
                      for a in molecule.GetAtoms() if a.GetAtomicNum() == 6 and a.HasProp("_CIPCode")}
            self.assertEqual(actual, record["cip"])

    def test_fixed_seed_reproduces_display_coordinates(self):
        repeated = analyze_chemistry(ROOT)
        for identifier, record in self.analysis["molecules"].items():
            self.assertEqual(record["atoms"], repeated["molecules"][identifier]["atoms"])

    def test_opposite_enantiomer_is_rejected_even_with_same_formula(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_inputs(temp)
            def mutate(data):
                entry = data["compounds"]["limonene"]
                entry["mapped_smiles"] = entry["mapped_smiles"].replace("@@H:6", "@H:6")
            self.edit_curated(root, mutate)
            with self.assertRaisesRegex(ValueError, "stereochemistry differs"):
                analyze_chemistry(root)

    def test_duplicate_carbon_lineage_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_inputs(temp)
            def mutate(data):
                entry = data["compounds"]["linalool"]
                entry["mapped_smiles"] = entry["mapped_smiles"].replace(":10]", ":8]")
            self.edit_curated(root, mutate)
            with self.assertRaisesRegex(ValueError, "each label 1–10 exactly once"):
                analyze_chemistry(root)

    def test_omitting_water_cannot_pass_full_balance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_inputs(temp)
            self.edit_curated(root, lambda data: data["reactions"][1]["neutral_equation"]["reactants"].pop("water"))
            with self.assertRaisesRegex(ValueError, "Unbalanced neutral-species equation"):
                analyze_chemistry(root)

    def test_wrong_ring_closure_cannot_pass_map_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_inputs(temp)
            def mutate(data):
                data["reactions"][0]["expected_carbon_bond_changes"][0]["atoms"] = [1, 5]
            self.edit_curated(root, mutate)
            with self.assertRaisesRegex(ValueError, "Carbon bond-change mismatch"):
                analyze_chemistry(root)

    def test_source_byte_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_inputs(temp)
            path = root / "data/sources/r-limonene.pubchem.json"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                analyze_chemistry(root)

    def test_drawings_export_after_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = write_molecule_svgs(ROOT, Path(temp))
            self.assertEqual(set(paths), {"gpp", "limonene", "linalool"})
            for identifier, path in paths.items():
                self.assertEqual(Path(path).read_bytes(),
                                 self.analysis["molecules"][identifier]["svg"].encode("utf-8"))

    def test_pipeline_svg_bytes_match_embedded_drawings(self):
        with tempfile.TemporaryDirectory() as temp:
            output = run(ROOT, Path(temp) / "results")
            analysis = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
            for identifier, molecule in analysis["chemistry"]["molecules"].items():
                with self.subTest(compound=identifier):
                    self.assertEqual((output / "molecules" / f"{identifier}.svg").read_bytes(),
                                     molecule["svg"].encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
