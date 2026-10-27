# Practical use

Terminology: [glossary](glossary.md). Scientific choices and consequences: [assumptions](assumptions.md).

## Where this fits

Use this case to learn how chemical identity, sequence correspondence, and experimental coordinates contribute different evidence about enzymes. The report and explorer support inspection and discussion. They do not accept arbitrary uploads, predict odor, or prescribe a laboratory experiment.

## Input and output contract

Use Python 3.12 and the versions in `requirements.txt`. The analysis reads the bundled source snapshots and curated case definitions. Keep their original bytes and attribution; do not replace a snapshot merely because its live database record has changed.

`run.py` accepts `--output-dir PATH`, optional `--overwrite`, and optional `--web-data PATH.js`. It reads this fixed case rather than accepting a new molecule or enzyme file. The [methods](methods.md#outputs-and-reproducibility) list the ten artifacts and their manifest.

The output directory must be new or empty. A nonempty directory requires `--overwrite` and a recognized result manifest containing exactly the project’s expected artifact inventory; unknown files and symlinks cause refusal. This check identifies the bundle layout, not the scientific validity of its contents. Choose a new directory to preserve an earlier result. Omitting `--output-dir` selects `results/`, whose recorded files likewise require an explicit overwrite.

The generator stages its calculations before copying files. Final copying is per file, not one atomic directory replacement. If interrupted, treat the output as incomplete until verification passes. A successful run exits with status 0; handled input, validation, or filesystem errors exit with status 2 and print a diagnostic.

The optional `--web-data web/data.js` writes the explorer’s prepared dataset after generating the result bundle. That `.js` file must be outside both the source data and the result directory, and its path must not use symlinks. An existing destination must contain a recognized `window.PERFUME_DATA` payload for this case; the generator refuses to replace other JavaScript files. It writes a temporary file beside the destination, then atomically replaces that one file.

Without this option, a reproduction run leaves the prepared explorer unchanged. Serving `web/` therefore displays its bundled data, not whichever output directory you generated most recently.

## Worked use case

From the repository root, with dependencies installed:

```sh
python run.py --output-dir .reproduction
python verify_results.py --results-dir .reproduction
```

Read the generated report first. Check the compound identities and stereochemistry, then the atom correspondence. Inspect the sequence-alignment denominator before reading a percentage, and check which experimental atoms support the structural result. Keep the source record, computed result, and biological interpretation separate.

To inspect the prepared explorer:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory web
```

Open <http://127.0.0.1:8000/>. Use the linked tables and source records to follow the evidence behind each view. The explorer is a presentation of this fixed case, not a live database query or a general molecular viewer.

For the recorded case, the alignment has 243 identical pairs among 560 paired-residue columns: 43.39% identity. Dividing by all 611 columns instead gives 39.77%. This difference reflects the denominator, not a change in enzyme function. The citrus structure contributes 522 modeled Cα positions; no lavender structure is added to fill the evidence gap.

If you intentionally refresh the explorer after a reviewed code change, generate a new bundle and pass `--web-data web/data.js` explicitly. Keep the result bundle and its matching payload together when assessing the page. Check their agreement with:

```sh
python verify_results.py --results-dir .reproduction --web-dir web
```

Use that command only after generating the matching payload, or verify the prepared `web/` payload against its matching recorded `results/`. A payload from a different bundle should fail. `--json` prints a receipt; the verifier does not alter files. Status 0 means its stated checks passed; status 2 means a handled validation or read failure. The [methods](methods.md#independent-verification) specify its independent calculations and shared-library limits.

## Checks before relying on a result

- Confirm the source identifiers, versions, selected stereochemistry, chains, and constructs.
- Run the verifier on the output directory you actually generated.
- Check the atom-map convention, alignment settings, metric denominators, and missing-coordinate treatment.
- Read the source-access limits in the reference audit before repeating a biological claim.
- Preserve source attribution and distinguish generated files from original snapshots.

## Known limits

This is a selected case, not a representative sample of terpene enzymes. The atom correspondence is curated, and the sequence and structural calculations depend on the declared selections. The project does not simulate catalysis, infer a product distribution, estimate enzyme activity, or test whether a variant improves a function.

There are no sensory measurements or odor-prediction labels. A successful graph parse, sequence alignment, or coordinate check does not establish how a compound, mixture, or organism smells. The workflow also does not validate a laboratory procedure or the completeness of a literature search.

## Next improvements

1. **Broader enzyme comparison:** define inclusion rules for independently characterized enzymes before adding cases. Acceptance requires traceable sequences, assay context, and separate reporting of measured and annotated functions.
2. **Atom-map review:** have an independent chemistry reader assess each correspondence against the cited evidence. Acceptance requires documenting ambiguous or unsupported mappings rather than choosing the most convenient picture.
3. **Structure sensitivity:** compare justified chain and residue selections. Acceptance requires reporting coverage and how each selection changes the result, without selecting a subset solely to improve agreement.
4. **Reader evaluation:** test whether a new reader can trace a report claim to its source and reproduce the fixed case. Acceptance requires recorded tasks and observed failures; passing software tests is not a substitute.
