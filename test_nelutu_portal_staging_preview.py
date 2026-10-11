"""Static isolation guarantees for the portal-style staging wrapper."""
from pathlib import Path
import unittest


class PortalStagingTests(unittest.TestCase):
    def test_reuses_exact_preview_without_importing_live_apps(self):
        source = Path(__file__).with_name("nelutu_portal_staging_preview.py").read_text(encoding="utf-8")
        self.assertIn('runpy.run_path(str(ROOT / "nelutu_gemini_preview.py")', source)
        self.assertNotIn("app_parinti.py", source.split("runpy.run_path", 1)[1])
        self.assertNotIn("app_web_catalog.py", source.split("runpy.run_path", 1)[1])
        self.assertNotIn("NELUTU_GEMINI_API_KEY", source)
        self.assertNotIn("PostgreSQLBudget(", source)
        self.assertNotIn("set_page_config(", source)
        self.assertIn("Nu este portalul activ", source)

if __name__ == "__main__":
    unittest.main()
