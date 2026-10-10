"""Static regression checks: the separately deployed landing page is offline."""
from pathlib import Path
import unittest


class LabPreviewSafetyTests(unittest.TestCase):
    def test_page_has_no_database_or_provider_execution(self):
        source = Path(__file__).with_name("nelutu_neon_lab_preview.py").read_text(encoding="utf-8")
        for forbidden in (
            "psycopg", "st.button(", "st.secrets", "lab_remaining(",
            "lab_reserve(", "IsolatedLabBudget(", "gemini.generate",
            "app_web_catalog", "app_parinti", "NELUTU_NEON_LAB_TEST_DSN",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertIn("st.set_page_config", source)
        self.assertIn("accesul la baza de date este dezactivat", source)

    def test_no_private_access_claim(self):
        source = Path(__file__).with_name("nelutu_neon_lab_preview.py").read_text(encoding="utf-8")
        self.assertIn("O adresă web diferită nu înseamnă acces privat", source)


if __name__ == "__main__":
    unittest.main()
