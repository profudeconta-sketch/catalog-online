"""Safety invariants for the integrated Neluțu rehearsal; offline only."""
import unittest
from nelutu_unified_rehearsal import rehearse


class UnifiedRehearsalTests(unittest.TestCase):
    def test_portal_flow_does_not_call_provider(self):
        result = rehearse("Cum trimit o scutire medicală în portal?",
                          consent=True, enabled=True, budget_reserved=True)
        self.assertEqual(result.provider_calls, 0)
        self.assertNotEqual(result.actual_route, "generative")

    def test_no_consent_never_calls_provider(self):
        result = rehearse("De ce plutește o barcă?",
                          consent=False, enabled=True, budget_reserved=True)
        self.assertEqual(result.provider_calls, 0)

    def test_disabled_never_calls_provider(self):
        result = rehearse("De ce plutește o barcă?",
                          consent=True, enabled=False, budget_reserved=True)
        self.assertEqual(result.provider_calls, 0)

    def test_no_budget_never_calls_provider(self):
        result = rehearse("De ce plutește o barcă?",
                          consent=True, enabled=True, budget_reserved=False)
        self.assertEqual(result.provider_calls, 0)

    def test_provider_only_for_eligible_question(self):
        result = rehearse("De ce plutește o barcă?",
                          consent=True, enabled=True, budget_reserved=True)
        if result.provider_calls:
            self.assertEqual(result.planned_route, "generative_eligible")
            self.assertEqual(result.actual_route, "generative")
            self.assertIn("FICTIV", result.answer)
        else:
            self.assertNotEqual(result.actual_route, "generative")


if __name__ == "__main__":
    unittest.main()
