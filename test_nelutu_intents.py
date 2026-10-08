"""Teste fără I/O pentru routerul Neluțu; rulare: python -m unittest test_nelutu_intents.py"""
import unittest
from nelutu_parent_guide import _match, answer_parent, contract

class NelutuIntentTests(unittest.TestCase):
    def test_known_questions(self):
        cases = {
            "unde bag scutirea": "medical",
            "unde trimit adeverinta": "medical",
            "cum justific absentele": "excuse",
            "vreau bilet de voie": "leave",
            "unde vad actele trimise": "sent",
            "am primit notificare de la scoala": "school",
            "unde pun documentele": "documents",
            "arata mi aplicatia": "tutorial",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(_match(question), expected)

    def test_safety_always_first(self):
        reply = answer_parent("Am fost amenintat, unde bag scutirea?")
        self.assertEqual(reply.intent, "safety")
        self.assertTrue(reply.serious)

    def test_unknown_not_falsely_matched(self):
        self.assertIsNone(_match("Ce părere ai despre vreme?"))

    def test_system_overview_not_scholarship(self):
        from nelutu_assistant import answer, answer_with_context
        question = "Spune-mi despre sistemul acesta?"
        self.assertEqual(answer(question).intent, "portal")
        self.assertNotEqual(answer_parent(question).intent, "scholarship")
        self.assertEqual(answer_with_context("Acest sistem cum functioneaza?").intent, "portal")

    def test_scholarship_only_real_word(self):
        from nelutu_assistant import answer
        self.assertEqual(answer("Ce acte trebuie pentru bursa?").intent, "scholarship")
        self.assertNotEqual(answer("Povesteste despre acest portal").intent, "scholarship")

    def test_read_only_contract(self):
        self.assertEqual(contract(), {
            "writes_data": False, "uses_network": False,
            "external_ai": False, "changes_school_workflow": False,
        })

if __name__ == "__main__":
    unittest.main()
