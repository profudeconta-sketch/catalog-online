"""Offline tests for Neluțu's synthetic conversation examination."""
import unittest
from nelutu_ai_conversation_exam import SCENARIOS, evaluate, verify_no_private_history
from nelutu_ai_privacy import external_messages
from nelutu_ai_experiment import NELUTU_PERSONA

class ConversationExamTests(unittest.TestCase):
    def test_all_synthetic_scenarios(self):
        passed, failed = evaluate()
        self.assertEqual(failed, [], f"Failed safety-policy scenarios: {failed}")
        self.assertEqual(len(passed), len(SCENARIOS))
        self.assertGreaterEqual(len(SCENARIOS), 20)

    def test_public_request_never_sends_history(self):
        self.assertTrue(verify_no_private_history())

    def test_private_requests_cannot_be_forwarded(self):
        for scenario in SCENARIOS:
            if scenario.group == "public":
                continue
            with self.subTest(scenario=scenario.id):
                with self.assertRaisesRegex(ValueError, "local_only"):
                    external_messages(scenario.message, NELUTU_PERSONA)

if __name__ == "__main__":
    unittest.main()
