"""Contextual routing regressions: public meanings must not become portal instructions."""
import unittest

from nelutu_contextual_intent import classify_context
from nelutu_dialogue_adapter import answer_parent_dialogue


class ContextualMenuTests(unittest.TestCase):
    def test_bare_menu_labels_request_clarification(self):
        for phrase in ("merit", "sociala", "venit", "orfan", "medicala",
                       "mame", "minore", "ces", "documente", "dosar personal",
                       "scutiri medicale", "invoire"):
            with self.subTest(phrase=phrase):
                self.assertEqual(classify_context(phrase), "ambiguous")
                answer, _ = answer_parent_dialogue(phrase)
                self.assertEqual(answer.intent, "clarification")

    def test_general_context_does_not_open_portal(self):
        for question in (
            "Unde pleaca soarele cand este noapte afara?",
            "Unde se duce luna cand este ziua afara?",
            "Ce inseamna merit in societate?",
            "Ce inseamna venit in economie?",
            "Ce inseamna orfan in literatura?",
            "De ce este importanta scoala in societate?",
        ):
            with self.subTest(question=question):
                answer, _ = answer_parent_dialogue(question)
                self.assertNotIn(answer.intent, (
                    "parent_flow_leave", "parent_flow_documents",
                    "parent_flow_excuse", "parent_flow_scholarship",
                    "parent_guide_leave", "portal_component", "scholarship",
                ))

    def test_explicit_portal_requests_remain_local(self):
        for question in (
            "Cum trimit cererea de motivare a absentelor?",
            "Cum incarc scutirea medicala pentru elev?",
            "Cum solicit un bilet de voie?",
        ):
            with self.subTest(question=question):
                self.assertEqual(classify_context(question), "portal")


if __name__ == "__main__":
    unittest.main()
