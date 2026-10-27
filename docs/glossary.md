# Glossary

These definitions describe how terms are used in this project. They do not substitute for the selected source records or experimental context.

| Term | Meaning here |
| --- | --- |
| Precursor | A starting compound used in a chemical transformation. |
| GPP | Geranyl diphosphate, the shared ten-carbon starting compound in this case. |
| Monoterpene | A member of the ten-carbon terpene family. Oxygen-containing derivatives are often called monoterpenoids; terminology varies by source. |
| Limonene | A cyclic ten-carbon compound. Its stereochemical form must be specified when interpreting a selected record. |
| Linalool | An acyclic ten-carbon alcohol. Its stereochemical form must likewise be specified. |
| Connectivity | Which atoms are bonded to which, including the represented bond types. |
| Stereochemistry | How atoms are arranged in space when connectivity alone does not distinguish molecules. |
| Enantiomers | Molecules related as nonsuperposable mirror images. This relationship alone does not quantify their biological or sensory differences. |
| SMILES | Simplified Molecular Input Line Entry System, a text representation of a molecular graph; it can include charges and stereochemistry. |
| InChIKey | A hashed identifier derived from a standardized InChI chemical representation. It supports identity checks, not experimental validation. |
| Atom map | Labels connecting a declared atom correspondence across molecular graphs. A map is not proof of a reaction mechanism. |
| Formal charge | A charge assigned within a molecular representation. It is distinct from a measured charge distribution. |
| Enzyme | A biological catalyst. A record's function annotation and an activity measurement provide different kinds of evidence. |
| Sequence | An ordered string of amino-acid residues. A reference sequence can differ from an experimental construct. |
| Construct | The molecular form used in an experiment, which may be shortened, modified, or tagged. |
| Pairwise alignment | A correspondence between two sequences chosen under a scoring rule. |
| Identity | The number of identical aligned residues divided by an explicitly stated denominator. |
| Gap | A position introduced by an alignment where one sequence has no corresponding residue. It does not by itself establish an insertion or deletion event. |
| Chain | A labeled polymer instance in a structure record. A chain label need not match numbering in a reference sequence. |
| Ligand / analogue | A bound molecule / a related molecule used to examine a system. Neither label establishes that turnover occurred. |
| Experimental structure | A model of atomic positions supported by an experimental method. Missing or uncertain coordinates remain limitations. |
| Cα | Alpha carbon, the backbone carbon used in many protein-structure comparisons. |
| Å | Ångström, a unit of length equal to $`10^{-10}`$ meters. |
| Apo structure | A structure described without its catalytic substrate or ligand state; other crystallization molecules can still be present. Read the specific source record. |
| ETKDG | Experimental-torsion knowledge distance geometry, the RDKit conformer-generation method used here for display, not for a reaction trajectory. |
| MMFF94 | A molecular-mechanics force field used here to relax display conformers. Its use does not validate a reaction mechanism or reactive energy calculation. |
| mmCIF | Macromolecular Crystallographic Information File, the format used for the experimental protein coordinates and their labels. |
| SVG | Scalable Vector Graphics, the format used for molecular drawings and figures. |
| RDKit | An open-source toolkit for representing and analyzing molecular graphs. |
| Biopython | An open-source collection of tools for biological data, including sequence alignment and structure parsing. |
| Provenance | A record of where an input came from and how it was processed. |
| SHA-256 / fingerprint | A fixed-length value calculated from exact file bytes. It can detect byte changes but is not a signature or proof of origin. |
| Pinned snapshot | A saved source version used consistently for this analysis. It need not be the latest live record. |
| CSV / JSON | Comma-separated table / JavaScript Object Notation structured text. These formats do not establish scientific validity. |
| Static explorer | A browser page that displays prepared files without an analysis server. |
| Independent verification | Separate checks of specified outputs and calculations. The methods document explains which steps are independent and which share inputs or libraries. |

See [methods](methods.md) for exact calculations and [assumptions](assumptions.md) for their interpretation limits.
