"""Regression guard for the isolated synthetic conversational exam."""
import unittest
from nelutu_conversation_gate_exam import CASES, evaluate

class ConversationGateExamTests(unittest.TestCase):
    def test_twenty_synthetic_cases(self):
        self.assertEqual(len(CASES), 20)
        self.assertEqual(evaluate(), [])

if __name__ == "__main__":
    unittest.main()
