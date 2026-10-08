"""Teste conversații educaționale fără servicii externe."""
import unittest
from nelutu_education_dialogue import educational_reply, contract
from nelutu_parent_guide import answer_parent

class EducationDialogueTests(unittest.TestCase):
    def test_topics(self):
        cases={
            "De ce este important invatamantul tehnic?":"education_technical",
            "Ce rost are educatia?":"education_purpose",
            "Copilul nu vrea sa invete":"education_motivation",
            "Cum colaboreaza familia si scoala?":"education_family",
            "Cum alegem cariera?":"education_future",
        }
        for question,intent in cases.items():
            with self.subTest(question=question):
                answer=educational_reply(question)
                self.assertIsNotNone(answer)
                self.assertEqual(answer.intent,intent)
                self.assertIn("?",answer.text)
    def test_portal_and_safety_priority(self):
        self.assertEqual(answer_parent("unde bag scutirea?").intent,"parent_guide_medical")
        self.assertEqual(answer_parent("am fost amenintat la scoala").intent,"safety")
    def test_education_integrated(self):
        self.assertEqual(answer_parent("Ce rost are educatia?").intent,"education_purpose")
    def test_no_unrelated_hallucination(self):
        self.assertIsNone(educational_reply("Cât este ceasul?"))
    def test_contract(self):
        self.assertEqual(contract(),{"writes_data":False,"uses_network":False,"external_ai":False,"reads_student_records":False})

if __name__=="__main__":
    unittest.main()
