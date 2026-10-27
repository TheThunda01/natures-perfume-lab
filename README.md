# Nature's perfume lab

**Orange peel and lavender contain familiar aroma compounds. How do plants build them from the same starting molecule?** Follow geranyl diphosphate (GPP) toward limonene and linalool, two products made by the selected citrus and lavender enzymes. The explorer lets you follow carbon atoms, rotate molecular illustrations, and compare the enzymes behind these routes.

## Why this project

Start with one carbon atom. Follow its label from GPP into a ring-shaped limonene molecule or an open-chain linalool molecule. Then look at the two enzyme sequences: where do they match, and what can a match actually tell us? An experimental citrus structure adds another view of the evidence.

The aim is to make the connection between chemistry and proteins easier to explore, with the sources and calculations close at hand. No coding is needed to use the prepared explorer; the Python workflow lets you reproduce its results. Start with the [project context](docs/project-context.md) or the [biology guide](docs/biology-and-concepts.md).

This case study was developed with AI assistance. It uses attributed public records and computational checks, with no new laboratory or sensory measurements.

## What it does

| Selected enzyme | Evidence used here | Boundary |
| --- | --- | --- |
| *Citrus sinensis* (+)-(4R)-limonene synthase, [UniProt A0A1C9J6A7](https://www.uniprot.org/uniprotkb/A0A1C9J6A7/entry) | Reviewed reference sequence, 607 residues; [Morehouse et al. (2017)](docs/references.md#morehouse-2017); [PDB 5UV0](https://www.rcsb.org/structure/5UV0), chain A | The published assay reported 99% limonene among products, not an exclusively limonene product mixture. The crystal is an open/apo model. |
| *Lavandula angustifolia* (3R)-(−)-linalool synthase, [UniProt Q2XSC5](https://www.uniprot.org/uniprotkb/Q2XSC5/entry) | Reviewed reference sequence, 564 residues; experimental function reported by [Landmann et al. (2007)](docs/references.md#landmann-2007) | No experimental structure is included for this selected enzyme. The primary paper was appraised at abstract level. |

These records come from different species and assay preparations. They do not form a controlled experiment in which sequence is the only difference.

- Checks the exact source snapshots against recorded file fingerprints.
- Uses RDKit, a molecular-graph toolkit, to inspect selected chemical structures and an explicitly curated atom correspondence.
- Uses Biopython to align selected enzyme sequences and report the scoring and denominator behind their similarity.
- Checks the citrus structure’s modeled alpha-carbon (Cα) positions against its reference sequence. It does not infer the lavender enzyme’s pocket or compare pockets across the pair.
- Produces a report, machine-readable results, and a static explorer for inspecting the same case.

The [2026 monoterpene-classification study](docs/references.md#o-raghallaigh-2026) inspired this small exploration. This project compares two documented cases; it does not reproduce or train that study’s classifier. Carbon labels show a curated correspondence between the starting compound and each product, not a simulated reaction or isotope-tracing experiment.

## Quick start

Use Python 3.12. From the project directory, create a virtual environment:

```sh
python -m venv .venv
```

Activate it on macOS or Linux:

```sh
source .venv/bin/activate
```

Or in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies, reproduce the analysis, and verify its outputs:

```sh
python -m pip install -r requirements.txt
python run.py --output-dir .reproduction
python verify_results.py --results-dir .reproduction
python -m unittest discover -s tests -v
```

The source snapshots are bundled, so the analysis needs no network after installation. Use the separate `.reproduction/` directory to keep the recorded [example results](results/report.md) available for comparison. Read the [practical-use contract](docs/practical-use.md) before choosing another output path.

To open the static explorer:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory web
```

Open <http://127.0.0.1:8000/>. The explorer displays this project's prepared evidence; it does not run a database search or accept arbitrary molecules and proteins.

## Example results

The carbon checks distinguish two outcomes without losing the shared ten-carbon framework: limonene forms a ring, while linalool remains an open-chain alcohol. Both declared neutral-species equations balance elements and formal charge.

![GPP branches toward the selected citrus limonene and lavender linalool products](results/figures/reaction_paths.svg)

**Figure 1. A shared precursor, two selected product branches.** This schematic summarizes the curated case. It omits minor products and mechanistic intermediates; the full neutral equations and carbon-label convention are recorded separately.

| Check | Recorded result | Interpretation |
| --- | --- | --- |
| Carbon labels | All 10 occur once in GPP and each selected product | Complete bookkeeping under the declared map, not measured isotope fate |
| Product graphs | Limonene: C10H16, 1 ring; linalool: C10H18O, 0 rings | Connectivity and formula of the selected stereochemical records |
| Sequence identity | 243 identical pairs / 560 paired-residue columns = **43.39%** | Descriptive identity for the alignment of the full canonical sequences |
| Gaps and alternate denominator | 51 gap columns; 243 / 611 total columns = **39.77%** | The denominator changes the reported percentage |
| Citrus structural coverage | **522 modeled Cα positions** out of 607 reference positions; **0 current identity mismatches** | Coverage of the deposited reference mapping, not the expressed construct length |

![Alignment columns divided into 243 identical residues, 317 different residues and 51 gap columns](results/figures/sequence_identity.svg)

**Figure 2. Sequence identity needs a denominator.** The displayed 43.39% uses only paired-residue columns. These two full canonical sequences come from different species and experiments; this comparison does not identify residues that cause a product switch.

The [aligned FASTA](results/alignment.fasta), [per-column residue table](results/residue_alignment.csv), [chemical table](results/chemical_summary.csv), and [complete analysis JSON](results/analysis.json) expose the values behind the figures.

Read the [report](results/report.md) for the complete results and their limits. The [methods](docs/methods.md) explain how each quantity is calculated.

## Practical use and limitations

Use this project to learn how chemical identity, atom bookkeeping, sequence alignment, and structural evidence fit together. It is a fixed case study, not a general analysis service.

- **Chemical identity:** stereochemistry and the chosen charge state matter. Similar formulas or two-dimensional drawings do not imply the same biological behavior.
- **Atom correspondence:** mapping atoms records a declared correspondence. It does not establish the order of bond changes, intermediates, reaction energetics, or experimentally observed atom fate.
- **Sequence alignment:** identity depends on the selected sequences, scoring, gaps, and denominator. It does not measure catalytic specificity.
- **Experimental structure:** PDB 5UV0 describes a particular citrus construct and an open/apo model. Missing coordinates remain missing. Without a matched lavender structure, the project makes no cross-enzyme pocket comparison.
- **Scent:** the project has no odor-response dataset or sensory experiment. Compound identity alone cannot predict the smell of a plant, a mixture, or a person’s perception.

## Documentation

| Guide | What it covers |
| --- | --- |
| [Project context](docs/project-context.md) | Question, rationale, and intended readers |
| [Biology and concepts](docs/biology-and-concepts.md) | Shared precursor, chemical branching, enzyme evidence, and scent boundaries |
| [Methods](docs/methods.md) | Source checks, calculations, selections, and metric definitions |
| [Practical use](docs/practical-use.md) | Input/output contract, worked example, failure behavior, and next steps |
| [Glossary](docs/glossary.md) / [assumptions](docs/assumptions.md) | Terms, choices, checks, and consequences |
| [References](docs/references.md) / [reference audit](docs/reference-audit.json) | Sources, supported claims, access levels, and remaining limits |
| [Literature review](docs/literature-review.md) / [search log](docs/search-log.json) | Bounded search, screening decisions, and source-to-method links |
| [Data provenance](data/README.md) | Snapshot origins, attribution, and reuse terms |
| [Editorial and verification record](docs/review-2026-10-27.md) | What was checked during this release and what remains untested |

## Development and reuse

[Contributing](CONTRIBUTING.md) explains how to propose a focused change and retain reproducible evidence. Tests check specified software behavior; they do not establish biological accuracy, sensory validity, or research benefits.

The original project code is available under the [MIT license](LICENSE). Public source records retain the separate [attribution and reuse terms](data/README.md) of their providers. [Citation metadata](CITATION.cff) identifies this software; cite the underlying data and methods when using their evidence.
