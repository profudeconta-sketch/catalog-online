import unittest
from nelutu_ai_experiment import NELUTU_PERSONA, ExperimentalPolicy, safe_to_activate

class ExperimentalPolicyTests(unittest.TestCase):
    def test_disabled_by_default(self):
        p = ExperimentalPolicy()
        self.assertFalse(p.enabled)
        self.assertFalse(p.external_student_data_allowed)
        self.assertTrue(p.automatic_fallback)
        self.assertGreaterEqual(p.max_output_tokens, 750)

    def test_requires_every_gate(self):
        self.assertFalse(safe_to_activate(consent=True, secret_configured=True,
            privacy_review_complete=False, integration_tests_passed=True))
        self.assertTrue(safe_to_activate(consent=True, secret_configured=True,
            privacy_review_complete=True, integration_tests_passed=True))

    def test_persona_sensitive_topics(self):
        self.assertIn("fără glume", NELUTU_PERSONA)
        self.assertIn("Nu pretinzi acces la catalog", NELUTU_PERSONA)

if __name__ == "__main__":
    unittest.main()
