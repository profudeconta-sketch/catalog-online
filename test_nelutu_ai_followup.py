import unittest
from nelutu_ai_followup import suggest_followup

class FollowUpTests(unittest.TestCase):
    def test_helpful_answer_can_invite_feedback(self):
        result = suggest_followup(helpful_answer=True, sensitive=False)
        self.assertEqual(result.category, "check")

    def test_no_followup_on_distress(self):
        self.assertIsNone(suggest_followup(helpful_answer=True, sensitive=True))

    def test_respects_stop(self):
        self.assertIsNone(suggest_followup(helpful_answer=True, sensitive=False, user_wants_to_stop=True))

    def test_does_not_push_after_unhelpful_answer(self):
        self.assertIsNone(suggest_followup(helpful_answer=False, sensitive=False))

    def test_varies_once_and_then_stops(self):
        result = suggest_followup(helpful_answer=True, sensitive=False, previous_category="check")
        self.assertEqual(result.category, "example")
        self.assertIsNone(suggest_followup(helpful_answer=True, sensitive=False, previous_category="example"))

if __name__ == "__main__":
    unittest.main()
