#!/usr/bin/env python3
"""Reproduce Nature's Perfume Lab from pinned local source snapshots."""
from pathlib import Path
import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--overwrite", action="store_true", help="Replace a recognized prior result bundle; refuse unknown files")
    parser.add_argument("--web-data", type=Path, help="Explicitly write a static explorer data.js file")
    args = parser.parse_args()
    try:
        from perfume_lab.pipeline import run
        output = run(Path(__file__).resolve().parent, args.output_dir, args.overwrite, args.web_data)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Analysis stopped: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote and fingerprinted {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
