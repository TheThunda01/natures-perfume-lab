"""Export or verify the three computed molecular illustrations for Avogadro."""
import argparse
import json
from pathlib import Path
from perfume_lab.inspection import export_bundle, verify_bundle

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output-dir", type=Path, help="New destination; existing folders are refused")
    mode.add_argument("--verify-dir", type=Path, help="Read-only verification of a saved bundle")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        result = export_bundle(root, args.output_dir) if args.output_dir else verify_bundle(root, args.verify_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Molecular inspection stopped: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
