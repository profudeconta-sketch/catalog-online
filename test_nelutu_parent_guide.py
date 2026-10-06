import unittest
import nelutu_parent_guide as g

class NelutuParentGuideTests(unittest.TestCase):
    def test_contract_is_golden_rule_safe(self):
        self.assertTrue(all(v is False for v in g.contract().values()))

    def test_tutorial_covers_real_portal(self):
        t=g.answer_parent("tutorial complet").text
        for phrase in ("🔔 Școală","🚪 Învoire","📁 Documente","Dosar personal","Scutiri medicale","Dosar bursă","Motivare absențe părinte","Situația școlară"):
            self.assertIn(phrase,t)

    def test_colloquial_questions_route(self):
        cases={
          "no unde bag scutirea?":"Scutiri medicale",
          "cum trimit hârtia la dirigu?":"Documente",
          "unde văd ce-o trimis școala?":"Școală",
          "mai trebe să duc cererea pe hârtie?":"nu mai trebuie",
          "cum stiu ca am trimis documentul?":"Documente deja transmise",
        }
        for q,needle in cases.items():
            self.assertIn(needle,g.answer_parent(q).text,q)

    def test_preview_is_not_submission(self):
        t=g.answer_parent("mai trebuie sa duc cererea tiparita?").text
        self.assertIn("Previzualizarea nu transmite nimic",t)
        self.assertIn("considerată depusă",t)

    def test_tutorial_does_not_claim_director_approval(self):
        t=g.answer_parent("ghid aplicatie").text
        self.assertIn("nu inventează aprobarea directorului",t)

    def test_unknown_falls_back_to_existing_nelutu(self):
        a=g.answer_parent("salut nelutu")
        self.assertTrue(a.text)
        self.assertNotEqual(a.intent,"portal_tutorial")

if __name__=="__main__":
    unittest.main()
