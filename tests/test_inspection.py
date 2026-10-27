"""Check molecular-viewer interoperability and protect recorded inputs."""
import json
from pathlib import Path
import tempfile
import unittest

from rdkit import Chem
from perfume_lab.inspection import export_bundle, verify_bundle
from perfume_lab.io import sha256

ROOT = Path(__file__).resolve().parents[1]


class MolecularInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "molecules"
        export_bundle(ROOT, self.output)

    def test_export_roundtrip_and_carbon_maps(self):
        self.assertTrue(verify_bundle(ROOT, self.output)["verified"])
        for name in ("gpp", "limonene", "linalool"):
            model = next(Chem.SDMolSupplier(str(self.output / f"{name}.sdf"), removeHs=False))
            self.assertEqual(sorted(a.GetAtomMapNum() for a in model.GetAtoms() if a.GetAtomicNum() == 6), list(range(1, 11)))

    def test_existing_destination_is_preserved(self):
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        with self.assertRaisesRegex(ValueError, "new output"):
            export_bundle(ROOT, self.output)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_tampered_map_rejected_even_with_updated_hash(self):
        path = self.output / "limonene.sdf"
        model = next(Chem.SDMolSupplier(str(path), removeHs=False))
        model.GetAtomWithIdx(0).SetAtomMapNum(99)
        with Chem.SDWriter(str(path)) as writer:
            writer.write(model)
        receipt = json.loads((self.output / "receipt.json").read_text(encoding="utf-8"))
        receipt["molecules"]["limonene"]["sha256"] = sha256(path)
        (self.output / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "carbon map"):
            verify_bundle(ROOT, self.output)

    def test_changed_coordinates_rejected_even_with_updated_hash(self):
        path = self.output / "linalool.sdf"
        model = next(Chem.SDMolSupplier(str(path), removeHs=False))
        point = model.GetConformer().GetAtomPosition(0)
        point.x += 1
        model.GetConformer().SetAtomPosition(0, point)
        with Chem.SDWriter(str(path)) as writer:
            writer.write(model)
        receipt = json.loads((self.output / "receipt.json").read_text(encoding="utf-8"))
        receipt["molecules"]["linalool"]["sha256"] = sha256(path)
        (self.output / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "coordinates"):
            verify_bundle(ROOT, self.output)


if __name__ == "__main__":
    unittest.main()
