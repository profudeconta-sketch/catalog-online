"""Probe izolate, fără apeluri externe sau date reale."""
import unittest
from unittest.mock import patch

from nelutu_local_dialogue import DialogueState, reply, contract


class LocalDialogueTests(unittest.TestCase):
    def test_topic_followup_without_history(self):
        first, state = reply("De ce învățăm la școală?")
        self.assertIsNotNone(first)
        self.assertEqual(state.topic, "purpose")
        second, next_state = reply("Dă-mi un exemplu", state)
        self.assertEqual(second.intent, "education_followup_purpose")
        self.assertEqual(next_state.topic, "purpose")

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

    def test_oversized_input(self):
        result, state = reply("x" * 1201)
        self.assertEqual(result.intent, "clarification")
        self.assertEqual(state.topic, "")


if __name__ == "__main__":
    unittest.main()
