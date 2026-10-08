import unittest
from nelutu_ai_tone import choose_tone

class ToneTests(unittest.TestCase):
    def test_ordinary_learning_allows_warmth(self):
        decision = choose_tone("De ce învățăm matematica?")
        self.assertTrue(decision.humor_allowed)
        self.assertEqual(decision.mode, "warm")

    def test_bullying_is_serious(self):
        self.assertFalse(choose_tone("Sunt victima de bullying.").humor_allowed)

    def test_violence_is_serious(self):
        self.assertFalse(choose_tone("M-au bătut colegii.").humor_allowed)

    def test_fear_is_serious(self):
        self.assertFalse(choose_tone("Mi-e frică să merg la școală.").humor_allowed)

    def test_loss_is_serious(self):
        self.assertFalse(choose_tone("Bunicul meu a murit.").humor_allowed)

    def test_harassment_inflection_is_serious(self):
        self.assertFalse(choose_tone("Sunt hărțuit la școală.").humor_allowed)

    def test_distress_without_explicit_suicide_word_is_serious(self):
        self.assertFalse(choose_tone("Nu mai vreau să trăiesc.").humor_allowed)

    def test_threat_is_serious(self):
        self.assertFalse(choose_tone("Am fost amenințat de colegi.").humor_allowed)

    def test_empty_does_not_crash(self):
        self.assertEqual(choose_tone(None).mode, "warm")

if __name__ == "__main__":
    unittest.main()
