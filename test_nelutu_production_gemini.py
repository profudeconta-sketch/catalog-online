"""Production Gemini gate contracts; no live provider or Neon calls."""
import unittest
from unittest.mock import patch
from nelutu_production_gemini import optional_provider
from nelutu_modern_core import answer

FLAGS = dict(
    NELUTU_GEMINI_ENABLED=True,
    NELUTU_PROVIDER_PRIVACY_APPROVED=True,
    NELUTU_PROVIDER_COST_APPROVED=True,
    NELUTU_NEON_BUDGET_ENABLED=True,
    NELUTU_NEON_LIVE_BUDGET_APPROVED=True,
    NELUTU_GEMINI_API_KEY="fake-for-offline-test",
    NELUTU_NEON_DSN="fake-for-offline-test",
)

class ProductionGateTests(unittest.TestCase):
    def test_no_consent_no_reservation(self):
        with patch("nelutu_production_gemini.PostgreSQLBudget") as budget:
            provider, reserved = optional_provider("De ce plutesc vapoarele?", "fallback", settings=FLAGS)
            self.assertIsNone(provider)
            self.assertFalse(reserved)
            budget.assert_not_called()

    def test_school_data_never_reserved(self):
        with patch("nelutu_production_gemini.PostgreSQLBudget") as budget:
            provider, reserved = optional_provider("Care este nota elevului?", "fallback", consent=True, settings=FLAGS)
            self.assertIsNone(provider)
            self.assertFalse(reserved)
            budget.assert_not_called()

    def test_disabled_gemini_never_reserved(self):
        with patch("nelutu_production_gemini.PostgreSQLBudget") as budget:
            provider, reserved = optional_provider("De ce plutesc vapoarele?", "fallback", consent=True, settings={})
            self.assertIsNone(provider)
            self.assertFalse(reserved)
            budget.assert_not_called()

    def test_school_answer_stays_local(self):
        provider = lambda history, question: self.fail("External provider invoked for school question")
        result = answer("Cum trimit o scutire medicală?", consent=True,
                        generative_enabled=True, budget_reserved=True, provider=provider)
        self.assertNotEqual(result.route, "generative")

if __name__ == "__main__":
    unittest.main()
