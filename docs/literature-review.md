# Literature review

## Question and scope

What published evidence supports comparing a plant enzyme that primarily cyclizes geranyl diphosphate (GPP) to limonene with one that forms the acyclic alcohol linalool? This focused review selects traceable enzymes and distinguishes experimental observations from database annotations and structural interpretation.

The selected pair is *Citrus sinensis* (+)-(R)-limonene synthase, UniProt A0A1C9J6A7, and *Lavandula angustifolia* (R)-(−)-linalool synthase LaLINS, UniProt Q2XSC5. Both appear in the 2026 ATC source table and have primary functional characterization. Citrus has an experimental structure, PDB 5UV0. This release does not provide experimental coordinates for lavender LaLINS or claim to reconstruct its catalytic mechanism.

## Search record

On 27 October 2026, PubMed searches for `limonene synthase crystal structure` and `linalool synthase characterization structure`, restricted to publication years 2000–2019, each returned nine records. Both result pages were retrieved for each search. Two additional records were retrieved directly: the requested 2026 classification paper, PMID 42799051, and the selected lavender characterization, PMID 17662687.

Of 20 distinct publication records, seven were included and 13 excluded after screening for relevance to the selected enzymes, their structural background, or the current classification dataset. The audit used full text for three included papers and abstracts for four. Full-text requests failed for the two PNAS background papers; the returned rights information did not permit automated full-text retrieval. Lavender assay detail therefore remains less fully verified than the citrus characterization. The [search log](search-log.json) records exact queries, pagination, counts, decisions, and access outcomes.

The 2026 paper led to a read of the ATC README, license, reference table, and feature table at commit `3216a2cdc89a97a9cc28c65011c628717159f7e4`. Pinned UniProt and RCSB records were also inspected. The [reference audit](reference-audit.json) separates metadata verification from support for individual claims; the [references](references.md) provide citations and reuse terms.

## What the sources support

### Product identity and source selection

[Morehouse et al.](references.md#morehouse-2017) experimentally characterized the selected citrus enzyme. Their reported product profile is 99% limonene, 0.7% beta-myrcene, and 0.3% alpha-pinene. Circular dichroism comparison supports the (+)-limonene enantiomer assignment. The ATC table's 99.3% cyclic fraction includes alpha-pinene; labeling it “99.3% limonene” would change the measurement's meaning.

The abstract of [Landmann et al.](references.md#landmann-2007) reports that lavender LaLINS forms exclusively (R)-(−)-linalool in the reported characterization. The same paper studies LaLIMS, a separate multiproduct synthase. Selecting Q2XSC5 avoids mixing those enzymes. The reported exclusivity should remain tied to the source assay; it does not establish product purity under every condition. The detailed lavender assay context in ATC is secondary curation because this review did not inspect Landmann's full text.

The two examples support a comparison of product topology and oxygen incorporation from a shared substrate. They do not form a matched experiment: assay conditions, constructs, and cofactors differ. Product identity and fraction should not be converted into a claim about relative catalytic efficiency, yield, or industrial suitability.

### Structural evidence and annotation limits

The citrus publication reports a 607-residue native sequence but uses an expression construct lacking residues 1–52 and carrying an affinity tag. The [5UV0 archive](references.md#pdb-5uv0) records 607 deposited polymer positions and 522 modeled residues. These numbers describe different objects. The structure is apo/open; its coordinates do not show a native substrate, product, or complete catalytic metal arrangement. Missing coordinates are not evidence that the native enzyme lacks those residues.

The archival A245/V245 conflict annotation also needs context: the pinned current UniProt and PDB polymer sequences both contain A245 and match across all positions. No engineered mutation is recorded. This release uses the structure as evidence for a fold and coordinate coverage, while keeping reaction interpretation separate.

The [UniProt records](references.md#uniprot-citrus) are reviewed, but their evidence varies by field. Citrus chloroplast localization is sequence-based. Lavender function and catalytic-reaction annotations cite experimental evidence, whereas its cofactor and three-metal-ion annotations are by similarity. A reviewed record is neither a declaration that every annotation was measured nor a substitute for experimental coordinates.

[Hyatt et al.](references.md#hyatt-2007), [Srividya et al.](references.md#srividya-2015), and [Crowell et al.](references.md#crowell-2002) supply background on related enzymes; they do not establish the selected pair's complete mechanism. [Karuppiah et al.](references.md#karuppiah-2017) provide experimental bacterial linalool-synthase structures, but that enzyme differs from lavender in organism and domain architecture. The authors describe one bound analogue pose as noncatalytic. Using those coordinates as if they were a lavender catalytic complex would exceed the evidence.

### What the 2026 study adds

[Ó Raghallaigh, Scrutton, and Hay](references.md#o-raghallaigh-2026) classify monoterpene synthases using AlphaFold2 models and Fpocket descriptors from manually selected pockets. Their curated reference table has 88 enzyme records. The modelling table has 87 observations: 59 linear and 28 cyclic. These counts refer to different tables and should remain distinct.

The labels summarize published GC-MS product profiles, with at least 70% of products in the assigned linear or cyclic class. A class label is therefore a simplification of an assay-dependent product profile. The methods also describe excluding A0A8H4VHP2 and O22340 because their inclusion reduced model performance. This selection history and the paper's discussion of sequence similarity across data splits limit how its reported performance should be generalized.

The source table provides useful accession, sequence, assay-context, and citation links for choosing this pair. This release does not reproduce AlphaFold prediction, pocket selection, feature extraction, data splitting, training, or the study's accuracy. Associations between pocket features and classes are not a demonstrated universal causal rule for cyclization.

## Changes made

- Selected two plant enzymes with traceable primary functional characterization and explicit accessions.
- Separated the citrus limonene fraction from the broader cyclic-product fraction.
- Distinguished the native sequence, expression construct, deposited sequence, and modeled residues.
- Recorded that lavender function is experimentally supported while selected cofactor annotations are by similarity, and retained the lavender structure gap.
- Added the verified 2026 paper citation, inspected its accessible data and license, and separated its published results from this repository's analysis.
- Recorded exact search decisions, access limitations, versioned sources, and reuse terms in machine-readable audits.

## Remaining work

Read the full lavender characterization before relying on its detailed assay conditions, detection limits, or quantitative comparisons. A broader review could include other substrates, additional plant synthases, and publications from 2020–2026 beyond the requested current paper. Any later lavender structural model should be labeled as predicted and assessed separately from the citrus crystal structure. Reproducing the classification study would require a separate protocol for data inclusion, pocket selection, data splitting, and model evaluation.

## Limits of this review

This is a focused narrative review for an educational comparison, not a systematic review or a complete map of terpene-synthase research. Screening decisions reflect this project's scope. Metadata and abstracts were available for all included publications, but full text was inspected for only three. Full-text access records describe the sections reviewed; raw assay data, diffraction data, supplementary experiments, and every cited reference were not independently reprocessed or audited.

No experiments were conducted, and no literature product profile was remeasured. Database evidence codes and published assays support bounded claims about the selected enzymes; they do not establish a complete mechanism, universal product specificity, or prospective engineering performance.
