"""Teste pentru biblioteca pedagogică și întrebările de clarificare."""
import unittest
from nelutu_parent_guide import answer_parent
from nelutu_pedagogy_library import lookup,clarify,contract

class PedagogyTests(unittest.TestCase):
    def test_historical_periods(self):
        for q,expected in [
            ("Ce a făcut Alexandru Ioan Cuza pentru educație?","library_cuza"),
            ("Cine a fost Spiru Haret?","library_haret"),
            ("Cum era școala în perioada interbelică?","library_interwar"),
            ("Cum era școala în comunism?","library_communism"),
            ("Cum s-a schimbat școala după 1989?","library_post1989"),
            ("Ce înseamnă pedagogia modernă?","library_pedagogy"),
            ("Cum comunic cu un adolescent?","library_adolescent")]:
            with self.subTest(q=q):
                self.assertEqual(lookup(q).intent,expected)
    def test_integrated(self):
        self.assertEqual(answer_parent("Cine a fost Spiru Haret?").intent,"library_haret")
        self.assertEqual(answer_parent("unde bag scutirea?").intent,"parent_guide_medical")
        self.assertEqual(answer_parent("am fost amenintat la scoala").intent,"safety")
    def test_clarification(self):
        self.assertEqual(clarify("Cum fac asta?").intent,"clarification")
        self.assertIsNone(clarify(""))
    def test_contract(self):
        self.assertFalse(contract()["claims_live_updates"])
        self.assertFalse(contract()["diagnoses"])

if __name__=="__main__":
    unittest.main()
