import unittest
from nelutu_ai_eval import SCENARIOS, evaluate_offline

class OfflineEvaluationTests(unittest.TestCase):
    def test_all_scenarios_match_expected_safety_policy(self):
        passed, failed = evaluate_offline()
        self.assertEqual(failed, (), f"Failed cases: {failed}")
        self.assertEqual(len(passed), len(SCENARIOS))

    def test_scenario_names_are_unique(self):
        names = [case.name for case in SCENARIOS]
        self.assertEqual(len(names), len(set(names)))

if __name__ == "__main__":
    unittest.main()
