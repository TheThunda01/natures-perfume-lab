"""Generate an inspectable result bundle from pinned sequence and chemistry inputs."""
from __future__ import annotations

import csv
import html
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import tempfile

from .constants import SOURCE_MANIFEST_SHA256
from .io import read_json, sha256, verify_sources, write_json
from .sequences import align_enzymes, alignment_rows, inspect_structures, load_enzymes

ARTIFACTS = (
    "analysis.json", "alignment.fasta", "residue_alignment.csv", "chemical_summary.csv", "report.md",
    "molecules/gpp.svg", "molecules/limonene.svg", "molecules/linalool.svg",
    "figures/reaction_paths.svg", "figures/sequence_identity.svg",
)


def csv_file(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check_destination(output: Path, overwrite: bool) -> None:
    if any(p.is_symlink() for p in [output, *output.parents]):
        raise ValueError("Output path must not use symlinks")
    if output.exists() and not output.is_dir():
        raise ValueError("Output destination is not a directory")
    if output.exists() and any(output.iterdir()):
        if not overwrite:
            raise ValueError("Output directory is not empty; use a new directory or --overwrite for a recognized result bundle")
        if not (output / "manifest.json").is_file():
            raise ValueError("Refusing to overwrite a directory without a result manifest")
        manifest = read_json(output / "manifest.json")
        if manifest.get("schema_version") != 1 or {f["path"] for f in manifest.get("files", [])} != set(ARTIFACTS):
            raise ValueError("Prior output does not have the expected result inventory")
        found = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file() or p.is_symlink()}
        if found != set(ARTIFACTS) | {"manifest.json"} or any(p.is_symlink() for p in output.rglob("*")):
            raise ValueError("Refusing to overwrite unrecognized files or symlinks in the output directory")


def check_web_destination(root: Path, output: Path, web_data: Path) -> None:
    if web_data.suffix != ".js" or any(p.is_symlink() for p in [web_data, *web_data.parents]):
        raise ValueError("Explorer payload must be a regular .js path without symlinks")
    if web_data.resolve().is_relative_to(root / "data") or web_data.resolve().is_relative_to(output):
        raise ValueError("Explorer payload must be outside the source data and result bundle")
    if web_data.exists():
        if not web_data.is_file():
            raise ValueError("Explorer payload destination is not a file")
        try:
            text = web_data.read_text(encoding="utf-8").strip()
            prefix = "window.PERFUME_DATA = "
            if not text.startswith(prefix) or not text.endswith(";"):
                raise ValueError("Not a generated payload")
            record = json.loads(text[len(prefix):-1])
            if (not isinstance(record, dict) or record.get("schema_version") != 1 or
                not isinstance(record.get("source_manifest_sha256"), str) or
                len(record["source_manifest_sha256"]) != 64 or
                {r["id"] for r in record["enzymes"]} != {"limonene_synthase", "linalool_synthase"} or
                set(record["chemistry"]["molecules"]) != {"gpp", "limonene", "linalool"}):
                raise ValueError("Not a recognized result payload")
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("Refusing to replace an existing JavaScript file that is not a recognized explorer payload") from exc


def reaction_figure(path: Path) -> None:
    # A schematic, not an atom-position or mechanistic-intermediate drawing.
    path.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360" role="img" aria-labelledby="title desc">
<title id="title">One precursor, two documented enzyme products</title>
<desc id="desc">Geranyl diphosphate has ten carbons. Sweet orange limonene synthase forms a ring and produces R-limonene. Lavender linalool synthase forms an open-chain alcohol, R-linalool. All ten carbons remain in either selected product.</desc>
<rect width="960" height="360" rx="18" fill="#f7f5ee"/>
<g font-family="DejaVu Sans, sans-serif" fill="#243c30"><text x="40" y="48" font-size="25" font-weight="bold">One precursor, two reaction routes</text>
<rect x="34" y="135" width="255" height="88" rx="12" fill="#dde9df"/><text x="55" y="170" font-size="20">Geranyl diphosphate</text><text x="55" y="200" font-size="16">10 carbon atoms</text>
<path d="M289 179 H360 V101 H514 M360 179 V258 H514" stroke="#516859" stroke-width="3" fill="none"/>
<path d="M505 95 L515 101 L505 107 M505 252 L515 258 L505 264" fill="none" stroke="#516859" stroke-width="3"/>
<rect x="525" y="65" width="400" height="107" rx="12" fill="#f0dfad"/><text x="545" y="97" font-size="19">Sweet orange → (4R)-limonene</text><text x="545" y="124" font-size="15">Ring formation; hydrocarbon product</text><text x="545" y="150" font-size="15">10 carbons retained · C₁₀H₁₆</text>
<rect x="525" y="212" width="400" height="107" rx="12" fill="#e6dff1"/><text x="545" y="244" font-size="19">Lavender → (3R)-linalool</text><text x="545" y="271" font-size="15">Water capture; open-chain alcohol</text><text x="545" y="297" font-size="15">10 carbons retained · C₁₀H₁₈O</text>
<text x="34" y="340" font-size="12">Selected product branches; full balanced equations and source evidence are recorded separately.</text></g></svg>\n''', encoding="utf-8")


def sequence_figure(path: Path, comparison: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.hashsalt": "natures-perfume-lab-v1"}):
        fig, ax = plt.subplots(figsize=(9, 2.6), layout="constrained")
        left = 0
        for name, key, color in [("Identical residues", "matches", "#476c54"),
                                 ("Different residues", "mismatches", "#8a77aa"),
                                 ("Gap columns", "gap_columns", "#d7b96f")]:
            count = comparison[key]
            ax.barh([0], [count], left=left, color=color, label=f"{name}: {count}")
            if count:
                ax.text(left + count / 2, 0, str(count), ha="center", va="center", color="white" if key != "gap_columns" else "#22352b")
            left += count
        ax.set(yticks=[], xlabel="Columns in the full-sequence global alignment", xlim=(0, left))
        ax.set_title(f"{comparison['identity_percent']:.2f}% identity among {comparison['paired_residues']} paired residues", loc="left")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3, frameon=False)
        ax.spines[["top", "left", "right"]].set_visible(False)
        fig.savefig(path, format="svg", metadata={"Date": None, "Creator": "Nature's Perfume Lab"})
        plt.close(fig)


def report(analysis: dict) -> str:
    a, b = analysis["enzymes"]
    c = analysis["sequence_comparison"]
    structural = next(r for r in analysis["structural_evidence"]["records"] if r["status"] == "experimental")
    molecules = analysis["chemistry"]["molecules"]
    table = "\n".join(f"| {m['name']} | {m['formula']} | {m['carbon_count']} | {m['ring_count']} |" for m in molecules.values())
    return f"""# Nature's Perfume Lab: reproducible case study

Two documented plant enzymes use the same ten-carbon precursor but produce different molecular shapes. This report combines source-backed reactions, a descriptive sequence alignment, and checks of one experimental protein structure. It does not predict smell or new enzyme activities.

## The chemical result

| Molecule | Formula in the selected representation | Carbon atoms | Rings |
| --- | --- | ---: | ---: |
{table}

All ten carbon labels occur once in each displayed molecule. Limonene has a ring; linalool remains acyclic and contains an alcohol group. The neutral-species reaction equations balance all elements and formal charge. Neutral bookkeeping does not specify physiological proton stoichiometry.

![Two reaction routes from one precursor](figures/reaction_paths.svg)

**Figure 1. The selected product branches.** The diagrams summarize documented reactions and the curated atom map. They do not show every intermediate or side product. Carbon labels describe a representative lineage map, not a simulated isotope experiment. Small-molecule 3D coordinates in the explorer are calculated display conformers, not experimental or protein-bound structures.

## The sequence comparison

{a['organism']} {a['accession']} has {len(a['sequence'])} residues; {b['organism']} {b['accession']} has {len(b['sequence'])}. The global alignment has **{c['alignment_columns']} columns**, including **{c['paired_residues']} paired-residue columns** and **{c['gap_columns']} gap columns**. Of the paired residues, **{c['matches']} are identical** and **{c['mismatches']} differ**.

Identity is **{c['identity_percent']:.2f}%** when divided by paired-residue columns, or **{c['identity_all_columns_percent']:.2f}%** when divided by all alignment columns. The score is **{c['score']:g}**, using match +2, mismatch −1, gap opening −10, and extension −0.5, including terminal gaps. The first optimum returned by the pinned alignment library is saved; other optimal placements may exist.

![Counts in the sequence alignment](figures/sequence_identity.svg)

**Figure 2. Sequence identity is descriptive.** Both inputs are full canonical sequences. Their different species, N-terminal regions, and assay preparations limit a functional interpretation. These two examples cannot identify a causal product-switching residue or validate a classifier.

Inspect [the aligned sequences](alignment.fasta), [the per-column residue table](residue_alignment.csv), and [the complete analysis](analysis.json).

## Experimental structure evidence

PDB **{structural['pdb_id']} chain {structural['chain']}** contains **{structural['modeled_alpha_carbon_residues']} unique modeled alpha-carbon positions** in the {structural['canonical_length']}-residue reference mapping, with **{len(structural['coordinate_sequence_mismatches'])} current coordinate/sequence mismatches**. The reference sequence is distinct from the tagged, truncated expression construct. Historical database-conflict annotations are retained in the source record rather than interpreted as present sequence differences.

No experimental structure for the selected lavender enzyme is included. The analysis therefore makes no cross-enzyme structural alignment, pocket-volume comparison, or inferred ligand pose.

## Evidence and limits

The citrus primary study reports a predominantly limonene product profile with minor products; a route card is not a claim of absolute product purity. The lavender source supports R-linalool formation. Their assays are not a matched experiment. Whole-plant aromas depend on mixtures, concentration, and perception; the same compound name does not specify every stereoisomer or odor experience.

The 2026 monoterpene-classification paper motivates the topic but its machine-learning analysis is not reproduced here. Passing the source, structural, atom-map, balance, and replay checks establishes the stated computational consistency, not a new biochemical discovery.

## Reproduce and inspect

From the repository root:

```sh
python run.py --output-dir .reproduction
python verify_results.py --results-dir .reproduction
```

The independent verifier checks source and artifact fingerprints, sequence recovery, alignment counts and optimal score, curated chemical identities and maps, and selected structural records. Hash checks on figures and prose do not establish their scientific interpretation. See the repository documentation for exact verification coverage and source access.

Source inventory SHA-256: `{analysis['source_manifest_sha256']}`.
"""


def run(root: Path, output: Path, overwrite: bool = False, web_data: Path | None = None) -> Path:
    from .chemistry import analyze_chemistry
    root = root.resolve()
    output = output.absolute()
    check_destination(output, overwrite)
    if web_data is not None:
        web_data = web_data.absolute()
        check_web_destination(root, output, web_data)
    verify_sources(root)
    enzymes = load_enzymes(root)
    comparison = align_enzymes(enzymes)
    chemistry = analyze_chemistry(root)
    analysis = {"schema_version": 1,
                "scope": "A source-backed, descriptive comparison of two known plant scent-enzyme reactions; no odor or activity prediction.",
                "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
                "enzymes": enzymes, "sequence_comparison": comparison, "chemistry": chemistry,
                "structural_evidence": inspect_structures(root, enzymes),
                "software_versions": {"python": platform.python_version(), **{name: importlib.metadata.version(name) for name in ("biopython", "numpy", "rdkit", "matplotlib", "Pillow")}}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".perfume-build-", dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / "molecules").mkdir()
        (stage / "figures").mkdir()
        write_json(stage / "analysis.json", analysis)
        c = comparison
        (stage / "alignment.fasta").write_text(f">{c['enzyme_a']}\n{c['alignment_a']}\n>{c['enzyme_b']}\n{c['alignment_b']}\n", encoding="utf-8")
        csv_file(stage / "residue_alignment.csv", ["column", "a_position", "a_residue", "b_position", "b_residue"], alignment_rows(c))
        molecules = chemistry["molecules"]
        csv_file(stage / "chemical_summary.csv", ["molecule_id", "name", "formula", "carbon_count", "ring_count"],
                 [{"molecule_id": k, **{f: m[f] for f in ("name", "formula", "carbon_count", "ring_count")}} for k, m in molecules.items()])
        for key, molecule in molecules.items():
            if key not in {"gpp", "limonene", "linalool"}:
                raise ValueError("Unexpected display molecule")
            (stage / "molecules" / f"{key}.svg").write_text(molecule["svg"], encoding="utf-8", newline="\n")
        reaction_figure(stage / "figures/reaction_paths.svg")
        sequence_figure(stage / "figures/sequence_identity.svg", c)
        (stage / "report.md").write_text(report(analysis), encoding="utf-8")
        manifest = {"schema_version": 1, "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
                    "files": [{"path": name, "sha256": sha256(stage / name), "bytes": (stage / name).stat().st_size} for name in sorted(ARTIFACTS)]}
        write_json(stage / "manifest.json", manifest)
        output.mkdir(exist_ok=True)
        for name in (*ARTIFACTS, "manifest.json"):
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / name, target)
    if web_data is not None:
        web_data.parent.mkdir(parents=True, exist_ok=True)
        payload = "window.PERFUME_DATA = " + json.dumps(analysis, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + ";\n"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=web_data.parent,
                                         prefix=".perfume-payload-", delete=False) as stream:
            temporary_payload = Path(stream.name)
            stream.write(payload)
        try:
            temporary_payload.replace(web_data)
        finally:
            temporary_payload.unlink(missing_ok=True)
    return output
