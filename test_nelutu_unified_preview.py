"""Offline guard for optional unified Gemini preview. No API requests."""
from pathlib import Path
import unittest


class UnifiedPreviewTests(unittest.TestCase):
    def test_opt_in_and_durable_budget_before_provider(self):
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        section = source.split('st.subheader("🤠 Neluțu — dialog generativ experimental', 1)[1]
        self.assertIn("NELUTU_UNIFIED_LIVE_ENABLED", section)
        self.assertIn("unified_consent", section)
        self.assertIn("durable_mode and durable_budget is not None", section)
        self.assertIn("reserve_gemini_attempt()", section)
        self.assertLess(section.index("reserve_gemini_attempt()"), section.index("generate_public_dialogue("))
        self.assertIn("answer_parent_dialogue", section)
        self.assertNotIn("import app_parinti", section)
        self.assertNotIn("import app_web_catalog", section)


if __name__ == "__main__":
    unittest.main()
