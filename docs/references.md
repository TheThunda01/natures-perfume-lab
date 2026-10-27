# References

These sources support the selected citrus and lavender enzymes, the chemical comparison, and its limits. The review was completed on 27 October 2026. Access levels describe what was actually inspected; a verified citation does not mean every assertion in its paper was independently verified. See the [literature review](literature-review.md), [search record](search-log.json), and [claim-level reference audit](reference-audit.json).

## Selected enzymes

<a id="morehouse-2017"></a>

**Morehouse et al. (2017).** Functional and Structural Characterization of a (+)-Limonene Synthase from *Citrus sinensis*. *Biochemistry* **56**(12), 1706–1715. [DOI: 10.1021/acs.biochem.7b00143](https://doi.org/10.1021/acs.biochem.7b00143); [PMID: 28272875](https://pubmed.ncbi.nlm.nih.gov/28272875/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5642283/).

Full text retrieved; construct, product, structural results, and interpretation inspected. This is the primary experimental source for the selected citrus enzyme and PDB 5UV0. Its assay reports 99% limonene, 0.7% beta-myrcene, and 0.3% alpha-pinene. The 99.3% cyclic fraction in the ATC table includes alpha-pinene; it is not the limonene fraction. The paper's full-length sequence, truncated expression construct, and modeled coordinates have different coverage. No general open reuse license was returned for the article; this repository cites it without redistributing it.

<a id="landmann-2007"></a>

**Landmann et al. (2007).** Cloning and functional characterization of three terpene synthases from lavender (*Lavandula angustifolia*). *Archives of Biochemistry and Biophysics* **465**(2), 417–429. [DOI: 10.1016/j.abb.2007.06.011](https://doi.org/10.1016/j.abb.2007.06.011); [PMID: 17662687](https://pubmed.ncbi.nlm.nih.gov/17662687/).

Abstract and metadata inspected. The abstract reports that LaLINS produces exclusively (R)-(−)-linalool in the reported characterization. LaLIMS is a separate, multiproduct enzyme described in the same paper. The selected entry is LaLINS, Q2XSC5. Detailed assay context copied into ATC remains secondary curation here because the primary full text was not read. No explicit open reuse license was returned.

## Current classification study and dataset

<a id="o-raghallaigh-2026"></a>

**Ó Raghallaigh, Scrutton, and Hay (2026).** Pockets to products: a data-driven approach for classification of monoterpene synthases. *Digital Discovery* **5**(10), 4573–4589. [DOI: 10.1039/d6dd00312e](https://doi.org/10.1039/d6dd00312e); [PMID: 42799051](https://pubmed.ncbi.nlm.nih.gov/42799051/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13613485/).

Full text retrieved; relevant methods, results, interpretation, and data availability inspected. The authors use AlphaFold2 models and manually selected Fpocket pockets to classify enzymes by predominantly linear or cyclic product profiles. The work supplies a useful curated source table, but this repository does not reproduce its model training or reported accuracy. Methods describe exclusions based on reduced model performance, which must be considered when interpreting the study. Article license: CC BY 3.0. The citation above follows the published record; the source repository's README uses different title wording.

<a id="atc-dataset"></a>

**Ó Raghallaigh et al. — ATC repository.** [Source snapshot at commit 3216a2c](https://github.com/cathaloraghallaigh/ATC/tree/3216a2cdc89a97a9cc28c65011c628717159f7e4), inspected 27 October 2026. The inspected files were [README.md](https://github.com/cathaloraghallaigh/ATC/blob/3216a2cdc89a97a9cc28c65011c628717159f7e4/README.md), [CharacterisedSeqRef.csv](https://github.com/cathaloraghallaigh/ATC/blob/3216a2cdc89a97a9cc28c65011c628717159f7e4/CharacterisedSeqRef.csv), [FullDataset.csv](https://github.com/cathaloraghallaigh/ATC/blob/3216a2cdc89a97a9cc28c65011c628717159f7e4/FullDataset.csv), and [LICENSE](https://github.com/cathaloraghallaigh/ATC/blob/3216a2cdc89a97a9cc28c65011c628717159f7e4/LICENSE).

The reference table contains 88 enzyme records. The derived-feature table contains 87 observations: 59 linear and 28 cyclic. Both selected accessions appear in both tables. Published class labels require at least 70% of reported products to be linear or cyclic; a class fraction need not equal the named product fraction. These are curated literature labels and derived features, not measurements made by this project. Repository license: MIT, copyright 2025 Cathal Ó Raghallaigh. Preserve that notice with copied material; article and upstream database rights remain separate.

## Sequence and structure records

<a id="uniprot-citrus"></a>

**UniProtKB A0A1C9J6A7.** [Reviewed citrus (+)-limonene synthase record](https://www.uniprot.org/uniprotkb/A0A1C9J6A7/entry), entry version 34, sequence version 2; 607 residues. Inspected the pinned JSON and FASTA retrieved on 27 October 2026. Function and catalytic annotations cite experimental sources, whereas chloroplast localization has sequence-based evidence. Reviewed status is not evidence that every field was measured directly.

<a id="uniprot-lavender"></a>

**UniProtKB Q2XSC5.** [Reviewed lavender (R)-linalool synthase record](https://www.uniprot.org/uniprotkb/Q2XSC5/entry), entry version 63, sequence version 1; 564 residues. Inspected the pinned JSON and FASTA retrieved on 27 October 2026. Function and catalytic-reaction fields cite experimental evidence from Landmann et al.; the cofactor and three-metal-ion annotations are by similarity. This sequence record does not supply experimental coordinates.

Both UniProt records are distributed under [CC BY 4.0](https://www.uniprot.org/help/license). Versions, retrieval information, and file hashes are recorded in the [enzyme source manifest](../data/enzyme-sources.json).

<a id="pdb-5uv0"></a>

**PDB 5UV0.** [*Citrus sinensis* (+)-limonene synthase](https://www.rcsb.org/structure/5UV0), primary citation Morehouse et al. (2017). RCSB entry, polymer, chain, and coordinate records retrieved on 27 October 2026 support an X-ray structure at 2.3 Å resolution with 522 modeled residues and 607 deposited polymer positions. The apo/open structure does not contain a modeled native substrate or product. Its archival sequence-conflict annotation records A245 versus V245 in an older reference; the pinned current UniProt and deposited polymer sequences both have A245 and match across all 607 positions. The metadata records no engineered mutation. The wwPDB archive is [CC0](https://www.wwpdb.org/about/usage-policies); retain the primary citation and separately attributed annotations.

## Background studies

<a id="hyatt-2007"></a>

**Hyatt et al. (2007).** Structure of limonene synthase, a simple model for terpenoid cyclase catalysis. *PNAS* **104**(13), 5360–5365. [DOI: 10.1073/pnas.0700915104](https://doi.org/10.1073/pnas.0700915104); [PMID: 17372193](https://pubmed.ncbi.nlm.nih.gov/17372193/).

Abstract and metadata inspected; full-text retrieval failed. The spearmint structure with fluorinated analogues provides a historical structural reference. It is a different enzyme from both selected entries and supplies no experimental lavender coordinates.

<a id="srividya-2015"></a>

**Srividya et al. (2015).** Functional analysis of (4S)-limonene synthase mutants reveals determinants of catalytic outcome in a model monoterpene synthase. *PNAS* **112**(11), 3332–3337. [DOI: 10.1073/pnas.1501203112](https://doi.org/10.1073/pnas.1501203112); [PMID: 25733883](https://pubmed.ncbi.nlm.nih.gov/25733883/).

Abstract and metadata inspected; full-text retrieval failed. Mutations in spearmint altered activity and product profiles. Those results do not establish a universal sequence rule or predict the effects of corresponding substitutions in citrus or lavender.

<a id="karuppiah-2017"></a>

**Karuppiah et al. (2017).** Structural Basis of Catalysis in the Bacterial Monoterpene Synthases Linalool Synthase and 1,8-Cineole Synthase. *ACS Catalysis* **7**(9), 6268–6282. [DOI: 10.1021/acscatal.7b01924](https://doi.org/10.1021/acscatal.7b01924); [PMID: 28966840](https://pubmed.ncbi.nlm.nih.gov/28966840/); [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5617326/).

Full text retrieved; relevant product, structural interpretation, and conclusion sections inspected. Bacterial bLinS produces R-linalool from GPP and trans-nerolidol from FPP in the reported assays. Its structure and domain architecture cannot stand in for lavender LaLINS. The authors explicitly describe the FGPP pose in one monomer as noncatalytic. Article license: CC BY.

<a id="crowell-2002"></a>

**Crowell et al. (2002).** Molecular cloning and characterization of a new linalool synthase. *Archives of Biochemistry and Biophysics* **405**(1), 112–121. [DOI: 10.1016/S0003-9861(02)00348-X](https://doi.org/10.1016/S0003-9861(02)00348-X); [PMID: 12176064](https://pubmed.ncbi.nlm.nih.gov/12176064/).

Abstract and metadata inspected. This paper characterizes a *Mentha citrata* R-linalool synthase. Its homology-model discussion is not experimental structural evidence for lavender.
