"""Offline checks for separate laboratory dependency manifest."""
from pathlib import Path
import unittest


class LabDependenciesTests(unittest.TestCase):
    def test_optional_manifest_contains_driver(self):
        root = Path(__file__).parent
        manifest = (root / "requirements-nelutu-neon-lab.txt").read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]", manifest)
        self.assertIn("streamlit", manifest)

    def test_school_manifest_not_extended_with_lab_driver(self):
        root = Path(__file__).parent
        manifest = (root / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("psycopg", manifest)


if __name__ == "__main__":
    unittest.main()
