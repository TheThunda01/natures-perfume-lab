# Contributing

Keep changes focused on a question a reader can inspect and reproduce. Explain the problem, the proposed behavior, and the evidence supporting the change. Use the [methods](docs/methods.md) and [practical-use contract](docs/practical-use.md) to understand the current scope.

For a code change, provide a small failing example when possible and run:

```sh
python -m unittest discover -s tests -v
python run.py --output-dir .reproduction
python verify_results.py --results-dir .reproduction
python scripts/check_docs.py
```

For explorer changes, also check the recorded payload with `python verify_results.py --results-dir results --web-dir web` and run the optional browser smoke test:

```sh
python -m pip install playwright==1.62.0
python -m playwright install chromium
python scripts/browser_smoke.py
```

The browser test starts its own temporary loopback server. It checks carbon selection, route and rotation controls, content, viewport fit, page errors, and external asset requests. Add `--screenshots /tmp/perfume-browser` to save screenshots. Playwright is a development dependency, separate from the analysis requirements; the GitHub Actions workflow does not run this browser check.

For documentation changes, check local links and preserve commands, identifiers, units, denominators, citations, and the strength of each claim. Follow the [editorial record](docs/review-2026-10-27.md): lead with the point, use precise verbs, and separate observation from interpretation.

A source update is a new input revision. Preserve the earlier provenance, inspect changed bytes and records, and explain any effect on results. Do not replace a checksum just to silence a failing check. Keep code licensing separate from source-data attribution and reuse terms.

A new enzyme or chemical case needs a defined selection rule and its own source review. Do not infer a product profile, catalytic effect, or sensory outcome from a convenient sequence match or structural picture. Tests establish specified software behavior; experimental claims need appropriate evidence.

Describe any AI assistance and verify its suggestions against code, source records, and executed checks. Do not add credentials, confidential records, or restricted source material to the repository. See [SECURITY.md](SECURITY.md) for reporting a suspected vulnerability.
