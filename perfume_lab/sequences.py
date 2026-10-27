"""A descriptive, fixed-score alignment of two full canonical sequences."""
from __future__ import annotations

from pathlib import Path
from Bio import Align, SeqIO
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.SeqUtils import seq1

from .io import read_json, safe_file

SCORING = {"match": 2.0, "mismatch": -1.0, "open_gap": -10.0, "extend_gap": -0.5}


def load_enzymes(root: Path) -> list[dict]:
    records = read_json(root / "data/curated/enzymes.json")["enzymes"]
    for record in records:
        sequence = str(SeqIO.read(safe_file(root, record["source_files"]["fasta"]), "fasta").seq)
        annotation = read_json(safe_file(root, record["source_files"]["uniprot_json"]))
        if sequence != annotation["sequence"]["value"] or sequence != record["sequence"]:
            raise ValueError(f"FASTA/annotation/curation sequence mismatch: {record['id']}")
        if len(sequence) != record["sequence_length"] or not set(sequence) <= set("ACDEFGHIKLMNPQRSTVWY"):
            raise ValueError(f"Invalid canonical sequence: {record['id']}")
        if annotation["primaryAccession"] != record["accession"]:
            raise ValueError(f"Accession mismatch: {record['id']}")
    if {r["id"] for r in records} != {"limonene_synthase", "linalool_synthase"} or len(records) != 2:
        raise ValueError("This case study requires its two documented reference enzymes")
    return sorted(records, key=lambda r: r["id"] != "limonene_synthase")


def align_enzymes(enzymes: list[dict]) -> dict:
    a, b = enzymes
    aligner = Align.PairwiseAligner(mode="global", match_score=SCORING["match"],
                                   mismatch_score=SCORING["mismatch"],
                                   open_gap_score=SCORING["open_gap"],
                                   extend_gap_score=SCORING["extend_gap"])
    alignment = aligner.align(a["sequence"], b["sequence"])[0]
    first, second = str(alignment[0]), str(alignment[1])
    paired = sum(x != "-" and y != "-" for x, y in zip(first, second))
    matches = sum(x == y and x != "-" for x, y in zip(first, second))
    return {"enzyme_a": a["id"], "enzyme_b": b["id"],
            "method": "Global affine-gap pairwise alignment of full canonical UniProt sequences; first optimum returned by pinned Biopython",
            "scoring": SCORING.copy(), "alignment_a": first, "alignment_b": second,
            "alignment_columns": len(first), "aligned_length": len(first),
            "paired_residues": paired, "matches": matches, "mismatches": paired - matches,
            "gap_columns": len(first) - paired, "identity_percent": 100.0 * matches / paired,
            "identity_all_columns_percent": 100.0 * matches / len(first), "score": float(alignment.score),
            "notes": ["Identity uses columns containing a residue in both sequences; gaps have a separate count.",
                      "Full canonical sequences retain N-terminal regions; the citrus experimental construct removes its targeting segment, while no lavender processing boundary is established here.",
                      "Different species and assay preparations confound a causal interpretation of sequence differences.",
                      "One pair does not establish which residues determine a product, an odor, or an activity rate."]}


def alignment_rows(comparison: dict) -> list[dict]:
    rows, i, j = [], 0, 0
    for column, (a, b) in enumerate(zip(comparison["alignment_a"], comparison["alignment_b"]), 1):
        i += a != "-"
        j += b != "-"
        rows.append({"column": column, "a_position": i if a != "-" else "",
                     "a_residue": a, "b_position": j if b != "-" else "", "b_residue": b})
    return rows


def inspect_structures(root: Path, enzymes: list[dict]) -> dict:
    records = []
    for enzyme in enzymes:
        source = enzyme.get("experimental_structure", {})
        if source.get("status") != "available":
            records.append({"enzyme_id": enzyme["id"], "status": "not_included",
                            "note": "No experimental structure is included for this selected enzyme; no cross-enzyme pocket geometry is inferred."})
            continue
        structure = MMCIF2Dict(str(safe_file(root, source["source_files"]["mmcif"])))
        chain = source.get("label_asym_id", "A")
        ids = structure["_atom_site.label_seq_id"]
        residues = {}
        for idx, value in enumerate(ids):
            if (structure["_atom_site.label_asym_id"][idx] != chain or
                structure["_atom_site.label_atom_id"][idx] != "CA" or
                structure["_atom_site.group_PDB"][idx] != "ATOM" or
                structure.get("_atom_site.pdbx_PDB_model_num", ["1"] * len(ids))[idx] != "1"):
                continue
            position = int(value)
            aa = seq1(structure["_atom_site.label_comp_id"][idx])
            if not 1 <= position <= len(enzyme["sequence"]):
                raise ValueError("Structure position outside deposited reference sequence")
            if position in residues and residues[position] != aa:
                raise ValueError("Conflicting structure residue identity")
            residues[position] = aa
        mismatches = [{"position": p, "coordinate": aa, "canonical": enzyme["sequence"][p - 1]}
                      for p, aa in sorted(residues.items()) if enzyme["sequence"][p - 1] != aa]
        if mismatches:
            raise ValueError(f"Current coordinate/sequence mismatches: {mismatches}")
        records.append({"enzyme_id": enzyme["id"], "status": "experimental", "pdb_id": source["pdb_id"],
                        "chain": chain, "canonical_length": len(enzyme["sequence"]),
                        "modeled_alpha_carbon_residues": len(residues),
                        "unmodeled_reference_positions": [p for p in range(1, len(enzyme["sequence"]) + 1) if p not in residues],
                        "coordinate_sequence_mismatches": mismatches,
                        "resolution_angstrom": source.get("resolution_angstrom"),
                        "note": "Positions use mmCIF label_seq_id and the documented identity mapping to the deposited canonical reference; this is not a count of residues in the experimental expression construct.",
                        "source_record": source})
    return {"records": records, "comparison": "One experimental enzyme structure is inspected; no pairwise enzyme structure comparison is made."}
