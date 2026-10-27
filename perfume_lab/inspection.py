"""Export and check the existing computed illustrations as molecular-viewer files."""
from __future__ import annotations

import io
import math
from pathlib import Path
import tempfile

from rdkit import Chem, rdBase
from rdkit.Chem import AllChem

from .chemistry import analyze_chemistry, _canonical_without_maps
from .io import read_json, sha256, verify_sources, write_json

IDS = ("gpp", "limonene", "linalool")
SCOPE = "Two-dimensional structure layout; not an experimental or computed three-dimensional conformation."


def _model(entry):
    molecule = Chem.MolFromSmiles(entry["mapped_smiles"])
    AllChem.Compute2DCoords(molecule)
    molecule.SetProp("_Name", entry["name"])
    for key, value in {
        "compound_id": entry["id"], "source_cid": str(entry["source"]["cid"]),
        "source_url": entry["source"]["url"], "source_sha256": entry["source"]["sha256"],
        "coordinate_units": "drawing units", "coordinate_scope": SCOPE,
        "carbon_labels": "Atom-map numbers 1-10 are the curated carbon-lineage labels, not IUPAC atom numbers.",
        "protonation": entry["representation"],
    }.items():
        molecule.SetProp(key, value)
    return molecule


def _sdf(entry):
    stream = io.StringIO()
    writer = Chem.SDWriter(stream)
    writer.write(_model(entry))
    writer.flush()
    text = stream.getvalue()
    writer.close()
    # The serialization must preserve physical stereochemistry as well as labels.
    _check_molecule(text.encode("utf-8"), entry)
    return text


def _check_molecule(raw, entry):
    models = list(Chem.ForwardSDMolSupplier(io.BytesIO(raw), removeHs=False, strictParsing=True))
    if len(models) != 1 or models[0] is None:
        raise ValueError("Expected exactly one valid molecule per SDF")
    model = models[0]
    if _canonical_without_maps(model) != entry["smiles"]:
        raise ValueError("Exported graph or physical stereochemistry differs from the source")
    if model.GetNumAtoms() != len(entry["atoms"]):
        raise ValueError("Exported atom count differs from the recorded illustration")
    conformer = model.GetConformer()
    if conformer.Is3D():
        raise ValueError("Export must declare a two-dimensional structure layout")
    expected_model = _model(entry)
    for expected in entry["atoms"]:
        atom = model.GetAtomWithIdx(expected["index"])
        if atom.GetSymbol() != expected["symbol"] or atom.GetAtomMapNum() != (expected["map_number"] or 0):
            raise ValueError("Exported atom identity or carbon map changed")
        point = conformer.GetAtomPosition(atom.GetIdx())
        reference = expected_model.GetConformer().GetAtomPosition(atom.GetIdx())
        for actual, value in zip((point.x, point.y, point.z), (reference.x, reference.y, reference.z)):
            if not math.isfinite(actual) or abs(actual - value) > 0.000051:
                raise ValueError("Exported display coordinates changed beyond SDF rounding")
    expected_model = _model(entry)
    for key in expected_model.GetPropNames():
        if not model.HasProp(key) or model.GetProp(key) != expected_model.GetProp(key):
            raise ValueError(f"Export metadata differs: {key}")


def export_bundle(root: Path, output: Path):
    root, output = Path(root).resolve(), Path(output).absolute()
    if output.exists() or any(p.is_symlink() for p in (output, *output.parents)):
        raise ValueError("Choose a new output directory without symlinks")
    if output.resolve().is_relative_to(root / "data"):
        raise ValueError("Output must be outside source data")
    verify_sources(root)
    chemistry = analyze_chemistry(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".molecule_export_", dir=output.parent) as temporary:
        stage = Path(temporary) / "bundle"
        stage.mkdir()
        for identifier in IDS:
            (stage / f"{identifier}.sdf").write_text(_sdf(chemistry["molecules"][identifier]), encoding="utf-8", newline="\n")
        receipt = {
            "schema_version": 1, "rdkit_version": rdBase.rdkitVersion, "scope": SCOPE,
            "source_manifest_sha256": sha256(root / "data/provenance.json"),
            "curation_sha256": sha256(root / "data/curated/chemistry.json"),
            "molecules": {identifier: {"source": chemistry["molecules"][identifier]["source"],
                "layout": {"method": "RDKit Compute2DCoords", "scope": SCOPE},
                "sha256": sha256(stage / f"{identifier}.sdf")} for identifier in IDS},
        }
        write_json(stage / "receipt.json", receipt)
        if output.exists() or output.is_symlink():
            raise ValueError("Destination appeared during export; no files replaced")
        stage.rename(output)
    return receipt


def verify_bundle(root: Path, bundle: Path):
    root, bundle = Path(root).resolve(), Path(bundle)
    names = {f"{identifier}.sdf" for identifier in IDS} | {"receipt.json"}
    if not bundle.is_dir() or bundle.is_symlink():
        raise ValueError("Bundle must be a real directory")
    if {p.name for p in bundle.iterdir()} - {"README.md"} != names:
        raise ValueError("Bundle must contain the three declared SDF files and receipt")
    if any((bundle / name).is_symlink() or not (bundle / name).is_file() for name in names):
        raise ValueError("Bundle members must be regular files")
    verify_sources(root)
    chemistry = analyze_chemistry(root)
    receipt = read_json(bundle / "receipt.json")
    if receipt.get("schema_version") != 1 or receipt.get("scope") != SCOPE:
        raise ValueError("Unsupported bundle or coordinate scope")
    if receipt.get("rdkit_version") != rdBase.rdkitVersion:
        raise ValueError("Use the recorded RDKit version to verify drawing coordinates")
    for field, relative in (("source_manifest_sha256", "data/provenance.json"), ("curation_sha256", "data/curated/chemistry.json")):
        if receipt.get(field) != sha256(root / relative):
            raise ValueError("Bundle input fingerprint differs from current pinned inputs")
    if set(receipt.get("molecules", {})) != set(IDS):
        raise ValueError("Receipt must identify all three compounds")
    for identifier in IDS:
        entry = chemistry["molecules"][identifier]
        expected = {"source": entry["source"], "layout": {"method": "RDKit Compute2DCoords", "scope": SCOPE},
                    "sha256": sha256(bundle / f"{identifier}.sdf")}
        if receipt["molecules"][identifier] != expected:
            raise ValueError("Molecular file fingerprint or provenance differs")
        _check_molecule((bundle / f"{identifier}.sdf").read_bytes(), entry)
    return {"verified": True, "molecules": 3, "carbon_labels_per_molecule": 10,
            "checks": ["source fingerprints", "graph and physical stereochemistry", "carbon atom maps", "display coordinates", "provenance fields"], "scope": SCOPE}
