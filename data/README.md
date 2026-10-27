# Data sources and attribution

This project compares two experimentally characterized plant enzymes that use
geranyl diphosphate (GPP). The source files are public database snapshots retrieved
on 27 October 2026. Their manifests record the original URLs, retrieval dates,
byte counts and SHA-256 hashes. Re-running the analysis uses these local files;
it does not silently replace them with newer database records.

## What is included

| Source | Records | Local files | Purpose |
| --- | --- | --- | --- |
| UniProt Consortium | [A0A1C9J6A7](https://www.uniprot.org/uniprotkb/A0A1C9J6A7/entry), *Citrus sinensis*; [Q2XSC5](https://www.uniprot.org/uniprotkb/Q2XSC5/entry), *Lavandula angustifolia* | `sources/uniprot_*.json` and `sources/uniprot_*.fasta` | Canonical sequences, names, annotation evidence and source publications |
| wwPDB and RCSB PDB | [5UV0](https://www.rcsb.org/structure/5UV0), orange (+)-limonene synthase | `sources/5uv0.cif` and `sources/rcsb_5UV0_*.json` | Experimental coordinates, construct mapping and model coverage |
| NCBI PubChem | GPP [CID 445995](https://pubchem.ncbi.nlm.nih.gov/compound/445995), R-limonene [CID 440917](https://pubchem.ncbi.nlm.nih.gov/compound/440917), R-linalool [CID 443158](https://pubchem.ncbi.nlm.nih.gov/compound/443158), diphosphoric acid [CID 1023](https://pubchem.ncbi.nlm.nih.gov/compound/1023), water [CID 962](https://pubchem.ncbi.nlm.nih.gov/compound/962) | `sources/*.pubchem.json` | Chemical identifiers, formulas and stereochemical structures |

[enzyme-sources.json](enzyme-sources.json) records the enzyme downloads;
[compound-sources.json](sources/compound-sources.json) records the chemical
downloads. The enzyme snapshots preserve the HTTP response bodies unchanged.

[enzymes.json](curated/enzymes.json) selects database fields and adds source-linked
interpretation notes. [chemistry.json](curated/chemistry.json) declares the
stereochemical structures, carbon maps, neutral-species equations and assumptions
used in the analysis. These curated files are project adaptations, not records
issued by the source databases.

## Terms of reuse

- **UniProt:** the UniProt Consortium applies [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  to copyrightable database content. Retain attribution to UniProt, links to the
  source entries and license, and an indication of any changes. See the
  [UniProt license policy](https://www.uniprot.org/help/license).
- **PDB coordinates:** wwPDB distributes PDB archive files under
  [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Credit the
  experimental authors and PDB accession when using the structure. See the
  [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies).
- **RCSB API metadata:** RCSB applies the PDB policy to its API data, while
  annotations integrated from external resources retain their source terms.
  The metadata here include UniProt annotations, so retain their attribution
  as well. See the [RCSB policies](https://www.rcsb.org/pages/policies).
- **PubChem:** the [NCBI data policy](https://www.ncbi.nlm.nih.gov/home/about/policies/#data)
  places no restrictions on use or distribution of molecular data, while noting
  that submitters may assert rights. The downloaded property responses provide
  no record-specific license; this project does not label them CC0. They contain
  chemical identifiers and computed properties, not contributed descriptive text.
  Credit PubChem, NCBI and the National Library of Medicine.

The repository's software license does not replace these source terms. Research
articles are cited below; their full text and figures are not redistributed here.

## Experimental evidence and its limits

Both pinned UniProt entries are reviewed. That status is separate from the
evidence for each annotation: measured catalytic activity, curator inference and
annotations transferred by similarity are not interchangeable.

- **Orange limonene synthase:** Morehouse and colleagues reported 99% limonene,
  0.7% myrcene and 0.3% alpha-pinene in the GPP product mixture. The limonene was
  exclusively the (+), R enantiomer; limonene was not the only product. The
  cyclic-product fraction, including alpha-pinene, is therefore 99.3%, distinct
  from the 99% limonene fraction. These are reported assay results, not predicted
  yields for other conditions.
- **Lavender linalool synthase:** the Landmann paper's abstract reports that
  LaLINS produces exclusively (R)-(−)-linalool. This project inspected that
  abstract and the reviewed UniProt annotations, not the primary full text or
  a quantitative product table. The paper's separate LaLIMS enzyme must not be
  confused with LaLINS. UniProt's cofactor and metal-binding annotations for
  Q2XSC5 are by similarity (`ECO:0000250`), whereas its function and catalytic
  activity cite experimental evidence (`ECO:0000269`).

The orange precursor has 607 residues. The reported experimental construct
removes residues 1–52 and replaces them with a His6 tag; the paper reports a
562-residue purified construct including the tag. PDB 5UV0 retains the full
607-residue reference sequence but models 522 residues: 60–218, 226–573 and
578–592. Its unmodeled reference positions include the removed targeting segment
and therefore cannot all be described as experimental disorder.

5UV0 is an open apo model at 2.3 Å. It contains 174 modeled water molecules and no
modeled metal, substrate or product. Unassigned active-site density discussed in
the paper is not treated as an identified ligand. The archival mmCIF retains an
ALA245/VAL245 sequence-conflict annotation, but the pinned current UniProt
sequence and PDB entity sequence agree at all 607 positions, including ALA245.
That historical annotation is not evidence of a current mismatch or an engineered
mutation.

The pinned Q2XSC5 entry has no PDB cross-reference. No experimental coordinates
or predicted protein model are included for lavender linalool synthase. This
bounded source finding does not prove that no experimental structure exists
anywhere; it means this project cannot compare the two experimental pockets.
Sequence similarity between this pair also cannot establish which residues
determine product specificity.

Chemical carbon maps are explicitly curated, and the compound file documents
their symmetry and stereochemical limits. Neutral chemical formulas support
formula and charge checks; they do not claim physiological protonation or proton
stoichiometry. Carbon-label illustrations do not simulate isotope enrichment,
reaction kinetics or measured flux.

## Primary references

- Morehouse BR, Kumar RP, Matos JO, Olsen SN, Entova S, Oprian DD. Functional and
  Structural Characterization of a (+)-Limonene Synthase from *Citrus sinensis*.
  *Biochemistry*. 2017;56(12):1706–1715.
  [doi:10.1021/acs.biochem.7b00143](https://doi.org/10.1021/acs.biochem.7b00143).
  [PMID 28272875](https://pubmed.ncbi.nlm.nih.gov/28272875/);
  [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC5642283/).
- Landmann C, Fink B, Festner M, Dregus M, Engel KH, Schwab W. Cloning and
  functional characterization of three terpene synthases from lavender
  (*Lavandula angustifolia*). *Archives of Biochemistry and Biophysics*.
  2007;465(2):417–429.
  [doi:10.1016/j.abb.2007.06.011](https://doi.org/10.1016/j.abb.2007.06.011).
  [PMID 17662687](https://pubmed.ncbi.nlm.nih.gov/17662687/).
