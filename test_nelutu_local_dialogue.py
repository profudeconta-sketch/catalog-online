"""Probe izolate, fără apeluri externe sau date reale."""
import unittest

from nelutu_local_dialogue import DialogueState, reply, contract


class LocalDialogueTests(unittest.TestCase):
    def test_topic_followup_without_history(self):
        first, state = reply("De ce învățăm la școală?")
        self.assertIsNotNone(first)
        self.assertEqual(state.topic, "purpose")
        second, next_state = reply("Dă-mi un exemplu", state)
        self.assertEqual(second.intent, "education_followup_purpose")
        self.assertEqual(next_state.topic, "purpose")

    def test_real_browser_followup_with_concret(self):
        _, state = reply("De ce învățăm la școală?")
        answer, state = reply("Dă-mi un exemplu concret.", state)
        self.assertEqual(answer.intent, "education_followup_purpose")
        self.assertEqual(state.topic, "purpose")

    def test_math_subject_after_example(self):
        _, state = reply("De ce învățăm la școală?")
        _, state = reply("Dă-mi un exemplu concret.", state)
        answer, state = reply("Matematică. Mai explică-mi.", state)
        self.assertEqual(answer.intent, "education_followup_purpose")
        self.assertIn("matematică", answer.text)
        self.assertEqual(state.topic, "purpose")

    def test_other_subjects_keep_context(self):
        for subject, keyword in (("Română", "contract"), ("Istorie", "sursele"), ("Fizică", "centura")):
            with self.subTest(subject=subject):
                _, state = reply("De ce învățăm la școală?")
                _, state = reply("Dă-mi un exemplu concret.", state)
                answer, state = reply(subject + ". Mai explică-mi.", state)
                self.assertEqual(answer.intent, "education_followup_purpose")
                self.assertIn(keyword, answer.text)
                self.assertEqual(state.topic, "purpose")

    def test_math_subject_without_context_does_not_invent(self):
        answer, state = reply("Matematică. Mai explică-mi.")
        self.assertIsNone(answer)
        self.assertEqual(state.topic, "")

    def test_new_topic_replaces_previous(self):
        _, state = reply("De ce învățăm la școală?")
        result, state = reply("Ce meserie ar putea învăța?", state)
        self.assertEqual(state.topic, "technical")
        self.assertEqual(result.intent, "education_technical")

    def test_unknown_does_not_hallucinate_followup(self):
        _, state = reply("De ce învățăm la școală?")
        result, state = reply("Ce s-a întâmplat ieri în clasa copilului meu?", state)
        self.assertIsNone(result)
        self.assertEqual(state.topic, "")

    def test_reset_and_empty(self):
        _, state = reply("De ce învățăm la școală?")
        result, state = reply("Schimbăm subiectul", state)
        self.assertEqual(state.topic, "")
        self.assertEqual(result.intent, "clarification")
        result, state = reply("", state)
        self.assertIsNone(result)

    def test_no_network_no_student_data_contract(self):
        c = contract()
        self.assertFalse(c["uses_network"])
        self.assertFalse(c["reads_student_records"])
        self.assertFalse(c["stores_message_history"])
        self.assertFalse(c["generative_ai"])

    def test_sensitive_question_overrides_education(self):
        answer, state = reply("Copilul mă amenință și nu vrea să învețe")
        self.assertEqual(answer.intent, "sensitive_redirect")
        self.assertTrue(answer.serious)
        self.assertEqual(state.topic, "")

    def test_non_string_fails_closed(self):
        answer, state = reply(None)
        self.assertIsNone(answer)
        self.assertEqual(state.topic, "")

    def test_reset_not_substring(self):
        answer, state = reply("Îmi trebuie o altă tematică la școală")
        self.assertNotEqual(getattr(answer, "intent", ""), "clarification")

    def test_followup_natural_phrase(self):
        _, state = reply("De ce învățăm la școală?")
        answer, state = reply("Poți să detaliezi?", state)
        self.assertEqual(answer.intent, "education_followup_purpose")

    def test_safety_variations(self):
        for question in ("Nu mai vreau să trăiesc", "Mă hărțuiesc colegii",
                         "Sunt bătut acasă", "Îmi este frică acasă"):
            with self.subTest(question=question):
                answer, state = reply(question)
                self.assertEqual(answer.intent, "sensitive_redirect")
                self.assertTrue(answer.serious)
                self.assertEqual(state.topic, "")

    def test_safety_before_reset_or_size_limit(self):
        for question in ("Schimbăm subiectul, dar nu mai vreau să trăiesc",
                         "Nu mai vreau să trăiesc " + "x" * 1300):
            with self.subTest(question=question[:45]):
                answer, state = reply(question)
                self.assertEqual(answer.intent, "sensitive_redirect")
                self.assertTrue(answer.serious)
                self.assertEqual(state.topic, "")

    def test_followups_progress_then_request_specifics(self):
        _, state = reply("De ce învățăm la școală?")
        first, state = reply("Dă-mi un exemplu", state)
        second, state = reply("Mai explică", state)
        third, state = reply("Continuă", state)
        self.assertEqual(first.intent, "education_followup_purpose")
        self.assertEqual(second.intent, "education_followup_purpose")
        self.assertNotEqual(first.text, second.text)
        self.assertEqual(third.intent, "clarification")
        self.assertEqual(state.topic, "purpose")

    def test_topic_change_resets_followup_progress(self):
        _, state = reply("De ce învățăm la școală?")
        _, state = reply("Continuă", state)
        _, state = reply("Ce meserie ar putea învăța?", state)
        answer, state = reply("Continuă", state)
        self.assertEqual(answer.intent, "education_followup_technical")
        self.assertEqual(state.turns, 2)

    def test_oversized_input(self):
        result, state = reply("x" * 1201)
        self.assertEqual(result.intent, "clarification")
        self.assertEqual(state.topic, "")


if __name__ == "__main__":
    unittest.main()
