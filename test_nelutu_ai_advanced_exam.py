"""Regression test for synthetic advanced exam; no external AI requests."""
import unittest
from nelutu_ai_advanced_exam import SCENARIOS, examine
from nelutu_ai_privacy import external_messages
from nelutu_ai_experiment import NELUTU_PERSONA

class AdvancedExamTests(unittest.TestCase):
    def test_all_local_scenarios_pass(self):
        self.assertEqual(len(SCENARIOS), 12)
        self.assertTrue(all(ok for _, ok, _ in examine()), examine())

    def test_no_sensitive_exam_prompt_can_leave_device(self):
        for scenario in SCENARIOS:
            with self.subTest(label=scenario.label):
                with self.assertRaises(ValueError):
                    external_messages(scenario.prompt, NELUTU_PERSONA)

if __name__ == "__main__":
    unittest.main()
