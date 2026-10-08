import unittest
from nelutu_ai_memory import NelutuMemory
from nelutu_ai_tutor import suggest_previous_answer, remember_approved_exchange

class TutorTests(unittest.TestCase):
    def test_remembers_exact_generic_question(self):
        m = NelutuMemory()
        self.assertTrue(remember_approved_exchange(m, "De ce învățăm matematica?", "Pentru logică."))
        result = suggest_previous_answer(m, "De ce învățăm matematica?")
        self.assertEqual(result.answer, "Pentru logică.")
        self.assertEqual(result.source, "previous_session_answer")

    def test_no_personal_memory(self):
        m = NelutuMemory()
        self.assertFalse(remember_approved_exchange(m, "Ce note are copilul meu?", "Nu."))
        self.assertIsNone(suggest_previous_answer(m, "Ce note are copilul meu?"))

    def test_separate_instances(self):
        first, second = NelutuMemory(), NelutuMemory()
        remember_approved_exchange(first, "De ce învățăm matematica?", "Primul.")
        self.assertIsNone(suggest_previous_answer(second, "De ce învățăm matematica?"))

if __name__ == "__main__":
    unittest.main()
