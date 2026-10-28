# Why study nature's perfume with code?

## Background and rationale

Nature builds many different molecules from shared starting materials. That raises a question that joins chemistry and molecular biology: how can one precursor lead to different products, and what evidence helps explain the branch?

This project uses geranyl diphosphate (GPP), limonene, and linalool as a small case study. Limonene has a ring; linalool has an open carbon chain and an alcohol group. Comparing their molecular graphs makes the difference concrete. The citrus limonene-synthase and lavender linalool-synthase sequences then add protein evidence. An experimental citrus structure provides a separate check of modeled residue coverage; no lavender structure is included. The [biology guide](biology-and-concepts.md) explains the chemistry and its source support.

The title supplies a familiar starting point, not an odor-prediction claim. This repository does not measure scent, infer a plant's volatile composition, or forecast how a person will perceive a mixture. Its question concerns chemical identity and enzyme evidence.

## What it does

The workflow begins with fixed public-source snapshots. It checks their file fingerprints, inspects chemical structures, records a curated atom correspondence, aligns selected protein sequences, and checks the citrus experimental model against its reference sequence. The report and explorer expose the inputs and choices behind each result.

Each step has a different evidential role. RDKit checks the supplied molecular graphs. Sequence alignment compares ordered amino-acid strings. The structure check inspects deposited citrus coordinates and metadata. These operations support a reproducible description of the selected records; they do not recreate catalysis or establish a new biological mechanism.

## Why it matters

A convincing molecular picture can hide uncertainty about identity, stereochemistry, sequence numbering, missing residues, or the meaning of a bound ligand. This case keeps those questions visible. A reader can inspect one evidence source at a time and see where a conclusion needs an experiment or a stronger comparison.

The intended readers are students and researchers learning to connect molecular chemistry with protein evidence. The repository is also a starting point for a carefully bounded extension: a broader set of independently characterized enzymes, for example, would ask a different question and need its own data-selection rules.

## Key themes

- **Shared starting material:** compare products without assuming one route explains every enzyme or organism.
- **Explicit correspondence:** show how atom labels and sequence positions are related.
- **Evidence boundaries:** distinguish source annotations, computed properties, structural observations, and untested interpretations.
- **Reproducibility:** keep source versions, calculation settings, and output checks together.

This project was developed with AI assistance. Its computational results come from the documented code and pinned inputs; its biological context comes from attributed sources. See the [methods](methods.md), [literature review](literature-review.md), and [assumptions](assumptions.md) before interpreting an output.

## Where this fits

Continue to the [enzyme kinetics workbench](https://github.com/TheThunda01/enzyme-kinetics-workbench) to ask what reaction-rate measurements can reveal about a fitted model. It uses a separate archived dataset. The link is a reading route from molecular evidence to quantitative questions, not a kinetic analysis of the enzymes shown here.
