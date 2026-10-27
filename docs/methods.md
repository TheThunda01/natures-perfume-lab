# Methods and calculation choices

Terminology: [glossary](glossary.md). Rationale and consequences: [assumptions](assumptions.md).

## Fixed case and source checks

The analysis uses the source snapshots included in `data/`. File fingerprints identify exact bytes, so changing whitespace or line endings can change a fingerprint even when a reader sees the same text. Source-provider records establish the original attribution; a matching local hash does not authenticate the provider or prove a scientific claim.

`data/provenance.json` lists the source and curated input paths, byte counts, and SHA-256 values. Its own expected fingerprint is pinned in `perfume_lab/constants.py`. Before analysis, the workflow checks that inventory and every listed file. This prevents replacing a source and its local inventory together without also changing the trusted project code.

The case definitions are `data/curated/chemistry.json` and `data/curated/enzymes.json`. Raw PubChem, UniProt, and RCSB/wwPDB responses remain in `data/sources/`. `data/enzyme-sources.json` and `data/sources/compound-sources.json` retain provider URLs, retrieval details, and source-specific fingerprints. See [data provenance](../data/README.md) for reuse terms.

## Chemical structures and atom correspondence

RDKit parses the selected molecular representations and checks their graph structure. Each result must be interpreted for the exact connectivity, formal charges, and stereochemical specification supplied. Computed graph properties describe that representation; they are not measured physical properties.

The curated atom correspondence records how this case relates labels across molecular graphs. Its purpose is to make the declared bookkeeping inspectable. Bond differences describe endpoints under that correspondence, not a series of mechanistic events.

The chemical module checks three mapped graphs—neutral GPP, (4R)-limonene, and (3R)-linalool—and the auxiliary water and diphosphoric-acid records. It compares each graph with the selected PubChem SMILES after removing map labels, checks molecular formula and InChIKey (a hashed chemical identifier), and checks the declared stereochemistry. Carbon labels 1–10 must each occur once in every mapped compound; noncarbon atoms carry no lineage labels.

The code calculates stereochemical priorities without the arbitrary map numbers. The product configuration is R at lineage C6 for limonene and C3 for linalool. The GPP C2–C3 bond has the declared E configuration. Product nomenclature and lineage numbering serve different purposes: limonene’s conventional C4 is lineage C6 here.

The endpoint comparison reports each changed carbon–carbon bond and its before/after order. It also checks element counts and formal charge on both sides of the two neutral-species equations. Water and diphosphoric acid are included in that full balance even though the carbon diagrams omit them. The C8/C10 symmetry caveat in the [biology guide](biology-and-concepts.md) applies to any selected carbon label.

Two-dimensional SVG drawings use RDKit coordinates and show lineage labels as annotations. Three-dimensional small-molecule views use ETKDGv3 with random seed `20261027`, one thread, and enforced chirality. Where MMFF94 parameters are available, the code attempts up to 500 optimization iterations and records convergence. Display coordinates use ångströms and are rounded to six decimal places. This geometry is a computed illustration, not an experimental conformation, enzyme-bound pose, preferred solution structure, or transition state.

## Sequence alignment

Biopython aligns the selected amino-acid sequences using the settings recorded in the output. Reported identity needs both a numerator and a denominator: identical aligned residues answer a different question from sequence coverage or the fraction of columns containing a gap.

The analysis first requires each saved FASTA sequence to match its UniProt JSON record. It uses the full citrus A0A1C9J6A7 precursor (607 residues) and lavender Q2XSC5 sequence (564 residues), without trimming either to an inferred mature domain.

Biopython `Align.PairwiseAligner` performs a global affine-gap alignment with match score +2, mismatch score −1, gap-open score −10, and gap-extension score −0.5. A gap of length $`n`$ therefore costs $`-10 - 0.5(n-1)`$. Terminal gaps receive the same treatment. The generator takes the first optimum returned by the pinned Biopython version; a different equally optimal alignment is not evidence of a biological insertion or deletion history.

The primary identity percentage divides identical residue pairs by columns containing a residue in both sequences. A separate percentage divides the same matches by all alignment columns, including gaps. The output also records mismatches, gap columns, total columns, and the optimal score. `residue_alignment.csv` uses one-based alignment columns and reference positions; a gap has no reference position. `alignment.fasta` preserves the aligned strings.

A pairwise alignment is a correspondence between these two sequences under the chosen scoring rule. It is not a phylogeny, a functional classifier, or a measure of evolutionary distance calibrated for this enzyme family.

## Experimental structures

The structure check inspects one model: citrus PDB 5UV0, chain A, X-ray resolution 2.3 Å. It uses model 1, `ATOM` records, and alpha-carbon (Cα) atoms. The parser reads mmCIF `label_seq_id` positions and compares the amino-acid identity at each modeled position with the corresponding position in the current reference sequence. The deposited polymer entity and reference sequence agree; the analysis does not align two protein structures or calculate a pocket volume.

Coverage counts distinct reference positions with modeled Cα atoms. Positions without such atoms remain explicitly unmodeled. This denominator is the 607-residue deposited reference, not the 562-residue purified construct including its tag. The paper describes removal of residues 1–52; those absent reference positions cannot all be interpreted as experimental disorder.

The mmCIF preserves a historical ALA/VAL sequence-conflict annotation at position 245. The current pinned UniProt sequence and deposited structure both have alanine there. This annotation is retained as source history, not counted as a current mismatch or an engineered mutation.

No nonwater ligand or metal is modeled in the selected open/apo structure. The cited paper notes unassigned active-site density; this project does not assign a substrate to it. No experimental or predicted lavender protein model is included, so no two-enzyme pocket or structural RMSD comparison is possible.

## Outputs and reproducibility

`run.py --output-dir .reproduction` writes an analysis for this fixed case. The report explains the calculated results, and the structured outputs preserve the values used by the explorer. The supplied sources stay separate from generated artifacts.

The result bundle contains ten artifacts plus `manifest.json`:

| Artifact | Contents |
| --- | --- |
| `analysis.json` | Source identities, chemical checks, aligned sequences and metrics, structural coverage, and Python/package versions |
| `alignment.fasta` | The two complete aligned strings |
| `residue_alignment.csv` | One row per alignment column, with reference positions or gaps |
| `chemical_summary.csv` | Compound name, formula, carbon count, and ring count |
| `report.md` | Readable results and interpretation limits |
| `molecules/gpp.svg`, `molecules/limonene.svg`, `molecules/linalool.svg` | Labeled molecular drawings |
| `figures/reaction_paths.svg` | Schematic of the selected branches, not mechanistic intermediates |
| `figures/sequence_identity.svg` | Counts of matches, mismatches, and gap columns |

The manifest records each artifact’s byte count and SHA-256 plus the source-inventory fingerprint. It does not hash itself. `analysis.json` records runtime versions; the bundle does not authenticate those version strings or its author.

The generator calculates and writes a staged bundle before copying it to the destination. Final replacement is per file, so an interrupted copy can leave an incomplete bundle; run verification before using it. Output files use UTF-8 and explicit table formats. The [practical-use contract](practical-use.md) explains overwrite protection and the separate explorer payload.

## Independent verification

`verify_results.py --results-dir .reproduction` checks the saved analysis. The verifier reads saved files without importing or running the result generator.

The verifier checks the pinned source-inventory fingerprint and all 17 listed input files, then the ten result artifacts and their manifest. It rejects missing or extra result files, duplicate JSON keys, nonfinite numbers, unsafe member paths, and symlinks. Each read member is limited to 20 MiB. Numeric recomputation uses absolute tolerance `1e-10` and zero relative tolerance; declared strings, field sets, and other values use exact checks.

It recovers both complete sequences from the saved alignment, recounts matches and gaps, recalculates the affine-gap score, and independently solves the optimal global score with a separate dynamic-programming recurrence. It checks the FASTA and per-column CSV against the aligned strings. An equally optimal alignment can pass; this does not establish which tied optimum a particular runtime returned first.

For chemistry, separate verifier logic checks the source graphs, stereochemistry, formulas, carbon labels, carbon-bond changes, and neutral element/charge balance. For the citrus structure, it checks the deposited entity sequence and experimental metadata, rereads the selected Cα records, and recounts coverage and current residue mismatches. These checks share RDKit’s chemical parser and Biopython’s mmCIF parser with the generator; they do not independently validate those libraries.

Prose and SVG layouts receive integrity and export-consistency checks, not independent scientific appraisal or regeneration. Display coordinates are checked for finite values and correct atom identities, not by recreating the conformer or validating a protein-bound pose. The verifier does not authenticate reported software versions.

`--web-dir web` additionally requires `web/data.js` to contain the same analysis as the verified bundle. `--json` prints a structured receipt. `--data-dir PATH` can point to a copy of the same pinned source inventory, not a different scientific case. The verifier writes no changes. Status 0 means the stated checks passed; status 2 means a handled validation or read error. Sources and artifacts are read again before completion to detect ordinary changes, but the workflow does not lock the filesystem.

A passing check establishes the stated computational consistency. It cannot establish who generated the files, validate the biological model, or turn a curated correspondence into an experimentally observed mechanism.
