"""Regression checks for preserving files outside a recognized generated bundle."""
import json
from pathlib import Path
import tempfile
import unittest

from perfume_lab.pipeline import ARTIFACTS, check_destination, check_web_destination, run


class OutputProtectionTests(unittest.TestCase):
    def test_mistyped_web_destination_does_not_erase_application_or_create_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "app.js"
            original = "document.title = 'my application';\n"
            app.write_text(original)
            with self.assertRaisesRegex(ValueError, "not a recognized explorer payload"):
                run(root, root / "results", web_data=app)
            self.assertEqual(app.read_text(), original)
            self.assertFalse((root / "results").exists())

    def test_payload_path_cannot_target_sources_results_or_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for destination in (root / "data" / "data.js", root / "results" / "data.js"):
                with self.assertRaisesRegex(ValueError, "outside"):
                    check_web_destination(root, root / "results", destination)
            original = root / "application.js"
            original.write_text("const x = 1;\n")
            link = root / "alias.js"
            try:
                link.symlink_to(original)
            except OSError as exc:
                self.skipTest(f"This environment cannot create a symbolic link: {exc}")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                check_web_destination(root, root / "results", link)

    def test_results_overwrite_rejects_unrecognized_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ARTIFACTS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("saved artifact")
            (root / "manifest.json").write_text(json.dumps({"schema_version": 1, "files": [{"path": name} for name in ARTIFACTS]}))
            valuable = root / "notes.txt"
            valuable.write_text("Keep this manual note")
            with self.assertRaisesRegex(ValueError, "unrecognized files"):
                check_destination(root, overwrite=True)
            self.assertEqual(valuable.read_text(), "Keep this manual note")


if __name__ == "__main__":
    unittest.main()
