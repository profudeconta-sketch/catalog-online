import unittest
from nelutu_ai_memory import NelutuMemory, MAX_TURNS

class MemoryTests(unittest.TestCase):
    def test_session_isolation(self):
        a, b = NelutuMemory(), NelutuMemory()
        self.assertTrue(a.add("De ce învățăm matematica?", "Pentru logică."))
        self.assertEqual(a.size(), 1)
        self.assertEqual(b.size(), 0)

    def test_refuse_student_data(self):
        m = NelutuMemory()
        self.assertFalse(m.add("Ce note are copilul meu?", "Date private"))
        self.assertFalse(m.add("De ce învățăm matematica? CNP 1234567890123", "Nu"))
        self.assertEqual(m.size(), 0)

    def test_bounded_and_clearable(self):
        m = NelutuMemory()
        for i in range(MAX_TURNS + 5):
            self.assertTrue(m.add("De ce învățăm matematica?", "Explicație " + str(i)))
        self.assertEqual(m.size(), MAX_TURNS)
        m.clear()
        self.assertEqual(m.size(), 0)

    def test_local_copy(self):
        m = NelutuMemory()
        m.add("De ce învățăm matematica?", "Pentru logică.")
        copy = m.recent_local()
        copy[0]["content"] = "Modificat"
        self.assertEqual(m.recent_local()[0]["content"], "De ce învățăm matematica?")

if __name__ == "__main__":
    unittest.main()
