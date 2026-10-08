import unittest
from nelutu_ai_stress import PROBES, run_policy_probes, followup_safety_probes

class StressTests(unittest.TestCase):
    def test_policy_matrix(self):
        passed, failed = run_policy_probes()
        self.assertEqual(failed, (), f"Policy mismatches: {failed}")
        self.assertEqual(len(passed), len(PROBES))

    def test_unique_probes(self):
        self.assertEqual(len({p.name for p in PROBES}), len(PROBES))

    def test_followup_does_not_pressure(self):
        self.assertTrue(followup_safety_probes())

if __name__ == "__main__":
    unittest.main()
