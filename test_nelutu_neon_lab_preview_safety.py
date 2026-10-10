"""Static safety checks for isolated lab UI, without importing Streamlit."""
from pathlib import Path
import unittest


class LabPreviewSafetyTests(unittest.TestCase):
    def test_no_write_controls_or_provider_calls(self):
        source = Path(__file__).with_name("nelutu_neon_lab_preview.py").read_text(encoding="utf-8")
        self.assertIn("nelutu_streamlit_lab_gate", source)
        self.assertNotIn("st.button(", source)
        self.assertNotIn("lab_reserve(config)", source)
        self.assertNotIn("demo_prompt(", source)
        self.assertNotIn("app_web_catalog", source)
        self.assertNotIn("app_parinti", source)
        self.assertNotIn("st.write(config.dedicated_dsn)", source)

    def test_disabled_by_default(self):
        source = Path(__file__).with_name("nelutu_neon_lab_preview.py").read_text(encoding="utf-8")
        self.assertIn('secret("NELUTU_NEON_LAB_ENABLED", False) is True', source)
        self.assertIn('secret("NELUTU_NEON_LAB_PRIVATE_ACCESS_VERIFIED", False) is True', source)


if __name__ == "__main__":
    unittest.main()
