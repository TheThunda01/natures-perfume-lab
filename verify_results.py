"""Independently check saved results against pinned source and curated records.

This module does not import or run the result generator. Verification checks
computational consistency, not source authenticity or experimental validity.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys


ROOT = Path(__file__).resolve().parent
MAX_FILE_BYTES = 20 * 1024 * 1024
NUMERIC_TOLERANCE = 1e-10
RESULT_FILES = {
    "analysis.json", "alignment.fasta", "residue_alignment.csv", "chemical_summary.csv",
    "report.md", "molecules/gpp.svg", "molecules/limonene.svg", "molecules/linalool.svg",
    "figures/sequence_identity.svg", "figures/reaction_paths.svg",
}


class VerificationError(ValueError):
    """An input or result fails the verification contract."""


def strict_json(raw: bytes, name: str):
    """Reject ambiguous objects, nonfinite values, and implicit decoding."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise VerificationError(f"Duplicate JSON key in {name}: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise VerificationError(f"Nonfinite JSON number in {name}: {value}")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                           parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"Invalid UTF-8 JSON in {name}: {error}") from error

    def check_finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise VerificationError(f"Nonfinite JSON number in {name}")
        if isinstance(item, dict):
            for child in item.values():
                check_finite(child)
        elif isinstance(item, list):
            for child in item:
                check_finite(child)

    check_finite(value)
    return value


def regular_bytes(root: Path, relative: str) -> bytes:
    """Read a bounded regular member without traversing a symlink."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise VerificationError(f"Expected a real directory: {root}")
    if not isinstance(relative, str) or "\\" in relative:
        raise VerificationError("Manifest paths must be relative POSIX paths")
    parts = PurePosixPath(relative).parts
    if (not parts or relative != PurePosixPath(relative).as_posix()
            or PurePosixPath(relative).is_absolute()
            or any(part in {".", ".."} for part in parts)):
        raise VerificationError(f"Unsafe member path: {relative!r}")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise VerificationError(f"Symlink member is not allowed: {relative}")
    if not path.is_file():
        raise VerificationError(f"Expected a regular file: {relative}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise VerificationError(f"File exceeds verification limit: {relative}")
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise VerificationError(f"File exceeds verification limit: {relative}")
    return raw


def fingerprint(raw: bytes) -> dict:
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def equal(actual, expected, location: str):
    """Compare JSON types/structure exactly, with bounded float tolerance."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise VerificationError(f"Field set mismatch: {location}")
        for key in expected:
            equal(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise VerificationError(f"List mismatch: {location}")
        for index, (left, right) in enumerate(zip(actual, expected)):
            equal(left, right, f"{location}[{index}]")
    elif type(expected) is float:
        if (type(actual) not in (int, float) or not math.isfinite(actual)
                or not math.isclose(actual, expected, rel_tol=0,
                                    abs_tol=NUMERIC_TOLERANCE)):
            raise VerificationError(f"Numeric mismatch: {location}")
    elif type(actual) is not type(expected) or actual != expected:
        raise VerificationError(f"Value mismatch: {location}")


def aligned_counts(left: str, right: str) -> dict:
    """Count identities and gaps directly from a saved pair of aligned strings."""
    if (not isinstance(left, str) or not isinstance(right, str)
            or not left or len(left) != len(right)
            or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY-]+", left)
            or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY-]+", right)):
        raise VerificationError("Aligned sequences must be equal-length protein strings")
    identities = mismatches = gap_columns = gap_runs = 0
    last_gap = None
    for a, b in zip(left, right):
        if a == b == "-":
            raise VerificationError("An alignment cannot contain a double-gap column")
        gap = "left" if a == "-" else "right" if b == "-" else None
        if gap is not None:
            gap_columns += 1
            gap_runs += gap != last_gap
        else:
            identities += a == b
            mismatches += a != b
        last_gap = gap
    return {"columns": len(left), "identities": identities,
            "mismatches": mismatches, "gap_columns": gap_columns,
            "gap_runs": gap_runs,
            "paired_columns": identities + mismatches}


def independent_global_score(sequence_a: str, sequence_b: str) -> float:
    """Global affine-gap optimum, independently of the alignment generator.

    A length-n gap costs -10 - 0.5*(n-1). The three rolling rows store
    residue-pair, gap-in-B, and gap-in-A terminal states respectively.
    """
    width = len(sequence_b)
    unreachable = float("-inf")
    diagonal = [0.0] + [unreachable] * width
    vertical = [unreachable] * (width + 1)
    horizontal = [unreachable] + [-10.0 - 0.5 * (j - 1) for j in range(1, width + 1)]
    for i, a in enumerate(sequence_a, 1):
        next_diagonal = [unreachable] * (width + 1)
        next_vertical = [-10.0 - 0.5 * (i - 1)] + [unreachable] * width
        next_horizontal = [unreachable] * (width + 1)
        for j, b in enumerate(sequence_b, 1):
            next_diagonal[j] = max(diagonal[j - 1], vertical[j - 1], horizontal[j - 1]) + (2 if a == b else -1)
            next_vertical[j] = max(diagonal[j] - 10, vertical[j] - 0.5, horizontal[j] - 10)
            next_horizontal[j] = max(next_diagonal[j - 1] - 10, next_vertical[j - 1] - 10, next_horizontal[j - 1] - 0.5)
        diagonal, vertical, horizontal = next_diagonal, next_vertical, next_horizontal
    return max(diagonal[-1], vertical[-1], horizontal[-1])


def verify_comparison(comparison: dict, sequences: dict[str, str]) -> dict:
    if not isinstance(comparison, dict):
        raise VerificationError("sequence_comparison must be an object")
    identifiers = [comparison.get("enzyme_a"), comparison.get("enzyme_b")]
    if (any(not isinstance(value, str) for value in identifiers)
            or len(set(identifiers)) != 2 or set(identifiers) != set(sequences)):
        raise VerificationError("Alignment must compare both selected enzyme identities")
    equal(comparison.get("scoring"),
          {"match": 2.0, "mismatch": -1.0, "open_gap": -10.0, "extend_gap": -0.5},
          "sequence_comparison.scoring")
    a, b = comparison.get("alignment_a"), comparison.get("alignment_b")
    counts = aligned_counts(a, b)
    if a.replace("-", "") != sequences[identifiers[0]] or b.replace("-", "") != sequences[identifiers[1]]:
        raise VerificationError("Saved alignment does not recover the pinned complete sequences")
    if counts["paired_columns"] == 0:
        raise VerificationError("Saved alignment has no paired residues")
    score = (2 * counts["identities"] - counts["mismatches"]
             - 10 * counts["gap_runs"] - 0.5 * (counts["gap_columns"] - counts["gap_runs"]))
    metrics = {
        "alignment_columns": counts["columns"],
        "paired_residues": counts["paired_columns"],
        "matches": counts["identities"], "mismatches": counts["mismatches"],
        "gap_columns": counts["gap_columns"],
        "identity_percent": 100.0 * counts["identities"] / counts["paired_columns"],
        "identity_all_columns_percent": 100.0 * counts["identities"] / counts["columns"],
        "score": float(score),
    }
    for key, expected in metrics.items():
        equal(comparison.get(key), expected, "sequence_comparison." + key)
    if "aligned_length" in comparison:
        equal(comparison["aligned_length"], counts["columns"], "sequence_comparison.aligned_length")
    optimal = independent_global_score(sequences[identifiers[0]], sequences[identifiers[1]])
    equal(float(score), optimal, "independently recomputed optimal global alignment score")
    return metrics


def data_member(data_dir: Path, path: str) -> bytes:
    if not isinstance(path, str) or not path.startswith("data/"):
        raise VerificationError("Source paths must start with data/")
    return regular_bytes(data_dir, path[len("data/"):])


def verify_sources(data_dir: Path) -> tuple[str, dict]:
    from perfume_lab.constants import SOURCE_MANIFEST_SHA256

    raw = regular_bytes(data_dir, "provenance.json")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_MANIFEST_SHA256:
        raise VerificationError("Source manifest differs from the pinned case fingerprint")
    manifest = strict_json(raw, "data/provenance.json")
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise VerificationError("Unsupported source manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise VerificationError("Source manifest needs a nonempty file inventory")
    members = {}
    for item in files:
        if not isinstance(item, dict) or not {"path", "bytes", "sha256"} <= item.keys():
            raise VerificationError("Invalid source inventory record")
        path = item["path"]
        if not isinstance(path, str) or path in members:
            raise VerificationError("Duplicate or invalid source inventory path")
        content = data_member(data_dir, path)
        equal({key: item[key] for key in ("sha256", "bytes")}, fingerprint(content), path + " fingerprint")
        members[path] = content
    return digest, members


def verify_artifacts(results_dir: Path, source_digest: str) -> dict[str, bytes]:
    raw = regular_bytes(results_dir, "manifest.json")
    manifest = strict_json(raw, "results/manifest.json")
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "source_manifest_sha256", "files"}:
        raise VerificationError("Result manifest field set mismatch")
    equal(manifest["schema_version"], 1, "manifest.schema_version")
    equal(manifest["source_manifest_sha256"], source_digest, "manifest.source_manifest_sha256")
    files = manifest["files"]
    if not isinstance(files, list):
        raise VerificationError("Result inventory must be a list")
    blobs = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"}:
            raise VerificationError("Invalid result inventory record")
        path = item["path"]
        if not isinstance(path, str) or path not in RESULT_FILES or path in blobs:
            raise VerificationError("Unexpected or duplicate result inventory path")
        content = regular_bytes(results_dir, path)
        equal({key: item[key] for key in ("sha256", "bytes")}, fingerprint(content), path + " fingerprint")
        blobs[path] = content
    if set(blobs) != RESULT_FILES:
        raise VerificationError("Result manifest does not cover the required artifacts")
    observed = set()
    for path in results_dir.rglob("*"):
        if path.is_symlink():
            raise VerificationError("Result bundle contains a symlink")
        if not path.is_dir():
            observed.add(path.relative_to(results_dir).as_posix())
    if observed != RESULT_FILES | {"manifest.json"}:
        raise VerificationError("Result directory contains missing or unlisted files")
    return blobs


def fasta_records(raw: bytes) -> dict[str, str]:
    records = {}
    name = None
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as error:
        raise VerificationError("FASTA must use ASCII") from error
    for line in lines:
        if line.startswith(">"):
            name = line[1:].split()[0] if line[1:].strip() else ""
            if not name or name in records:
                raise VerificationError("FASTA identifiers must be nonempty and unique")
            records[name] = ""
        elif line:
            if name is None or not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY-]+", line):
                raise VerificationError("Malformed protein FASTA")
            records[name] += line
    if not records or any(not sequence for sequence in records.values()):
        raise VerificationError("FASTA records cannot be empty")
    return records


def csv_rows(raw: bytes, fields: list[str], name: str) -> list[list[str]]:
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True))
    except (UnicodeError, csv.Error) as error:
        raise VerificationError(f"Invalid CSV in {name}: {error}") from error
    if not rows or rows[0] != fields or any(len(row) != len(fields) for row in rows[1:]):
        raise VerificationError(f"CSV schema mismatch: {name}")
    return rows[1:]


def verify_alignment_exports(comparison: dict, blobs: dict):
    expected = {comparison["enzyme_a"]: comparison["alignment_a"],
                comparison["enzyme_b"]: comparison["alignment_b"]}
    equal(fasta_records(blobs["alignment.fasta"]), expected, "alignment.fasta")
    expected_rows = []
    a_position = b_position = 0
    for column, (a, b) in enumerate(zip(comparison["alignment_a"], comparison["alignment_b"]), 1):
        a_position += a != "-"
        b_position += b != "-"
        expected_rows.append([str(column), str(a_position) if a != "-" else "", a,
                              str(b_position) if b != "-" else "", b])
    rows = csv_rows(blobs["residue_alignment.csv"],
                    ["column", "a_position", "a_residue", "b_position", "b_residue"],
                    "residue_alignment.csv")
    equal(rows, expected_rows, "residue_alignment.csv")


def verify_web_payload(web_dir: Path, analysis: dict):
    text = regular_bytes(web_dir, "data.js").decode("utf-8").strip()
    prefix = "window.PERFUME_DATA = "
    if not text.startswith(prefix) or not text.endswith(";"):
        raise VerificationError("Web payload must contain only the PERFUME_DATA assignment")
    payload = strict_json(text[len(prefix):-1].encode("utf-8"), "web/data.js")
    # JSON serialization preserves scalar types, unlike Python's bool/int equality.
    if json.dumps(payload, sort_keys=True, ensure_ascii=False) != json.dumps(analysis, sort_keys=True, ensure_ascii=False):
        raise VerificationError("Web payload differs from the verified analysis")


def verify_enzymes(enzymes: list, sources: dict) -> dict[str, str]:
    curated = strict_json(sources["data/curated/enzymes.json"], "curated enzymes")
    records = curated["enzymes"]
    if (not isinstance(enzymes, list) or not isinstance(records, list)
            or len(enzymes) != 2 or len(records) != 2):
        raise VerificationError("The case requires exactly two curated enzyme records")
    if {record["id"] for record in records} != {"limonene_synthase", "linalool_synthase"}:
        raise VerificationError("Unexpected curated enzyme identities")
    sequences = {}
    for actual, record in zip(enzymes, records):
        if not isinstance(actual, dict):
            raise VerificationError("Enzyme result must be an object")
        equal(actual, record, "enzyme." + record["id"])
        source_files = record["source_files"]
        annotation = strict_json(sources[source_files["uniprot_json"]], "UniProt record")
        accession = annotation["primaryAccession"]
        sequence = annotation["sequence"]["value"]
        if not re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", sequence):
            raise VerificationError("Pinned source sequence contains unsupported residues")
        equal(len(sequence), annotation["sequence"]["length"], "UniProt sequence length")
        equal(record["sequence_length"], len(sequence), "curated sequence length")
        fasta = fasta_records(sources[source_files["fasta"]])
        if len(fasta) != 1:
            raise VerificationError("Pinned FASTA must contain one selected sequence")
        identifier, fasta_sequence = next(iter(fasta.items()))
        fields = identifier.split("|")
        if len(fields) != 3 or fields[1] != accession or fasta_sequence != sequence:
            raise VerificationError("Pinned UniProt JSON and FASTA disagree")
        expected = {
            "id": record["id"],
            "name": annotation["proteinDescription"]["recommendedName"]["fullName"]["value"],
            "organism": annotation["organism"]["scientificName"],
            "accession": accession, "sequence": sequence,
            "product_id": record["product_id"],
            "reviewed": annotation["entryType"] == "UniProtKB reviewed (Swiss-Prot)",
        }
        for key in ("name", "organism", "accession", "sequence", "reviewed"):
            equal(record[key], expected[key], "curated enzyme." + key)
        equal(record["sequence_sha256"], hashlib.sha256(sequence.encode("ascii")).hexdigest(), "enzyme sequence digest")
        for motif in record["annotated_motifs"]:
            start, end = motif["start"], motif["end"]
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(sequence):
                raise VerificationError("Motif positions are outside the canonical sequence")
            equal(motif["sequence"], sequence[start - 1:end], "annotated motif residues")
        sequences[record["id"]] = sequence
    return sequences


def independent_molecule(record: dict, source: dict, raw: bytes, mapped: bool) -> dict:
    """Parse curated and source chemical graphs without generator functions."""
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors

    smiles = record["mapped_smiles"] if mapped else record["smiles"]
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None or len(Chem.GetMolFrags(molecule)) != 1:
        raise VerificationError("Curated compound must be one valid molecular graph")
    Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
    formula = rdMolDescriptors.CalcMolFormula(molecule)
    equal(formula, record["expected_formula"], record["id"] + " formula")
    properties = strict_json(raw, "PubChem source")["PropertyTable"]["Properties"]
    if not isinstance(properties, list) or len(properties) != 1:
        raise VerificationError("Expected exactly one PubChem compound")
    properties = properties[0]
    equal(properties["CID"], source["cid"], record["id"] + " PubChem identity")
    equal(formula, properties["MolecularFormula"], record["id"] + " PubChem formula")
    source_molecule = Chem.MolFromSmiles(properties["SMILES"])
    if source_molecule is None:
        raise VerificationError("Invalid PubChem molecular graph")
    unlabelled = Chem.Mol(molecule)
    for atom in unlabelled.GetAtoms():
        atom.SetAtomMapNum(0)
    # Atom-map labels are lineage metadata, not chemical priority. Clear them
    # before assigning CIP/E/Z while retaining atom and bond index correspondence.
    Chem.AssignStereochemistry(unlabelled, cleanIt=True, force=True)
    canonical = Chem.MolToSmiles(unlabelled, canonical=True, isomericSmiles=True)
    if canonical != Chem.MolToSmiles(source_molecule, canonical=True, isomericSmiles=True):
        raise VerificationError("Mapped molecule differs from pinned source graph or stereochemistry")
    equal(Chem.MolToInchiKey(unlabelled), properties["InChIKey"], record["id"] + " InChIKey")
    carbons = [atom for atom in molecule.GetAtoms() if atom.GetAtomicNum() == 6]
    carbon_maps = [atom.GetAtomMapNum() for atom in carbons]
    if mapped:
        if sorted(carbon_maps) != list(range(1, 11)):
            raise VerificationError("Carbon atom maps must contain each lineage label 1 through 10 exactly once")
        if any(atom.GetAtomMapNum() for atom in molecule.GetAtoms() if atom.GetAtomicNum() != 6):
            raise VerificationError("This case maps carbon atoms only")
        equal(len(carbons), record["expected_carbon_count"], record["id"] + " carbon count")
    cip = {str(atom.GetAtomMapNum()): unlabelled.GetAtomWithIdx(atom.GetIdx()).GetProp("_CIPCode")
           for atom in carbons if unlabelled.GetAtomWithIdx(atom.GetIdx()).HasProp("_CIPCode")}
    carbon_bonds = {}
    stereo = []
    for bond in molecule.GetBonds():
        left, right = bond.GetBeginAtom(), bond.GetEndAtom()
        if left.GetAtomicNum() == right.GetAtomicNum() == 6:
            atoms = tuple(sorted((left.GetAtomMapNum(), right.GetAtomMapNum())))
            carbon_bonds[atoms] = bond.GetBondTypeAsDouble()
            physical_stereo = str(unlabelled.GetBondWithIdx(bond.GetIdx()).GetStereo())
            if physical_stereo not in {"STEREONONE", "STEREOANY"}:
                stereo.append({"atoms": list(atoms), "stereo": physical_stereo})
    if mapped:
        equal(cip, record["expected_cip"], record["id"] + " absolute stereochemistry")
        equal(sorted(stereo, key=lambda item: item["atoms"]), record["expected_double_bond_stereo"],
              record["id"] + " double-bond stereochemistry")
    elements = dict(Counter(atom.GetSymbol() for atom in Chem.AddHs(molecule).GetAtoms()))
    return {"molecule": molecule, "formula": formula, "canonical_smiles": canonical,
            "carbon_count": len(carbons), "ring_count": molecule.GetRingInfo().NumRings(),
            "cip": cip, "double_bond_stereo": stereo, "carbon_bonds": carbon_bonds,
            "elements": elements, "formal_charge": Chem.GetFormalCharge(molecule),
            "source": source, "properties": properties}


def verify_chemistry(chemistry: dict, sources: dict, blobs: dict) -> dict:
    curated = strict_json(sources["data/curated/chemistry.json"], "curated chemistry")
    source_manifest = strict_json(sources[curated["source_manifest"]], "compound sources")
    if not isinstance(chemistry, dict) or set(chemistry) != {
            "schema_version", "scope", "numbering", "protonation_note", "molecules",
            "reactions", "sources", "validation", "rdkit_version"}:
        raise VerificationError("Chemistry result field set mismatch")
    equal(chemistry["schema_version"], 1, "chemistry.schema_version")
    for key in ("scope", "numbering", "protonation_note"):
        equal(chemistry[key], curated[key], "chemistry." + key)
    equal(chemistry["sources"], source_manifest["sources"], "chemistry.sources")
    if not isinstance(chemistry["rdkit_version"], str) or not chemistry["rdkit_version"]:
        raise VerificationError("Chemistry runtime version must be a nonempty string")
    source_records = {}
    for source in source_manifest["sources"]:
        if source["id"] in source_records:
            raise VerificationError("Duplicate chemical source identity")
        source_records[source["id"]] = source
        equal({key: source[key] for key in ("sha256", "bytes")},
              fingerprint(sources[source["path"]]), "compound source fingerprint")
    all_curated = {**curated["compounds"], **curated["auxiliary_compounds"]}
    if len(all_curated) != len(curated["compounds"]) + len(curated["auxiliary_compounds"]):
        raise VerificationError("Duplicate primary/auxiliary compound identity")
    facts = {}
    for identifier, record in all_curated.items():
        equal(record["id"], identifier, "curated compound identity")
        source = source_records[record["source_id"]]
        facts[identifier] = independent_molecule(record, source, sources[source["path"]],
                                                  identifier in curated["compounds"])
    if not isinstance(chemistry["molecules"], dict) or set(chemistry["molecules"]) != set(curated["compounds"]):
        raise VerificationError("Result must contain exactly the curated primary compounds")
    for identifier, record in curated["compounds"].items():
        actual = chemistry["molecules"][identifier]
        fact = facts[identifier]
        mol = fact["molecule"]
        expected = {"id": identifier, "name": record["name"],
                    "formula": fact["formula"], "smiles": fact["canonical_smiles"],
                    "mapped_smiles": record["mapped_smiles"],
                    "carbon_count": fact["carbon_count"], "ring_count": fact["ring_count"],
                    "formal_charge": fact["formal_charge"], "cip": fact["cip"],
                    "carbon_bonds": [{"atoms": list(pair), "order": order}
                                     for pair, order in sorted(fact["carbon_bonds"].items())],
                    "bonds": [{"begin": bond.GetBeginAtomIdx(), "end": bond.GetEndAtomIdx(),
                               "order": bond.GetBondTypeAsDouble()} for bond in mol.GetBonds()],
                    "representation": record["representation"],
                    "source": {"id": fact["source"]["id"], "cid": fact["source"]["cid"],
                               "url": fact["source"]["record_url"], "sha256": fact["source"]["sha256"]},
                    "svg": blobs["molecules/" + identifier + ".svg"].decode("utf-8")}
        if not isinstance(actual, dict) or set(actual) != set(expected) | {"atoms", "computed_conformer"}:
            raise VerificationError("Molecule result field set mismatch: " + identifier)
        for key, value in expected.items():
            equal(actual[key], value, "molecule." + identifier + "." + key)
        atoms = actual["atoms"]
        if not isinstance(atoms, list) or len(atoms) != mol.GetNumAtoms():
            raise VerificationError("Display atoms do not cover the molecular graph")
        for atom, displayed in zip(mol.GetAtoms(), atoms):
            if not isinstance(displayed, dict) or set(displayed) != {"index", "symbol", "map_number", "x", "y", "z", "svg_position"}:
                raise VerificationError("Display atom field set mismatch")
            equal(displayed["index"], atom.GetIdx(), "display atom index")
            equal(displayed["symbol"], atom.GetSymbol(), "display atom element")
            equal(displayed["map_number"], atom.GetAtomMapNum() or None, "display atom lineage")
            if any(type(displayed[key]) not in (float, int) or not math.isfinite(displayed[key])
                   for key in ("x", "y", "z")):
                raise VerificationError("Display coordinates must be finite numbers")
            svg_position = displayed["svg_position"]
            if not isinstance(svg_position, dict) or set(svg_position) != {"x", "y"}:
                raise VerificationError("SVG position must contain x and y")
            for axis, bound in (("x", 600), ("y", 360)):
                coordinate = svg_position[axis]
                if type(coordinate) not in (float, int) or not math.isfinite(coordinate) or not 0 <= coordinate <= bound:
                    raise VerificationError("SVG position must be finite and inside the 600 by 360 viewBox")
        conformer = actual["computed_conformer"]
        if not isinstance(conformer, dict) or set(conformer) != {"method", "random_seed", "optimization", "coordinate_units", "scope"}:
            raise VerificationError("Computed-conformer metadata field set mismatch")
        equal(conformer["method"], "RDKit ETKDGv3", "conformer method")
        equal(conformer["random_seed"], 20261027, "conformer seed")
        equal(conformer["coordinate_units"], "angstrom", "conformer units")
        equal(conformer["scope"], "Computed display conformer; not an experimental, enzyme-bound, preferred-solution or transition-state structure.", "conformer scope")
        optimization = conformer["optimization"]
        if not isinstance(optimization, dict):
            raise VerificationError("Conformer optimization metadata must be an object")
        if optimization.get("force_field") is None:
            equal(optimization, {"force_field": None, "converged": None}, "conformer optimization")
        elif (set(optimization) != {"force_field", "converged", "maximum_iterations"}
              or optimization["force_field"] != "MMFF94" or type(optimization["converged"]) is not bool
              or type(optimization["maximum_iterations"]) is not int or optimization["maximum_iterations"] != 500):
            raise VerificationError("Unsupported conformer optimization metadata")
    expected_reactions = []
    for reaction in curated["reactions"]:
        before = facts[reaction["substrate_id"]]["carbon_bonds"]
        after = facts[reaction["product_id"]]["carbon_bonds"]
        changes = [{"atoms": list(pair), "before": before.get(pair, 0.0), "after": after.get(pair, 0.0)}
                   for pair in sorted(set(before) | set(after))
                   if before.get(pair, 0.0) != after.get(pair, 0.0)]
        equal(changes, reaction["expected_carbon_bond_changes"], reaction["id"] + " curated bond changes")
        balance = {}
        for side, prefix in (("reactants", "reactant"), ("products", "product")):
            elements = Counter()
            charge = 0
            for identifier, coefficient in reaction["neutral_equation"][side].items():
                if type(coefficient) is not int or coefficient <= 0:
                    raise VerificationError("Equation coefficients must be positive integers")
                elements.update({element: count * coefficient for element, count in facts[identifier]["elements"].items()})
                charge += coefficient * facts[identifier]["formal_charge"]
            balance[prefix + "_elements"] = dict(sorted(elements.items()))
            balance[prefix + "_charge"] = charge
        if (balance["reactant_elements"] != balance["product_elements"]
                or balance["reactant_charge"] != balance["product_charge"]):
            raise VerificationError("Curated neutral reaction is not element/charge balanced")
        balance["balanced"] = True
        expected_reactions.append({**reaction, "carbon_bond_changes": changes,
                                   "neutral_species_balance": balance,
                                   "carbon_balance": {"reactant_carbons": facts[reaction["substrate_id"]]["carbon_count"],
                                                      "product_carbons": facts[reaction["product_id"]]["carbon_count"],
                                                      "complete_lineage_labels": list(range(1, 11))}})
    equal(chemistry["reactions"], expected_reactions, "chemistry.reactions")
    equal(chemistry["validation"], {"source_records_checked": len(source_records),
                                   "carbon_maps_complete": True, "neutral_equations_balanced": True,
                                   "source_graphs_and_stereochemistry_match": True}, "chemistry.validation")
    expected_rows = [[identifier, record["name"], facts[identifier]["formula"],
                      str(facts[identifier]["carbon_count"]), str(facts[identifier]["ring_count"])]
                     for identifier, record in curated["compounds"].items()]
    equal(csv_rows(blobs["chemical_summary.csv"], ["molecule_id", "name", "formula", "carbon_count", "ring_count"],
                   "chemical_summary.csv"), expected_rows, "chemical_summary.csv")
    return {"molecules_checked": len(curated["compounds"]), "source_compounds_checked": len(facts),
            "balanced_reactions_checked": len(expected_reactions)}


def verify_structures(actual: dict, enzymes: list, sources: dict) -> dict:
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict

    three_letter = "ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR".split()
    amino_acids = dict(zip(three_letter, "ACDEFGHIKLMNPQRSTVWY"))
    expected_records = []
    inspected = 0
    for enzyme in enzymes:
        source = enzyme["experimental_structure"]
        if source["status"] != "available":
            expected_records.append({"enzyme_id": enzyme["id"], "status": "not_included",
                                     "note": "No experimental structure is included for this selected enzyme; no cross-enzyme pocket geometry is inferred."})
            continue
        files = source["source_files"]
        structure = MMCIF2Dict(io.StringIO(sources[files["mmcif"]].decode("utf-8")))
        entity = strict_json(sources[files["entity"]], "PDB entity")
        entry = strict_json(sources[files["entry"]], "PDB entry")
        equal(entity["entity_poly"]["pdbx_seq_one_letter_code_can"].replace("\n", ""),
              enzyme["sequence"], "deposited polymer/canonical sequence")
        equal(entry["rcsb_id"].upper(), source["pdb_id"].upper(), "experimental structure identity")
        if source["method"] not in [item["method"] for item in entry["exptl"]]:
            raise VerificationError("Experimental method differs from source")
        if source["resolution_angstrom"] not in entry["rcsb_entry_info"]["resolution_combined"]:
            raise VerificationError("Experimental resolution differs from source")
        chain = source["label_asym_id"]
        residues = {}
        for index, group in enumerate(structure["_atom_site.group_PDB"]):
            if (group != "ATOM" or structure["_atom_site.label_asym_id"][index] != chain
                    or structure["_atom_site.label_atom_id"][index] != "CA"
                    or structure["_atom_site.pdbx_PDB_model_num"][index] != str(source["model"])):
                continue
            position = int(structure["_atom_site.label_seq_id"][index])
            residue = amino_acids.get(structure["_atom_site.label_comp_id"][index])
            if not residue or not 1 <= position <= len(enzyme["sequence"]):
                raise VerificationError("Unrecognized or out-of-range coordinate residue")
            if position in residues and residues[position] != residue:
                raise VerificationError("Conflicting coordinate residue identities")
            if source["sequence_mapping"]["author_and_label_numbering_match"]:
                equal(int(structure["_atom_site.auth_seq_id"][index]), position, "author/label residue numbering")
            residues[position] = residue
        if not residues:
            raise VerificationError("No alpha-carbon residues found for the declared experimental chain")
        mismatches = [{"position": position, "coordinate": residue, "canonical": enzyme["sequence"][position - 1]}
                      for position, residue in sorted(residues.items())
                      if residue != enzyme["sequence"][position - 1]]
        if mismatches:
            raise VerificationError("Experimental coordinate residues differ from the pinned canonical sequence")
        equal(len(residues), source["modeled_residue_count"], "curated modeled residue count")
        unmodeled = [position for position in range(1, len(enzyme["sequence"]) + 1) if position not in residues]
        equal(len(unmodeled), source["deposited_unmodeled_residue_count"], "curated unmodeled reference count")
        expected_records.append({"enzyme_id": enzyme["id"], "status": "experimental", "pdb_id": source["pdb_id"],
                                 "chain": chain, "canonical_length": len(enzyme["sequence"]),
                                 "modeled_alpha_carbon_residues": len(residues),
                                 "unmodeled_reference_positions": unmodeled,
                                 "coordinate_sequence_mismatches": mismatches,
                                 "resolution_angstrom": source["resolution_angstrom"],
                                 "note": "Positions use mmCIF label_seq_id and the documented identity mapping to the deposited canonical reference; this is not a count of residues in the experimental expression construct.",
                                 "source_record": source})
        inspected += 1
    equal(actual, {"records": expected_records, "comparison": "One experimental enzyme structure is inspected; no pairwise enzyme structure comparison is made."},
          "structural_evidence")
    return {"experimental_structures_checked": inspected}


def verify_results(data_dir: Path = ROOT / "data", results_dir: Path = ROOT / "results",
                   web_dir: Path | None = None) -> dict:
    """Check pinned inputs and saved calculations; never generate or write files."""
    data_dir, results_dir = Path(data_dir), Path(results_dir)
    source_digest, sources = verify_sources(data_dir)
    blobs = verify_artifacts(results_dir, source_digest)
    analysis = strict_json(blobs["analysis.json"], "analysis.json")
    if not isinstance(analysis, dict) or set(analysis) != {
            "schema_version", "scope", "source_manifest_sha256", "enzymes",
            "sequence_comparison", "chemistry", "structural_evidence", "software_versions"}:
        raise VerificationError("Analysis result field set mismatch")
    equal(analysis["schema_version"], 1, "analysis.schema_version")
    equal(analysis["source_manifest_sha256"], source_digest, "analysis.source_manifest_sha256")
    equal(analysis["scope"], "A source-backed, descriptive comparison of two known plant scent-enzyme reactions; no odor or activity prediction.", "analysis.scope")
    versions = analysis["software_versions"]
    if (not isinstance(versions, dict) or set(versions) != {"python", "biopython", "numpy", "rdkit", "matplotlib", "Pillow"}
            or any(not isinstance(value, str) or not value for value in versions.values())):
        raise VerificationError("Runtime metadata must contain the six recorded package-version strings")
    sequences = verify_enzymes(analysis["enzymes"], sources)
    metrics = verify_comparison(analysis["sequence_comparison"], sequences)
    verify_alignment_exports(analysis["sequence_comparison"], blobs)
    chemistry = verify_chemistry(analysis["chemistry"], sources, blobs)
    structures = verify_structures(analysis["structural_evidence"], analysis["enzymes"], sources)
    if web_dir is not None:
        verify_web_payload(Path(web_dir), analysis)
    # Catch ordinary changes between the initial reads and completion. These
    # sequential checks are not a filesystem lock or a signed chain of custody.
    final_digest, final_sources = verify_sources(data_dir)
    if final_digest != source_digest or final_sources != sources:
        raise VerificationError("Sources changed during verification")
    final_blobs = verify_artifacts(results_dir, source_digest)
    if final_blobs != blobs:
        raise VerificationError("Results changed during verification")
    return {
        "schema_version": 1, "verified": True,
        "source_manifest_sha256": source_digest,
        "source_files_checked": len(sources), "artifacts_checked": len(blobs),
        "enzyme_lengths": {identifier: len(sequence) for identifier, sequence in sequences.items()},
        "sequence_metrics": metrics, **chemistry, **structures,
        "web_payload_checked": web_dir is not None,
        "artifact_sha256": {path: hashlib.sha256(raw).hexdigest() for path, raw in sorted(blobs.items())},
        "limits": [
            "Checks pinned-case file integrity, sequence/alignment calculations, chemical graphs and declared net equations, and experimental residue coverage.",
            "Uses an independent affine-score recurrence; optimal alignments may tie, so it does not authenticate which optimum a runtime returned first.",
            "Shares RDKit's chemical parser and Biopython's mmCIF parser with the generator; this is not an independent validation of those libraries.",
            "Prose and SVG layouts are checked for file integrity and export agreement, not regenerated or scientifically validated. Display coordinates are checked for finite values and graph identities, not recomputed conformers or experimental poses.",
            "No authenticity, authorship, runtime provenance, enzyme-activity, odor, yield, or isotope-enrichment claim is established. Files are read sequentially without a filesystem lock.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--web-dir", type=Path, help="Also check web/data.js against the verified analysis")
    parser.add_argument("--json", action="store_true", help="Print the verification report as JSON")
    args = parser.parse_args(argv)
    try:
        result = verify_results(args.data_dir, args.results_dir, args.web_dir)
    except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError) as error:
        print(f"Verification stopped: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    else:
        print(f"Verified {result['artifacts_checked']} artifacts, {len(result['enzyme_lengths'])} enzymes, "
              f"{result['molecules_checked']} molecular graphs, and {result['balanced_reactions_checked']} balanced reactions.")
        print("This checks computational consistency, not experimental validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
