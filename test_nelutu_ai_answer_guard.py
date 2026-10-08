import unittest
from nelutu_ai_answer_guard import safe_memory_answer

class AnswerGuardTests(unittest.TestCase):
    def test_ordinary_educational_answer(self):
        self.assertTrue(safe_memory_answer("Matematica dezvoltă gândirea logică."))

    def test_reject_identifiers(self):
        for answer in (
            "CNP: 1234567890123",
            "Contact: profesor@example.com",
            "Telefon: 0712345678",
            "PIN: 1234",
            "Parola: exemplu",
            "Copilul meu a lipsit.",
        ):
            with self.subTest(answer=answer):
                self.assertFalse(safe_memory_answer(answer))

    def test_invalid(self):
        self.assertFalse(safe_memory_answer(""))
        self.assertFalse(safe_memory_answer(None))
        self.assertFalse(safe_memory_answer("x" * 2201))

if __name__ == "__main__":
    unittest.main()
