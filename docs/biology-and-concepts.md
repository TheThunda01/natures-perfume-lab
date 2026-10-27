# From a shared precursor to different molecules

Terminology: [glossary](glossary.md). Source details and access limits: [references](references.md) and [reference audit](reference-audit.json).

## Start with the molecule

Geranyl diphosphate (GPP) is a ten-carbon precursor used in monoterpene biosynthesis. A precursor is a starting compound in a chemical transformation. Limonene and linalool both have ten-carbon frameworks, but their connectivity and functional groups differ: limonene is cyclic, whereas linalool is an acyclic alcohol. The selected source structures make these distinctions explicit.

Stereochemistry adds another distinction. Molecules can have the same connectivity while arranging atoms differently in space. A stereochemical name or symbol must therefore be tied to the selected chemical record. An unspecified stereocenter is missing specification, not evidence that all forms behave identically.

The selected products are (4R)-(+)-limonene from the citrus enzyme and (3R)-(−)-linalool from the lavender enzyme. The `R` label specifies stereochemical configuration under a naming rule; `+` and `−` report the sign of optical rotation. One does not determine the other. The source records, not a rule that “R means positive,” define these particular names.

[Morehouse et al. (2017)](references.md#morehouse-2017) reported a citrus product mixture containing 99% limonene, 0.7% myrcene, and 0.3% α-pinene. “Exclusively (+)” refers to the limonene enantiomer, not to an exclusively limonene product mixture. [Landmann et al. (2007)](references.md#landmann-2007) reported the selected lavender enzyme’s linalool function; this review accessed the abstract rather than the full paper. These are attributed experimental findings, not measurements made by this repository.

## What atom tracking means here

An atom map assigns labels so that a chosen atom in one molecular graph can be related to an atom in another. Here the labels track carbon only. GPP C1 is the carbon attached to the diphosphate oxygen; C1–C8 follow the main chain, C9 is the methyl attached to C3, and C10 is the second methyl attached to C7. These are persistent lineage labels, not a universal numbering system for the products. The code checks the declared labels and which carbon–carbon bonds differ. In limonene, the atom conventionally named C4 has lineage label C6 in this map. The unlabeled GPP graph also permits exchanging the two methyl labels C8 and C10. This case selects one representative correspondence; it does not establish their fate in a position-specific isotope experiment or imply identical spectroscopic environments.

Follow C1 in the explorer. In the limonene map, it gains a bond to C6, closing the ring; two other carbon–carbon bonds change order. In the linalool map, the carbon connections stay open-chain, while the C2–C3 double bond becomes a C1–C2 double bond and the alcohol group is attached at C3. These comparisons describe the starting and ending graphs.

That calculation is narrower than explaining a reaction mechanism. A mechanism also concerns intermediate species, the sequence of chemical steps, stereochemical outcomes, and the conditions under which they occur. A two-dimensional graph comparison does not establish those features. The project does not follow measured isotope labels or simulate a time-dependent reaction.

## What the enzyme contributes

An enzyme can shape which transformations occur by providing a particular chemical environment. A protein's sequence describes its ordered amino acids; its structure describes a model of their spatial arrangement. Neither is a complete record of catalysis.

The comparison uses the full canonical UniProt sequences: 607 residues for citrus A0A1C9J6A7 and 564 for lavender Q2XSC5. Both downloaded records are reviewed entries. The citrus reference includes an N-terminal targeting region absent from the experimental construct; this project does not impose a processing boundary on the lavender sequence. The alignment retains both complete references rather than independently defined catalytic domains.

The two enzymes come from different organisms and experiments. Their reported products motivate the comparison, but differences in the alignment cannot identify which substitutions cause the product difference. That causal question would require a suitable experimental or independently validated comparative design.

Sequence correspondence can help locate conserved regions or differences, but an aligned residue is not automatically a catalytic residue. Likewise, identity between two sequences does not measure how much product either enzyme makes or establish that they share a product profile. This project compares the selected sequences without training a classifier or predicting new functions.

## Read a structure as evidence

An experimental structure contains modeled atoms supported by a particular experiment and refinement. It may omit flexible residues or include a shortened construct, mutations, cofactors, ligands, or analogues. The structure's residue labels can also differ from positions in a reference sequence.

The analysis inspects chain A of the 2.3 Å citrus structure, PDB 5UV0. It records alpha-carbon (Cα) coverage and checks modeled residue identities against the reference sequence. Missing coordinates remain missing. A ligand observed in a structure helps describe that experimental state; it does not by itself demonstrate substrate turnover, product release, or the complete catalytic path. Structural similarity likewise cannot establish the cause of a difference in enzyme behavior.

5UV0 is an open/apo structure. The paper describes a crystallization construct lacking reference residues 1–52 and carrying a His6 tag, whereas the deposited polymer entity lists the 607-residue reference sequence. The paper reports a purified construct length of 562 residues including its tag. A deposited reference length is therefore not the length of the material used in the experiment. The coordinate check reports which reference positions actually have modeled Cα atoms. The 85 unmodeled reference positions include the removed targeting segment; they do not all represent experimentally disordered residues.

The mmCIF also preserves a historical ALA/VAL conflict at position 245, while the current pinned UniProt sequence and deposited model both have alanine. The project retains the historical note without turning it into a current sequence mismatch.

No experimental structure is included for the selected lavender enzyme. The project neither predicts one nor substitutes a different enzyme’s structure as if it were the same protein. It makes no cross-enzyme pocket-volume, ligand-binding, or RMSD comparison.

## Neutral equations and display geometry

The chemical snapshots represent neutral GPP and diphosphoric acid. The code checks element and formal-charge balance for those explicit representations:

- Neutral GPP → limonene + diphosphoric acid.
- Neutral GPP + water → linalool + diphosphoric acid.

These equations are bookkeeping conventions, not claims about physiological protonation or proton stoichiometry. The carbon-only diagrams omit water and diphosphate for readability. They do not imply that linalool is formed by oxidizing limonene: the two displayed routes branch from GPP.

Any three-dimensional small-molecule view uses a fixed-seed RDKit conformer for display. It is not an experimental conformation, an enzyme-bound pose, or a computed reaction trajectory.

## Why this is not a smell prediction

A chemical record can identify a molecule without predicting a sensory experience. An odor experiment would need its own measurements and definitions, including what material was presented and how responses were recorded. A plant sample or mixture also raises questions beyond the identity of one isolated compound.

This case contains no sensory labels, odor-receptor assay, or model trained to predict smell. Its conclusions concern the supplied molecular graphs, selected enzyme records, and the deposited citrus structure. The [practical-use guide](practical-use.md) separates those conclusions from possible future experiments.
