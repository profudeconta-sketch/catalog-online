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

    def test_no_generating_without_consent(self):
        history = append_local_public_archive((), "Vorbeste-mi despre Einstein", "Relativitate.")
        self.assertNotEqual(choose_reply_route("continua", existing_intent="clarification", consent=False, history=history)[0], "generative_eligible")


if __name__ == "__main__":
    unittest.main()
