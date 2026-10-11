import unittest
from nelutu_free_dialogue_preparation import append_public_exchange, prepare_public_dialogue


class PublicMemoryContinuityTests(unittest.TestCase):
    def test_rejected_assistant_wording_does_not_erase_public_question(self):
        question = "Ce este bursa de valori?"
        history = append_public_exchange((), question, "Bursa de valori este o piata; profesorul poate explica.")
        self.assertEqual(history[0], ("user", question))
        self.assertEqual(history[1], ("model", "Am raspuns la intrebarea anterioara."))
        self.assertIsNotNone(prepare_public_dialogue(history, "Poti explica mai mult?", consent=True))

    def test_safe_answers_are_preserved_verbatim(self):
        history = append_public_exchange((), "Ce este o stea?", "O stea este un corp ceresc.")
        self.assertEqual(history[1][1], "O stea este un corp ceresc.")

    def test_private_question_clears_external_history(self):
        history = append_public_exchange((), "Ce este o stea?", "O stea este un corp ceresc.")
        self.assertEqual(append_public_exchange(history, "Ce note are elevul meu?", "Nu pot divulga."), ())

    def test_bounded_history_keeps_recent_public_topic(self):
        history = ()
        for i in range(8):
            history = append_public_exchange(history, "Ce este o stea? " + str(i), "O stea lumineaza.")
        self.assertEqual(len(history), 12)
        self.assertEqual(history[-2][1], "Ce este o stea? 7")


if __name__ == "__main__":
    unittest.main()
