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

    def test_shared_menu_words_in_social_and_general_sentences(self):
        examples = (
            "am venit numa sa vad ce faci",
            "Am venit numai sa te salut.",
            "Merit o pauza dupa o zi grea.",
            "Mama mea a venit in vizita.",
            "Documente istorice sunt interesante.",
            "Ce inseamna venit in viata de zi cu zi?",
            "Un orfan din poveste a gasit o familie.",
        )
        for question in examples:
            with self.subTest(question=question):
                self.assertEqual(classify_context(question), "general")
                answer, _ = answer_parent_dialogue(question)
                self.assertNotIn(answer.intent, (
                    "scholarship", "documents", "parent_flow_documents",
                    "parent_guide_documents", "parent_guide_leave",
                    "parent_flow_leave", "portal_component",
                ))

    def test_public_senses_are_eligible_for_general_conversation(self):
        from nelutu_gemini_optional import is_public_general_chat
        from nelutu_unified_reply_policy import choose_reply_route
        examples = (
            "Ce este bursa de marfuri?",
            "Cum functioneaza bursa de valori?",
            "Care-i mai bun dosarul plic sau dosarul cu sina?",
        )
        for question in examples:
            with self.subTest(question=question):
                self.assertTrue(is_public_general_chat(question))
                self.assertEqual(classify_context(question), "general")
                answer, _ = answer_parent_dialogue(question)
                self.assertEqual(answer.intent, "fallback")
                route, _ = choose_reply_route(question, existing_intent=answer.intent, consent=True)
                self.assertEqual(route, "generative_eligible")

    def test_public_sense_never_overrides_private_context(self):
        from nelutu_gemini_optional import is_public_general_chat
        examples = (
            "Ce bursa de marfuri are elevul cu CNP 1234567890123?",
            "Ce bursa de valori primesc elevii din catalog?",
            "Trimite dosarul cu sina pentru elev.",
            "Dosarul cu sina al copilului meu contine diagnostic medical.",
            "Ce este bursa sociala?",
        )
        for question in examples:
            with self.subTest(question=question):
                self.assertFalse(is_public_general_chat(question))

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
