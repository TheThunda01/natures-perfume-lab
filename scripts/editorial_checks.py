"""Mechanical checks for an editorial review; these do not assess scientific truth."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

try:
    from .check_portfolio_docs import unique_object, without_fences
except ImportError:  # Direct invocation through scripts/check_portfolio_docs.py.
    from check_portfolio_docs import unique_object, without_fences

ACCESS_LEVELS = {"full_text", "abstract", "official_documentation", "metadata_only", "unavailable"}
METADATA_STATES = {"verified", "corrected", "unresolved"}
FIELDS = {"id", "source_type", "title", "authors", "year", "url", "checked_on",
          "access_level", "metadata_status", "supported_claims", "limitations", "corrections"}


def heading_ids(text: str) -> set[str]:
    """Approximate GitHub heading slugs for ordinary authored Markdown headings."""
    seen: dict[str, int] = {}
    result = set()
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", without_fences(text), re.MULTILINE):
        title = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", title)
        title = re.sub(r"<[^>]+>", "", title).lower().strip()
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        suffix = seen.get(slug, 0)
        seen[slug] = suffix + 1
        result.add(slug if suffix == 0 else f"{slug}-{suffix}")
    result.update(re.findall(r'<(?:a|h[1-6])\b[^>]*(?:id|name)=["\']([^"\']+)', text, re.I))
    return result


def local_link_errors(path: Path) -> list[str]:
    errors = []
    text = without_fences(path.read_text(encoding="utf-8"))
    for raw in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
        target = urlsplit(raw.strip("<>"))
        if target.scheme or target.netloc:
            continue
        linked = path if not target.path else path.parent / unquote(target.path)
        if not linked.exists():
            errors.append(f"{path}: missing local target {raw}")
        elif target.fragment and linked.suffix.lower() == ".md":
            if unquote(target.fragment) not in heading_ids(linked.read_text(encoding="utf-8")):
                errors.append(f"{path}: missing Markdown heading {raw}")
    return errors


def authored_markdown(root: Path) -> list[Path]:
    """Current guides and examples; immutable upstream copies are not edited here."""
    # TEMPLATE_ORIGIN.md is the preserved upstream template, not an active guide.
    roots = [p for p in root.glob("*.md")
             if p.name not in {"LICENSE.md", "TEMPLATE_ORIGIN.md"}]
    for name in ("docs", "examples", "experiments"):
        directory = root / name
        if directory.exists():
            roots.extend(p for p in directory.rglob("*.md")
                         if not any(part.startswith(".") for part in p.relative_to(root).parts)
                         and "results" not in p.relative_to(root).parts)
    data_readme = root / "data" / "README.md"
    if data_readme.is_file():
        roots.append(data_readme)
    return sorted(set(roots))


def audit_errors(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(data, dict):
            raise ValueError("audit must be an object")
        for key in ("review_date", "scope", "limits", "references"):
            if key not in data:
                errors.append(f"{path.name}: missing {key}")
        if "review_date" in data:
            date.fromisoformat(data["review_date"])
        refs = data.get("references")
        if not isinstance(refs, list) or not refs:
            return errors + [f"{path.name}: references must be a nonempty array"]
        ids = set()
        for index, ref in enumerate(refs):
            label = f"{path.name}: reference {index + 1}"
            if not isinstance(ref, dict):
                errors.append(label + " must be an object")
                continue
            missing = FIELDS - ref.keys()
            if missing:
                errors.append(label + ": missing " + ", ".join(sorted(missing)))
            key = ref.get("id")
            if not isinstance(key, str) or not key.strip() or key in ids:
                errors.append(label + ": id must be nonblank and unique")
            if isinstance(key, str):
                ids.add(key)
            for field in ("source_type", "title"):
                if not isinstance(ref.get(field), str) or not ref[field].strip():
                    errors.append(label + f": {field} must be nonblank")
            if not isinstance(ref.get("authors"), (str, list)) or not ref.get("authors"):
                errors.append(label + ": authors/organization must be recorded")
            year = ref.get("year")
            if year is not None and (type(year) is not int or not 1000 <= year <= 9999):
                errors.append(label + ": year must be a four-digit integer or null")
            url = ref.get("url", "")
            if not isinstance(url, str) or urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).netloc:
                errors.append(label + ": canonical URL must be HTTP(S)")
            try:
                date.fromisoformat(ref.get("checked_on", ""))
            except (TypeError, ValueError):
                errors.append(label + ": invalid checked_on date")
            if ref.get("access_level") not in ACCESS_LEVELS:
                errors.append(label + ": unknown access_level")
            if ref.get("metadata_status") not in METADATA_STATES:
                errors.append(label + ": unknown metadata_status")
            for field in ("supported_claims", "limitations", "corrections"):
                values = ref.get(field)
                if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
                    errors.append(label + f": {field} must be an array of nonblank strings")
            if not ref.get("supported_claims"):
                errors.append(label + ": source role/support must be recorded")
            if ref.get("access_level") in {"metadata_only", "unavailable"} and not ref.get("limitations"):
                errors.append(label + ": access limitations must be explicit")
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"{path.name}: {exc}")
    return errors


def inspect_editorial_review(root: Path, review_date: str) -> list[str]:
    errors = []
    try:
        date.fromisoformat(review_date)
    except ValueError:
        return ["Editorial review date must use YYYY-MM-DD"]
    guides = ("docs/glossary.md", "docs/assumptions.md", f"docs/review-{review_date}.md")
    for relative in guides:
        path = root / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"Missing or empty review guide: {relative}")
    errors.extend(audit_errors(root / "docs/reference-audit.json"))
    for path in authored_markdown(root):
        errors.extend(local_link_errors(path))
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        for relative in (*guides, "docs/reference-audit.json"):
            if relative not in text:
                errors.append(f"README.md: review guide is not linked: {relative}")
    return errors
