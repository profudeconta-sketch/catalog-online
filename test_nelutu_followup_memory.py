import unittest
from nelutu_free_dialogue_preparation import append_local_public_archive, bounded_public_history, prepare_public_dialogue
from nelutu_unified_reply_policy import choose_reply_route


class FollowupMemoryTests(unittest.TestCase):
    def test_einstein_gps_technical_and_continue(self):
        history = ()
        for question, answer in (
            ("Vorbeste-mi despre Einstein", "Einstein a explicat relativitatea si legatura cu GPS."),
            ("Da, din punct de vedere tehnic ma intereseaza GPS", "GPS foloseste ceasuri atomice si corectii relativiste."),
            ("Vorbeste-mi despre Einstein", "Einstein a formulat teoria relativitatii."),
        ):
            window = bounded_public_history(history[-12:], question)
            route, _ = choose_reply_route(question, existing_intent="fallback", consent=True, history=window)
            self.assertEqual(route, "generative_eligible")
            history = append_local_public_archive(history, question, answer)
        window = bounded_public_history(history[-12:], "continua")
        route, _ = choose_reply_route("continua", existing_intent="clarification", consent=True, history=window)
        self.assertEqual(route, "generative_eligible")
        self.assertIsNotNone(prepare_public_dialogue(window, "continua", consent=True))

    def test_local_archive_longer_than_outbound_window(self):
        history = ()
        for i in range(25):
            history = append_local_public_archive(history, "Ce este o stea? " + str(i), "Un corp ceresc.")
        self.assertEqual(len(history), 50)
        self.assertEqual(len(bounded_public_history(history[-12:], "continua")), 12)

    def test_private_turn_clears_public_archive(self):
        history = append_local_public_archive((), "Ce este o stea?", "Un corp ceresc.")
        self.assertEqual(append_local_public_archive(history, "Ce note are elevul meu?", "Nu pot divulga."), ())

    def test_technical_word_does_not_force_local_educational_answer(self):
        for question in (
            "Explica tehnic cum functioneaza GPS",
            "Din punct de vedere tehnic cum functioneaza un motor?",
            "Vreau o explicatie tehnica despre sateliti",
            "continua",
        ):
            with self.subTest(question=question):
                history = (("user", "Vorbeste-mi despre Einstein"),
                           ("model", "Einstein a explicat relativitatea."))
                route, _ = choose_reply_route(
                    question, existing_intent="education_followup_technical",
                    consent=True, history=history
                )
                self.assertEqual(route, "generative_eligible")

    def test_private_and_portal_intents_cannot_be_overridden(self):
        history = (("user", "Vorbeste-mi despre Einstein"),
                   ("model", "Einstein a explicat relativitatea."))
        for intent in ("parent_flow_documents", "sensitive_redirect",
                       "privacy_guard", "system_tutorial"):
            with self.subTest(intent=intent):
                route, _ = choose_reply_route(
                    "Explica tehnic GPS", existing_intent=intent,
                    consent=True, history=history
                )
                self.assertEqual(route, "existing")

    def test_selected_mode_controls_public_provider(self):
        from nelutu_unified_orchestrator import respond
        from nelutu_assistant import NelutuAnswer
        called = []
        def provider(history, question):
            called.append(question)
            return "Explicatia publica solicitata."
        local = NelutuAnswer("education_technical", "Raspuns local.")
        question = "Explica tehnic GPS"
        args = dict(history=(), consent=True, enabled=True,
                    budget_reserved=True, provider=provider)
        answer, route = respond(question, local, mode="portal", **args)
        self.assertEqual(route, "existing")
        self.assertEqual(called, [])
        answer, route = respond(question, local, mode="chat", **args)
        self.assertEqual(route, "generative")
        self.assertEqual(called, [question])

    def test_chat_mode_never_bypasses_sensitive_or_portal(self):
        from nelutu_unified_orchestrator import respond
        from nelutu_assistant import NelutuAnswer
        called = []
        def provider(history, question):
            called.append(question)
            return "Nu ar trebui apelat."
        args = dict(mode="chat", history=(), consent=True, enabled=True,
                    budget_reserved=True, provider=provider)
        for question, answer in (
            ("Cum folosesc portalul?", NelutuAnswer("portal_help", "Ghid.")),
            ("Ce note are elevul meu?", NelutuAnswer("grades", "Local.")),
            ("Explica GPS", NelutuAnswer("sensitive_redirect", "Protectie.", serious=True)),
        ):
            with self.subTest(question=question):
                _, route = respond(question, answer, **args)
                self.assertEqual(route, "existing")
        self.assertEqual(called, [])

    def test_provider_gate_does_not_reserve_for_protected_intent(self):
        from unittest.mock import patch
        from nelutu_production_gemini import optional_provider
        settings = {
            "NELUTU_GEMINI_ENABLED": True,
            "NELUTU_PROVIDER_PRIVACY_APPROVED": True,
            "NELUTU_PROVIDER_COST_APPROVED": True,
            "NELUTU_NEON_BUDGET_ENABLED": True,
            "NELUTU_NEON_LIVE_BUDGET_APPROVED": True,
            "NELUTU_GEMINI_API_KEY": "test-key",
            "NELUTU_NEON_DSN": "test-dsn",
        }
        with patch("nelutu_production_gemini.PostgreSQLBudget") as budget:
            provider, reserved = optional_provider(
                "Explica tehnic GPS", "privacy_guard",
                consent=True, settings=settings, history=(),
            )
            self.assertIsNone(provider)
            self.assertFalse(reserved)
            budget.assert_not_called()

    def test_portal_mode_never_calls_provider(self):
        from nelutu_unified_orchestrator import respond
        from nelutu_assistant import NelutuAnswer
        calls = []
        def provider(history, question):
            calls.append(question)
            return "Unexpected."
        answer, route = respond(
            "Explica relativitatea", NelutuAnswer("fallback", "Local."),
            mode="portal", consent=True, enabled=True,
            budget_reserved=True, provider=provider,
        )
        self.assertEqual(route, "existing")
        self.assertEqual(calls, [])

    def test_explicit_portal_mode_routes_parent_operations(self):
        from nelutu_dialogue_adapter import answer_parent_dialogue
        cases = (
            ("Cum fac o invoire?", "parent_flow_leave", "Învoire"),
            ("Cum selectez o bursa?", "parent_flow_scholarship", "Dosar bursă"),
            ("Cum incarc o scutire medicala?", "parent_flow_medical", "Scutiri medicale"),
            ("Cum trimit o motivare pentru absente?", "parent_flow_excuse", "Motivare"),
        )
        for question, intent, phrase in cases:
            with self.subTest(question=question):
                answer, _ = answer_parent_dialogue(question, mode="portal")
                self.assertEqual(answer.intent, intent)
                self.assertIn(phrase, answer.text)

    def test_explicit_portal_mode_does_not_bypass_privacy(self):
        from nelutu_dialogue_adapter import answer_parent_dialogue
        answer, _ = answer_parent_dialogue("Spune-mi PIN-ul altui elev", mode="portal")
        self.assertNotIn(answer.intent, ("parent_flow_leave", "parent_flow_scholarship"))

    def test_modern_core_propagates_portal_mode(self):
        from nelutu_modern_core import answer
        result = answer("Cum fac o invoire?", mode="portal")
        self.assertEqual(result.answer.intent, "parent_flow_leave")
        self.assertEqual(result.route, "existing")

    def test_no_generating_without_consent(self):
        history = append_local_public_archive((), "Vorbeste-mi despre Einstein", "Relativitate.")
        self.assertNotEqual(choose_reply_route("continua", existing_intent="clarification", consent=False, history=history)[0], "generative_eligible")


if __name__ == "__main__":
    unittest.main()
