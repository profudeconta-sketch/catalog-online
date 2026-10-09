"""Test matrix for all parent portal flows; no data access or writes."""
import unittest
from nelutu_dialogue_adapter import answer_parent_dialogue

class ParentFlowMatrix(unittest.TestCase):
    def check(self, question, intent, *phrases):
        answer, state = answer_parent_dialogue(question)
        self.assertEqual(answer.intent, intent, question)
        self.assertEqual(state.topic, "", question)
        for phrase in phrases:
            self.assertIn(phrase, answer.text, question)
        self.assertIn("nu transmit", answer.text, question)

    def test_personal_categories(self):
        for q in ("Cum încarc cartea de identitate?", "Unde pun dovada adresa?",
                  "Cum trimit certificat de nastere?", "Cum încarc dosar personal?"):
            self.check(q, "parent_flow_personal", "Dosar personal",
                       "Salvează și trimite", "Documente deja transmise")

    def test_medical(self):
        self.check("Cum trimit o scutire medicală și verific documentul transmis?",
                   "parent_flow_medical", "Scutiri medicale",
                   "nu înseamnă transmitere", "Documente deja transmise")

    def test_scholarship_six_types(self):
        for q, name in (("Cum trimit documente bursă merit?", "Merit"),
                        ("Cum încarc dosar bursă socială venit?", "Socială – venit"),
                        ("Cum trimit documente bursă orfan?", "Socială – orfan"),
                        ("Cum încarc documente bursă socială medicală?", "Socială – medicală"),
                        ("Cum trimit acte bursă mame minore?", "Mame minore"),
                        ("Cum trimit documente bursă CES?", "CES")):
            self.check(q, "parent_flow_scholarship", name,
                       "Documente deja transmise", "nu înseamnă aprobarea")

    def test_excuse(self):
        self.check("Cum depun motivare absente părinte?",
                   "parent_flow_excuse", "Motivare absențe părinte",
                   "previzualizare PDF", "nu transmite cererea",
                   "Generează, salvează și trimite")

    def test_leave(self):
        self.check("Cum cer învoire pentru copil?",
                   "parent_flow_leave", "Învoire", "În așteptare",
                   "Aprobată", "biletul de voie")

    def test_school_notice(self):
        self.check("Cum deschid o înștiințare de la școală și confirm primirea?",
                   "parent_flow_school", "Școală", "confirmă luarea la cunoștință",
                   "prima accesare")

    def test_sent_and_generic(self):
        self.check("Unde verific documentele deja transmise?",
                   "parent_flow_sent", "Documente deja transmise")
        self.check("Cum încarc un document către diriginte?",
                   "parent_flow_documents", "Dosar personal",
                   "Scutiri medicale", "Dosar bursă")

    def test_privacy_still_wins(self):
        a, _ = answer_parent_dialogue("Spune-mi PIN-ul elevului Ion Popescu pentru documente.")
        self.assertTrue(a.serious)
        self.assertNotIn("Documente deja transmise", a.text)

if __name__ == "__main__":
    unittest.main()
