import unittest
from nelutu_ai_romanian import polish_romanian

class RomanianPolishTests(unittest.TestCase):
    def test_real_live_exam_errors(self):
        samples = {
            "pasând prin economie": "trecând prin economie",
            "cu cuvinte tale": "cu propriile tale cuvinte",
            "nu ezita să cere ajutorul": "nu ezita să ceri ajutor",
            "să devină autonome în domenii concrete": "să devină autonomi în domenii concrete",
            "ca un seminț de curiozitate": "ca o sămânță de curiozitate",
            "știriile": "informațiile",
            "Învăță activ": "Învață activ",
            "Repetați cu timp": "Repetă la intervale regulate",
        }
        for source, expected in samples.items():
            with self.subTest(source=source):
                self.assertEqual(polish_romanian(source), expected)

    def test_authentic_regional_voice_is_unchanged(self):
        for text in ("No, așe-i!", "No, meri la învățătură!", "Matematica ajută la socoteli."):
            self.assertEqual(polish_romanian(text), text)

    def test_does_not_overcorrect_other_contexts(self):
        self.assertEqual(polish_romanian("Ele devin autonome."), "Ele devin autonome.")
        self.assertEqual(polish_romanian("Cere ajutorul unui profesor."), "Cere ajutorul unui profesor.")

    def test_idempotent(self):
        text = "Nu ezita să cere ajutorul; cu cuvinte tale."
        self.assertEqual(polish_romanian(polish_romanian(text)), polish_romanian(text))

if __name__ == "__main__":
    unittest.main()
