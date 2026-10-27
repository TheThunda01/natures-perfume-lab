"""Validate curated chemistry against pinned compound records and draw it.

Carbon labels encode one declared atom correspondence. They are not a mechanism
prediction or an experimentally resolved isotope map. Display conformers are
computed molecular illustrations, never experimental or enzyme-bound poses.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D


CONFORMER_SEED = 20261027


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Input path escapes project: {relative}")
    return path


def _mol(smiles: str, label: str):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid molecular structure: {label}")
    Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
    return molecule


def _canonical_without_maps(molecule):
    plain = Chem.Mol(molecule)
    for atom in plain.GetAtoms():
        atom.SetAtomMapNum(0)
    Chem.AssignStereochemistry(plain, cleanIt=True, force=True)
    return Chem.MolToSmiles(plain, canonical=True, isomericSmiles=True)


def _physical_stereochemistry(molecule):
    """Calculate CIP priorities without arbitrary atom-map numbers affecting rank."""
    plain = Chem.Mol(molecule)
    for atom in plain.GetAtoms():
        atom.SetAtomMapNum(0)
    Chem.AssignStereochemistry(plain, cleanIt=True, force=True)
    return plain


def carbon_bonds(molecule) -> list[dict]:
    """Return the carbon-only graph using persistent lineage labels."""
    result = []
    for bond in molecule.GetBonds():
        a, b = bond.GetBeginAtom(), bond.GetEndAtom()
        if a.GetSymbol() == b.GetSymbol() == "C":
            result.append({"atoms": sorted([a.GetAtomMapNum(), b.GetAtomMapNum()]),
                           "order": bond.GetBondTypeAsDouble()})
    return sorted(result, key=lambda item: item["atoms"])


def carbon_bond_changes(reactant, product) -> list[dict]:
    before = {tuple(row["atoms"]): row["order"] for row in carbon_bonds(reactant)}
    after = {tuple(row["atoms"]): row["order"] for row in carbon_bonds(product)}
    return [{"atoms": list(pair), "before": before.get(pair, 0.0),
             "after": after.get(pair, 0.0)}
            for pair in sorted(before.keys() | after.keys())
            if before.get(pair, 0.0) != after.get(pair, 0.0)]


def _elements(molecule) -> Counter:
    # AddHs turns both implicit and bracket-declared H counts into atoms.
    return Counter(atom.GetSymbol() for atom in Chem.AddHs(molecule).GetAtoms())


def _equation_balance(equation, molecules):
    sides = []
    for side in ("reactants", "products"):
        elements, charge = Counter(), 0
        for identifier, coefficient in equation[side].items():
            if type(coefficient) is not int or coefficient <= 0:
                raise ValueError("Stoichiometric coefficients must be positive integers")
            molecule = molecules[identifier]
            for element, count in _elements(molecule).items():
                elements[element] += coefficient * count
            charge += coefficient * Chem.GetFormalCharge(molecule)
        sides.append((dict(sorted(elements.items())), charge))
    balanced = sides[0] == sides[1]
    if not balanced:
        raise ValueError(f"Unbalanced neutral-species equation: {equation['text']}")
    return {"balanced": True, "reactant_elements": sides[0][0],
            "product_elements": sides[1][0], "reactant_charge": sides[0][1],
            "product_charge": sides[1][1]}


def _validate(root: Path):
    curated = _read_json(root / "data/curated/chemistry.json")
    source_manifest = _read_json(_inside(root, curated["source_manifest"]))
    if curated.get("schema_version") != 1 or source_manifest.get("schema_version") != 1:
        raise ValueError("Unsupported chemistry schema")
    records = {}
    for source in source_manifest["sources"]:
        if source["id"] in records:
            raise ValueError("Duplicate compound source identifier")
        path = _inside(root, source["path"])
        raw = path.read_bytes()
        if len(raw) != source["bytes"] or hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError(f"Compound source fingerprint mismatch: {source['id']}")
        properties = _read_json(path)["PropertyTable"]["Properties"]
        if len(properties) != 1 or properties[0]["CID"] != source["cid"]:
            raise ValueError("Compound source identity mismatch")
        records[source["id"]] = properties[0]
    if set(curated["compounds"]) != {"gpp", "limonene", "linalool"}:
        raise ValueError("Expected GPP and the two declared products")
    if set(curated["compounds"]) & set(curated["auxiliary_compounds"]):
        raise ValueError("Duplicate molecular identifier")
    molecules = {}
    for identifier, entry in {**curated["compounds"], **curated["auxiliary_compounds"]}.items():
        molecule = _mol(entry.get("mapped_smiles", entry.get("smiles")), identifier)
        source = records[entry["source_id"]]
        source_mol = _mol(source["SMILES"], identifier + " source")
        if _canonical_without_maps(molecule) != _canonical_without_maps(source_mol):
            raise ValueError(f"Curated structure/stereochemistry differs from source: {identifier}")
        formula = rdMolDescriptors.CalcMolFormula(molecule)
        if formula != entry["expected_formula"] or formula != source["MolecularFormula"]:
            raise ValueError(f"Molecular formula mismatch: {identifier}")
        if Chem.MolToInchiKey(molecule) != source["InChIKey"]:
            raise ValueError(f"InChIKey mismatch: {identifier}")
        if identifier in curated["compounds"]:
            carbons = [atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 6]
            labels = [atom.GetAtomMapNum() for atom in carbons]
            if len(carbons) != entry["expected_carbon_count"] or sorted(labels) != list(range(1, 11)):
                raise ValueError(f"Carbon map must contain each label 1–10 exactly once: {identifier}")
            if any(atom.GetAtomMapNum() for atom in molecule.GetAtoms() if atom.GetAtomicNum() != 6):
                raise ValueError("Only carbon lineage is mapped in this curation")
            stereo_mol = _physical_stereochemistry(molecule)
            cip = {str(molecule.GetAtomWithIdx(atom.GetIdx()).GetAtomMapNum()): atom.GetProp("_CIPCode")
                   for atom in stereo_mol.GetAtoms() if atom.HasProp("_CIPCode")}
            if cip != entry["expected_cip"]:
                raise ValueError(f"CIP stereochemistry mismatch: {identifier}")
            atom_ids = {atom.GetAtomMapNum(): atom.GetIdx() for atom in carbons}
            for declared in entry["expected_double_bond_stereo"]:
                a, b = declared["atoms"]
                bond = stereo_mol.GetBondBetweenAtoms(atom_ids[a], atom_ids[b])
                if bond is None or str(bond.GetStereo()) != declared["stereo"]:
                    raise ValueError(f"Double-bond stereochemistry mismatch: {identifier}")
        molecules[identifier] = molecule
    if len(curated["reactions"]) != 2 or len({r["id"] for r in curated["reactions"]}) != 2:
        raise ValueError("Expected two uniquely identified reaction branches")
    reaction_checks = {}
    for reaction in curated["reactions"]:
        changes = carbon_bond_changes(molecules[reaction["substrate_id"]], molecules[reaction["product_id"]])
        if changes != reaction["expected_carbon_bond_changes"]:
            raise ValueError(f"Carbon bond-change mismatch: {reaction['id']}")
        reaction_checks[reaction["id"]] = {"carbon_bond_changes": changes,
            "neutral_species_balance": _equation_balance(reaction["neutral_equation"], molecules)}
    return curated, source_manifest, molecules, reaction_checks


def _drawing(molecule, title: str) -> tuple[str, list[dict]]:
    """Return the SVG and atom positions from the same drawing coordinate frame."""
    drawing_molecule = Chem.Mol(molecule)
    for atom in drawing_molecule.GetAtoms():
        label = atom.GetAtomMapNum()
        atom.SetAtomMapNum(0)
        if label:
            atom.SetProp("atomNote", f"C{label}")
    Chem.AssignStereochemistry(drawing_molecule, cleanIt=True, force=True)
    AllChem.Compute2DCoords(drawing_molecule)
    drawer = rdMolDraw2D.MolDraw2DSVG(600, 360)
    drawer.drawOptions().clearBackground = False
    drawer.drawOptions().addStereoAnnotation = True
    drawer.drawOptions().includeAtomTags = True
    drawer.DrawMolecule(drawing_molecule, legend=title)
    drawer.FinishDrawing()
    positions = []
    for atom in drawing_molecule.GetAtoms():
        point = drawer.GetDrawCoords(atom.GetIdx())
        if not all(math.isfinite(value) for value in (point.x, point.y)):
            raise ValueError("Nonfinite SVG atom coordinate")
        positions.append({"x": round(point.x, 6), "y": round(point.y, 6)})
    return drawer.GetDrawingText(), positions


def _conformer(molecule):
    with_hydrogens = Chem.AddHs(molecule)
    params = AllChem.ETKDGv3()
    params.randomSeed = CONFORMER_SEED
    params.numThreads = 1
    params.enforceChirality = True
    if AllChem.EmbedMolecule(with_hydrogens, params) != 0:
        raise ValueError("Could not generate a display conformer")
    optimization = {"force_field": None, "converged": None}
    if AllChem.MMFFHasAllMoleculeParams(with_hydrogens):
        status = AllChem.MMFFOptimizeMolecule(with_hydrogens, mmffVariant="MMFF94", maxIters=500)
        optimization = {"force_field": "MMFF94", "converged": status == 0,
                        "maximum_iterations": 500}
    coordinates = with_hydrogens.GetConformer()
    atoms = []
    for atom in molecule.GetAtoms():
        point = coordinates.GetAtomPosition(atom.GetIdx())
        if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
            raise ValueError("Nonfinite display coordinate")
        atoms.append({"index": atom.GetIdx(), "symbol": atom.GetSymbol(),
                      "x": round(point.x, 6), "y": round(point.y, 6), "z": round(point.z, 6),
                      "map_number": atom.GetAtomMapNum() or None})
    return atoms, {"method": "RDKit ETKDGv3", "random_seed": CONFORMER_SEED,
                   "optimization": optimization, "coordinate_units": "angstrom",
                   "scope": "Computed display conformer; not an experimental, enzyme-bound, preferred-solution or transition-state structure."}


def analyze_chemistry(root: Path) -> dict:
    """Return validated molecules, SVGs, computed 3D coordinates and net maps."""
    root = Path(root)
    curated, manifest, molecules, checks = _validate(root)
    output = {}
    for identifier, entry in curated["compounds"].items():
        molecule = molecules[identifier]
        atoms, conformer = _conformer(molecule)
        svg, svg_positions = _drawing(molecule, entry["name"])
        for atom in atoms:
            atom["svg_position"] = svg_positions[atom["index"]]
        source = next(item for item in manifest["sources"] if item["id"] == entry["source_id"])
        output[identifier] = {"id": identifier, "name": entry["name"],
            "formula": rdMolDescriptors.CalcMolFormula(molecule),
            "smiles": _canonical_without_maps(molecule), "mapped_smiles": entry["mapped_smiles"],
            "carbon_count": sum(atom.GetAtomicNum() == 6 for atom in molecule.GetAtoms()),
            "ring_count": rdMolDescriptors.CalcNumRings(molecule),
            "formal_charge": Chem.GetFormalCharge(molecule), "cip": entry["expected_cip"],
            "carbon_bonds": carbon_bonds(molecule), "svg": svg,
            "atoms": atoms, "bonds": [{"begin": b.GetBeginAtomIdx(), "end": b.GetEndAtomIdx(),
                                         "order": b.GetBondTypeAsDouble()} for b in molecule.GetBonds()],
            "computed_conformer": conformer, "representation": entry["representation"],
            "source": {"id": source["id"], "cid": source["cid"], "url": source["record_url"],
                       "sha256": source["sha256"]}}
    reactions = [{**reaction, **checks[reaction["id"]],
                  "carbon_balance": {"reactant_carbons": 10, "product_carbons": 10,
                                     "complete_lineage_labels": list(range(1, 11))}}
                 for reaction in curated["reactions"]]
    return {"schema_version": 1, "scope": curated["scope"], "numbering": curated["numbering"],
            "protonation_note": curated["protonation_note"], "molecules": output,
            "reactions": reactions, "sources": manifest["sources"],
            "validation": {"source_records_checked": len(manifest["sources"]),
                           "carbon_maps_complete": True, "neutral_equations_balanced": True,
                           "source_graphs_and_stereochemistry_match": True},
            "rdkit_version": rdBase.rdkitVersion}


def write_molecule_svgs(root: Path, output_dir: Path) -> dict[str, str]:
    """Write numbered molecule drawings after validating all chemical inputs."""
    curated, _, molecules, _ = _validate(Path(root))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for identifier, entry in curated["compounds"].items():
        path = output_dir / f"{identifier}.svg"
        svg, _ = _drawing(molecules[identifier], entry["name"])
        path.write_text(svg, encoding="utf-8", newline="\n")
        paths[identifier] = str(path)
    return paths
