import unittest
from nelutu_unified_reply_policy import choose_reply_route


class UnifiedPolicyTests(unittest.TestCase):
    def test_existing_answers_have_priority(self):
        self.assertEqual(choose_reply_route("Cum introduc note?", existing_intent="portal_notes", consent=True)[0], "existing")

    def test_tutorial_for_teacher(self):
        route, guide = choose_reply_route("Cum introduc notele in aplicatia profesorului?")
        self.assertEqual(route, "tutorial")
        self.assertIn("Notele", guide)

    def test_general_chat_requires_consent(self):
        self.assertEqual(choose_reply_route("Salut, ce mai faci?")[0], "local_only")
        self.assertEqual(choose_reply_route("Salut, ce mai faci?", consent=True)[0], "generative_eligible")

    def test_opted_in_smalltalk_can_be_generatively_extended(self):
        self.assertEqual(
            choose_reply_route("Salut, ce mai faci?", existing_intent="smalltalk", consent=True)[0],
            "generative_eligible",
        )
        self.assertEqual(
            choose_reply_route("Salut, ce mai faci?", existing_intent="smalltalk", consent=False)[0],
            "local_only",
        )

    def test_school_private_content_never_goes_to_provider(self):
        self.assertNotEqual(choose_reply_route("Ce nota are elevul?", consent=True)[0], "generative_eligible")


if __name__ == "__main__":
    unittest.main()
