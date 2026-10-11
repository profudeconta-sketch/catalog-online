"""Offline guard for optional unified Gemini preview. No API requests."""
from pathlib import Path
import unittest


class UnifiedPreviewTests(unittest.TestCase):
    def test_opt_in_and_durable_budget_before_provider(self):
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        section = source.split('st.subheader("🤠 Neluțu — dialog generativ experimental', 1)[1]
        self.assertIn("NELUTU_UNIFIED_LIVE_ENABLED", section)
        self.assertIn("NELUTU_UNIFIED_ACCESS_CODE", section)
        self.assertIn("_hmac.compare_digest", section)
        self.assertIn("len(_unified_expected_code) >= 16", section)
        self.assertIn("elif not _unified_operator_authorized:", section)
        self.assertLess(section.index("elif not _unified_operator_authorized:"), section.index("reserve_gemini_attempt()"))
        self.assertIn("unified_consent", section)
        self.assertIn("durable_mode and durable_budget is not None", section)
        self.assertIn("reserve_gemini_attempt()", section)
        self.assertLess(section.index("reserve_gemini_attempt()"), section.index("generate_public_dialogue("))
        self.assertIn("answer_parent_dialogue", section)
        self.assertIn("nelutu_unified_public_history", section)
        self.assertIn("Șterge conversația generativă", section)
        self.assertIn("_prepare_public(_history, unified_question, consent=True)", section)
        self.assertIn("history=_history", section)
        self.assertIn("len(_next_history) <= 6", section)
        self.assertNotIn("import app_parinti", section)
        self.assertNotIn("import app_web_catalog", section)


if __name__ == "__main__":
    unittest.main()
