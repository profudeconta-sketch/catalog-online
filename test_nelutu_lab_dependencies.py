"""Offline checks for separate laboratory dependency manifest."""
from pathlib import Path
import unittest


class LabDependenciesTests(unittest.TestCase):
    def test_optional_manifest_contains_driver(self):
        root = Path(__file__).parent
        manifest = (root / "requirements-nelutu-neon-lab.txt").read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]", manifest)
        self.assertIn("streamlit", manifest)

    def test_preview_manifest_includes_school_dependencies_and_driver(self):
        root = Path(__file__).parent
        manifest = (root / "requirements-nelutu-preview.txt").read_text(encoding="utf-8")
        self.assertIn("-r requirements.txt", manifest)
        self.assertIn("psycopg[binary]", manifest)

    def test_staging_root_manifest_includes_driver_without_database_configuration(self):
        root = Path(__file__).parent
        manifest = (root / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]", manifest)
        self.assertNotIn("NELUTU_NEON_DSN=", manifest)
        self.assertNotIn("NELUTU_GEMINI_API_KEY=", manifest)


if __name__ == "__main__":
    unittest.main()
