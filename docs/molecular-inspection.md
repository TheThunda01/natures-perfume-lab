# Inspecting the curated molecules in Avogadro

The molecular-viewer export makes the existing chemical case inspectable in a desktop editor. It adds no compounds, measurements, reaction mechanism, or energy calculation.

## Files and reproduction

Use the normal pinned Python requirements. From the repository root:

```sh
python export_molecules.py --output-dir .reproduction/molecular-inspection
python export_molecules.py --verify-dir .reproduction/molecular-inspection
```

The first command requires a new destination outside `data/`; it refuses existing destinations and symlink paths. The second reads the bundle without changing it. It checks source and curation fingerprints, file hashes, molecular graphs, physical stereochemistry, carbon atom-map numbers, provenance fields, and drawing coordinates to the SDF rounding tolerance. It recomputes the layout with the recorded RDKit version. A successful command exits with 0; handled validation/read errors exit with 2. The checked-in [example](../examples/molecules/README.md) can be verified with `--verify-dir examples/molecules`.

Each SDF contains one molecule, with heavy atoms and implicit hydrogens. Its properties identify the PubChem record, source fingerprint, coordinate scope, protonation convention, and carbon-label convention. The receipt binds the three SDF files to the pinned source manifest and curation. An optional README is descriptive and is not authenticated by the receipt.

## Why the export is two-dimensional

The SDF coordinates are a structure drawing, in drawing units. They are not experimental positions, an enzyme-bound pose, or a preferred solution conformation. Wedge/bond annotations preserve the selected R product stereochemistry and GPP double-bond geometry.

Neutral GPP has an unspecified phosphorus stereocenter in this source representation. A 3D SDF reader can infer a specific phosphorus configuration from an arbitrary display conformer. The 2D export avoids adding that claim. The interactive explorer's computed display conformers retain their separate limitations; they are not exported as experimentally resolved stereochemical information.

Carbon atom-map numbers 1–10 retain the curated lineage labels. They are not the viewer's atom indices or universal chemical numbering. A viewer may display its own sequential atom labels and may not expose the map field directly. The verifier checks the saved SDF map, independently of the displayed label style.

## Viewer walkthrough

1. Open an individual SDF from the bundle using Avogadro's file-open action.
2. Check its formula and compare connectivity and stereochemistry with the [existing numbered drawings](../results/molecules/gpp.svg) and [curation](../data/curated/chemistry.json).
3. Preserve the original bundle. Save any edits or generated conformers to a different folder; a changed file should fail the original verification.

Avogadro 2.1.0 imported all three files during the 27 October 2026 check. Its importer added explicit hydrogens: the reported counts were 39 atoms for GPP (`C10H20O7P2`), 26 for limonene (`C10H16`), and 29 for linalool (`C10H18O`). This check confirms import and formula/count agreement. It does not establish preservation of every SDF property after a viewer edit/export, or validate a computed conformation. Re-verify any derivative with an appropriate independent method before relying on it.

The source attribution and reuse conditions remain in [data/README.md](../data/README.md). The [Avogadro documentation](https://avogadro.cc/docs/) describes the viewer; it is not evidence for this case's chemical or biological claims.
