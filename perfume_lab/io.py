"""Small input checks shared by the analysis, not by its independent verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path):
    def invalid(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique,
                      parse_constant=invalid)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def safe_file(root: Path, relative: str) -> Path:
    part = Path(relative)
    if part.is_absolute() or not part.parts or any(x in {"..", "."} for x in part.parts):
        raise ValueError(f"Unsafe source path: {relative}")
    path = root / part
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError(f"Symlink is not an accepted source: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing or external source: {relative}")
    return path


def verify_sources(root: Path) -> dict:
    from .constants import SOURCE_MANIFEST_SHA256
    path = safe_file(root, "data/provenance.json")
    if sha256(path) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Source manifest differs from the pinned inventory")
    manifest = read_json(path)
    if manifest.get("schema_version") != 1 or not manifest.get("files"):
        raise ValueError("Unsupported or empty source manifest")
    seen = set()
    for item in manifest["files"]:
        relative = item["path"]
        if relative in seen:
            raise ValueError(f"Duplicate source path: {relative}")
        seen.add(relative)
        source = safe_file(root, relative)
        if source.stat().st_size != item["bytes"] or sha256(source) != item["sha256"]:
            raise ValueError(f"Source fingerprint mismatch: {relative}")
    return manifest
