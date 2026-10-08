import unittest
from nelutu_ai_memory import NelutuMemory
from nelutu_ai_recall import recall_local

class RecallTests(unittest.TestCase):
    def test_relevant_memory_first(self):
        m = NelutuMemory()
        m.add("Ce rol are educația tehnică?", "Meserii practice.")
        m.add("De ce învățăm matematica?", "Pentru gândirea logică.")
        matches = recall_local(m, "De ce învățăm matematica?")
        self.assertEqual(matches[0].answer, "Pentru gândirea logică.")

    def test_isolated(self):
        a, b = NelutuMemory(), NelutuMemory()
        a.add("De ce învățăm matematica?", "Din sesiunea A.")
        self.assertEqual(recall_local(b, "De ce învățăm matematica?"), [])

    def test_personal_queries_cannot_search(self):
        m = NelutuMemory()
        m.add("De ce învățăm matematica?", "Pentru logică.")
        self.assertEqual(recall_local(m, "Ce note are copilul meu?"), [])

    def test_clear_and_no_side_effects(self):
        m = NelutuMemory()
        m.add("De ce învățăm matematica?", "Pentru logică.")
        self.assertTrue(recall_local(m, "De ce învățăm matematica?"))
        m.clear()
        self.assertFalse(recall_local(m, "De ce învățăm matematica?"))

if __name__ == "__main__":
    unittest.main()
