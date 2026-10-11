"""Offline checks for separate experimental Streamlit deployment."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class PreviewDeploymentTests(unittest.TestCase):
    def test_entrypoint_uses_existing_preview_only(self):
        source = (ROOT / "nelutu_preview_deploy" / "app.py").read_text(encoding="utf-8")
        self.assertIn("nelutu_gemini_preview.py", source)
        self.assertNotIn("app_parinti.py", source)
        self.assertNotIn("app_web_catalog.py", source)

    def test_deployment_manifest_isolated(self):
        manifest = (ROOT / "nelutu_preview_deploy" / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]", manifest)
        self.assertIn("-r ../requirements.txt", manifest)
        school = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("psycopg", school)

if __name__ == "__main__":
    unittest.main()
