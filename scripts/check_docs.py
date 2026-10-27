"""Run the same documentation contracts used by the existing portfolio."""
from pathlib import Path
from check_portfolio_docs import inspect_repository
from editorial_checks import inspect_editorial_review, local_link_errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = inspect_repository(root)
    errors.extend(inspect_editorial_review(root, "2026-10-27"))
    if (root / "results/report.md").is_file():
        errors.extend(local_link_errors(root / "results/report.md"))
    if errors:
        for error in errors:
            print(error)
        return 1
    print("PASS: portfolio structure, source-audit fields, and local documentation links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
