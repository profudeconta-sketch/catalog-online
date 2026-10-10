"""Teste pentru intrebari scolare, fara date personale sau retea."""
import unittest
from nelutu_dialogue_adapter import answer_parent_dialogue

class SchoolTopicTests(unittest.TestCase):
    def test_school_variants(self):
        cases = {
            "la ce-i buna atata scoala?": "education_purpose",
            "La ce e bună atâta școală?": "education_purpose",
            "la cei buna atata scoala": "education_purpose",
            "dc trebe sa mergem la scoala": "education_purpose",
            "da ce folos are scoala asta": "education_purpose",
            "pt ce mai invata copilu": "education_purpose",
            "no da la ce ne trebe atata carte": "education_purpose",
            "De ce facem Fizica?": "education_physics",
            "de ce facem fizica": "education_physics",
            "De ce facem Chimie?": "education_chemistry",
            "ce invatam la chimie": "education_chemistry",
            "Ce facem la Bazele Contabilitatii?": "education_accounting",
            "Ce invatam la bazele contabilității?": "education_accounting",
            "Ce fac la Structuri de primire turistica?": "education_tourism",
            "Ce invatam la structuri de primire turistică?": "education_tourism",
            "Ce inseamna 40 de absente?": "absences_40",
            "Care este regula cu 40 de absente?": "absences_40",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                answer, _ = answer_parent_dialogue(question)
                self.assertEqual(answer.intent, expected)

    def test_portal_keeps_priority(self):
        answer, _ = answer_parent_dialogue("Cum trimit motivarea absentelor?")
        self.assertTrue(answer.intent.startswith("parent_flow"))

if __name__ == "__main__":
    unittest.main()
