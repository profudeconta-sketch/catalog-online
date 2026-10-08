import unittest
from nelutu_ai_budget import SessionAIBudget, guarded_generate

class BudgetTests(unittest.TestCase):
    def test_quota(self):
        budget = SessionAIBudget(max_requests=2)
        calls = []
        def fake(question):
            calls.append(question)
            return "OK"
        self.assertEqual(guarded_generate("a",budget=budget,consent=True,generator=fake),"OK")
        self.assertEqual(guarded_generate("b",budget=budget,consent=True,generator=fake),"OK")
        with self.assertRaises(RuntimeError):
            guarded_generate("c",budget=budget,consent=True,generator=fake)
        self.assertEqual(len(calls),2)

    def test_consent(self):
        budget = SessionAIBudget()
        with self.assertRaises(PermissionError):
            guarded_generate("a",budget=budget,consent=False,generator=lambda q:"OK")
        self.assertEqual(budget.used,0)

    def test_failed_calls_consume_quota(self):
        budget = SessionAIBudget(max_requests=1)
        def failing(question): raise OSError("offline")
        with self.assertRaises(OSError):
            guarded_generate("a",budget=budget,consent=True,generator=failing)
        self.assertEqual(budget.remaining,0)

if __name__ == "__main__":
    unittest.main()
