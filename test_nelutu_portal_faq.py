"""Regresii pentru FAQ-ul Neluțu, fără rețea și fără date de elev."""
import unittest
from nelutu_portal_faq import answer_portal, contract
from nelutu_parent_guide import answer_parent

class PortalFAQTests(unittest.TestCase):
    def test_steps(self):
        for question,intent in [
            ("am uitat pinul","portal_faq_login"),
            ("cum trimit scutirea medicala","portal_faq_medical"),
            ("cum motivez absentele","portal_faq_excuse"),
            ("cum cer invoire","portal_faq_leave"),
            ("cum confirm instiintarea","portal_faq_notice"),
            ("cum verific daca am trimis","portal_faq_sent"),
            ("cum trimit pe whatsapp","portal_faq_whatsapp"),
        ]:
            with self.subTest(question=question):
                answer=answer_portal(question)
                self.assertIsNotNone(answer)
                self.assertEqual(answer.intent,intent)
    def test_typo_and_no_hallucination(self):
        self.assertEqual(answer_portal("unde e instiintarea?").intent,"portal_faq_notice")
        self.assertIsNone(answer_portal("ce culoare are luna?"))
    def test_safety_and_authorized_context(self):
        self.assertEqual(answer_parent("sunt amenintat si vreau invoire").intent,"safety")
        context={"facts":[{"keywords":["media mea"],"answer":"Media afișată este 9."}]}
        self.assertEqual(answer_parent("care e media mea?",context).intent,"authorized_context")
    def test_no_side_effects(self):
        self.assertEqual(contract(),{"writes_data":False,"uses_network":False,"calls_paid_ai":False})

if __name__=="__main__":
    unittest.main()
