# Curated molecular structures for inspection

Open [GPP](gpp.sdf), [R-limonene](limonene.sdf), or [R-linalool](linalool.sdf) in a molecular viewer such as Avogadro. These are 2D layouts with the original carbon atom-map labels and selected stereochemistry, not measured or computed 3D conformations. Source identifiers and fingerprints are embedded in each file and in [receipt.json](receipt.json).

From the repository root:

```sh
python export_molecules.py --verify-dir examples/molecules
```

The [inspection guide](../../docs/molecular-inspection.md) records reproduction, import checks, protonation and stereochemical limitations. Preserve this bundle when editing in another application. The README is explanatory; the verifier checks the SDF files and receipt. Follow the source [attribution and reuse terms](../../data/README.md).
