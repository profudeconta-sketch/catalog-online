"""Focused tests for the new single entrypoint; no duplicate Neon tests."""
import unittest
from unittest.mock import patch
from nelutu_modern_core import answer

class ModernCoreTests(unittest.TestCase):
    def test_local_portal_question_stays_local(self):
        calls = []
        result = answer("Cum trimit o scutire medicală în portal?", provider=lambda *args: calls.append(args))
        self.assertEqual(calls, [])
        self.assertNotEqual(result.route, "generative")

    def test_no_provider_without_consent(self):
        calls = []
        answer("De ce plutesc vapoarele din metal?", generative_enabled=True,
               budget_reserved=True, provider=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_no_provider_with_private_context(self):
        calls = []
        answer("De ce plutesc vapoarele din metal?", context={"facts": ["private"]},
               consent=True, generative_enabled=True, budget_reserved=True,
               provider=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_no_provider_without_budget(self):
        calls = []
        answer("De ce plutesc vapoarele din metal?", consent=True,
               generative_enabled=True, provider=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

if __name__ == "__main__":
    unittest.main()
