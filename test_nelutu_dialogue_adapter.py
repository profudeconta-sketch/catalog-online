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

    def test_three_turn_math_dialogue_in_adapter(self):
        state = DialogueState()
        for question in ("De ce învățăm la școală?", "Dă-mi un exemplu concret.", "Matematică. Mai explică-mi."):
            answer, state = answer_parent_dialogue(question, state=state)
        self.assertEqual(answer.intent, "education_followup_purpose")
        self.assertIn("matematică", answer.text)
        self.assertEqual(state.topic, "purpose")

    def test_portal_switch_after_subject_discussion(self):
        state = DialogueState()
        for question in ("De ce învățăm la școală?", "Dă-mi un exemplu concret.", "Istorie. Mai explică-mi."):
            _, state = answer_parent_dialogue(question, state=state)
        answer, state = answer_parent_dialogue("Cum trimit scutirea medicală?", state=state)
        self.assertEqual(answer.intent, "parent_guide_medical")
        self.assertEqual(state.topic, "")

    def test_disclosed_pin_warns_without_echo(self):
        answer, state = answer_parent_dialogue(
            "Sunt părintele elevului Ion Popescu, numărul matricol 9999 și PIN 1234. Poți să-mi spui notele lui?"
        )
        self.assertEqual(answer.intent, "credential_privacy")
        self.assertTrue(answer.serious)
        self.assertIn("Nu introduceți PIN-uri", answer.text)
        self.assertNotIn("1234", answer.text)
        self.assertEqual(state.topic, "")

    def test_forgotten_pin_guidance(self):
        answer, _ = answer_parent_dialogue("Am uitat PIN-ul pentru portalul părinților. Ce trebuie să fac?")
        self.assertEqual(answer.intent, "access_forgotten")
        self.assertIn("dirigintele", answer.text)

    def test_password_change_guidance(self):
        answer, _ = answer_parent_dialogue("Unde schimb parola în portal?")
        self.assertEqual(answer.intent, "access_change")
        self.assertIn("Nu pot confirma", answer.text)

    def test_password_help_is_not_blocked(self):
        answer, state = answer_parent_dialogue("Unde schimb parola în portal?")
        self.assertNotEqual(answer.intent, "credential_privacy")

    def test_individual_grade_question_has_privacy_priority(self):
        answer, state = answer_parent_dialogue("Ce note are elevul Ion Popescu la matematică?")
        self.assertEqual(answer.intent, "student_records_privacy")
        self.assertTrue(answer.serious)
        self.assertIn("Nu pot consulta", answer.text)
        self.assertEqual(state.topic, "")

    def test_individual_absence_question_has_privacy_priority(self):
        answer, state = answer_parent_dialogue("Ce absențe are eleva la școală?")
        self.assertEqual(answer.intent, "student_records_privacy")
        self.assertTrue(answer.serious)
        self.assertEqual(state.topic, "")

    def test_general_grade_guidance_still_available(self):
        answer, state = answer_parent_dialogue("Unde văd notele în portal?")
        self.assertNotEqual(answer.intent, "student_records_privacy")

    def test_sensitive_portal_mix_overrides_regular_router(self):
        answer, state = answer_parent_dialogue("Nu mai vreau să trăiesc, unde este butonul din portal?")
        self.assertEqual(answer.intent, "sensitive_redirect")
        self.assertTrue(answer.serious)
        self.assertEqual(state.topic, "")

    def test_oversize_portal_question_is_rejected(self):
        answer, state = answer_parent_dialogue("Cum trimit scutirea? " + "x" * 1300)
        self.assertEqual(answer.intent, "clarification")
        self.assertEqual(state.topic, "")

    def test_sensitive_oversize_still_has_priority(self):
        answer, state = answer_parent_dialogue("Nu mai vreau să trăiesc " + "x" * 1300)
        self.assertEqual(answer.intent, "sensitive_redirect")
        self.assertEqual(state.topic, "")

    def test_unrelated_portal_request_clears_context(self):
        _, state = answer_parent_dialogue("De ce învățăm la școală?")
        answer, state = answer_parent_dialogue("Unde trimit scutirea?", state=state)
        self.assertEqual(answer.intent, "parent_guide_medical")
        self.assertEqual(state.topic, "")

if __name__ == "__main__":
    unittest.main()
