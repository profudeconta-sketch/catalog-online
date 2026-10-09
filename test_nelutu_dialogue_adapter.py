"""Teste de compatibilitate ale adaptorului, fără Streamlit și fără date reale."""
import unittest
from nelutu_dialogue_adapter import answer_parent_dialogue
from nelutu_local_dialogue import DialogueState

class AdapterTests(unittest.TestCase):
    def test_portal_question_keeps_existing_answer(self):
        answer, state = answer_parent_dialogue("Cum trimit scutirea medicală?")
        self.assertEqual(answer.intent, "parent_guide_medical")
        self.assertEqual(state.topic, "")

    def test_educational_topic_then_followup(self):
        first, state = answer_parent_dialogue("De ce învățăm la școală?")
        self.assertEqual(first.intent, "education_purpose")
        self.assertEqual(state.topic, "purpose")
        second, state = answer_parent_dialogue("Dă-mi un exemplu", state=state)
        self.assertEqual(second.intent, "education_followup_purpose")

    def test_unrelated_portal_request_clears_context(self):
        _, state = answer_parent_dialogue("De ce învățăm la școală?")
        answer, state = answer_parent_dialogue("Unde trimit scutirea?", state=state)
        self.assertEqual(answer.intent, "parent_guide_medical")
        self.assertEqual(state.topic, "")

if __name__ == "__main__":
    unittest.main()
