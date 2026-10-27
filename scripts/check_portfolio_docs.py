"""Check documentation contracts in local portfolio checkouts; no network access."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

README_HEADINGS = [
    "Why this project", "What it does", "Quick start", "Example results",
    "Practical use and limitations", "Documentation", "Development and reuse",
]
PRACTICAL_HEADINGS = [
    "Where this fits", "Input and output contract", "Worked use case",
    "Checks before relying on a result", "Known limits", "Next improvements",
]
REVIEW_HEADINGS = [
    "Question and scope", "Search record", "What the sources support",
    "Changes made", "Remaining work", "Limits of this review",
]
SEARCH_KEYS = {"search_date", "scope", "inclusion_criteria", "exclusion_criteria",
               "searches", "screening"}


def without_fences(text: str) -> str:
    """Ignore code examples while checking Markdown headings and links."""
    lines, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token[0]
            elif token[0] == fence:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)


def inspect_markdown(path: Path, expected: list[str]) -> list[str]:
    if not path.is_file():
        return [f"Missing file: {path.name}"]
    text = without_fences(path.read_text(encoding="utf-8"))
    headings = re.findall(r"^## (.+?)\s*$", text, re.MULTILINE)
    errors = []
    if headings != expected:
        errors.append(f"{path.name}: level-2 headings must match the shared order")
    for raw in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
        target = urlsplit(raw.strip("<>"))
        if target.scheme or target.netloc or not target.path:
            continue
        linked = path.parent / unquote(target.path)
        if not linked.exists():
            errors.append(f"{path.name}: missing relative link target {raw}")
    return errors


def unique_object(pairs):
    """Reject duplicate keys instead of silently accepting the last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def inspect_search_log(path: Path) -> list[str]:
    errors = []
    label = path.name
    try:
        record = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(record, dict):
            raise ValueError("search log must be an object")
        missing = SEARCH_KEYS - record.keys()
        if missing:
            errors.append(label + ": missing " + ", ".join(sorted(missing)))
        if "search_date" in record:
            parsed = date.fromisoformat(record["search_date"])
            if parsed.isoformat() != record["search_date"]:
                errors.append(label + ": use YYYY-MM-DD")
        if not isinstance(record.get("searches"), list) or not record.get("searches"):
            errors.append(label + ": searches must be a nonempty list")
        if not isinstance(record.get("screening"), (list, dict)) or not record.get("screening"):
            errors.append(label + ": screening must record decisions")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"{label}: {exc}")
    return errors


def inspect_repository(root: Path, required_update: str | None = None) -> list[str]:
    errors = []
    for relative, headings in [
        ("README.md", README_HEADINGS),
        ("docs/practical-use.md", PRACTICAL_HEADINGS),
        ("docs/literature-review.md", REVIEW_HEADINGS),
    ]:
        errors.extend(inspect_markdown(root / relative, headings))
    paths = {root / "docs/search-log.json"}
    paths.update((root / "docs").glob("search-update-*.json"))
    if required_update is not None:
        paths.add(root / "docs" / f"search-update-{required_update}.json")
    for path in sorted(paths):
        errors.extend(inspect_search_log(path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True,
                        help="Directory containing one checkout per repository slug")
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "portfolio.json")
    parser.add_argument("--output", type=Path,
                        help="Optional JSON report, overwritten if it exists")
    parser.add_argument("--require-update", type=str,
                        help="Require a numbered search update in every repository (for example 02)")
    parser.add_argument("--editorial-review", type=str,
                        help="Also check glossary, assumptions, source-audit fields and authored-document links for YYYY-MM-DD")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if args.require_update is not None and not re.fullmatch(r"[0-9]+", args.require_update):
            raise ValueError("required update must contain only digits")
        repositories = manifest["repositories"]
        if not isinstance(repositories, list) or not repositories:
            raise ValueError("repositories must be a nonempty list")
        if any(not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", s)
               or s in {".", ".."} for s in repositories):
            raise ValueError("repository names must be safe directory names")
        if len(set(repositories)) != len(repositories):
            raise ValueError("repository names must be unique")
        results = [{"repository": slug, "errors": inspect_repository(args.root / slug, args.require_update)}
                   for slug in repositories]
        if args.editorial_review:
            try:
                from .editorial_checks import inspect_editorial_review
            except ImportError:
                from editorial_checks import inspect_editorial_review
            for result in results:
                result["errors"].extend(inspect_editorial_review(args.root / result["repository"], args.editorial_review))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    report = {"schema_version": 1, "checks": "documentation structure and local links only",
              "repositories": results, "passed": all(not r["errors"] for r in results)}
    if args.editorial_review:
        report["checks"] = "Documentation structure, authored-document links/anchors and source-audit fields; not scientific validity"
        report["editorial_review"] = args.editorial_review
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['repository']}: {'PASS' if not result['errors'] else 'FAIL'}")
        for error in result["errors"]:
            print(f"  {error}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
