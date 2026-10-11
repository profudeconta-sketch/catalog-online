import unittest
from nelutu_unified_orchestrator import respond
from nelutu_assistant import NelutuAnswer


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.fallback = NelutuAnswer("clarification", "Reformulează, te rog!")

    def test_existing_is_authoritative(self):
        answer = NelutuAnswer("portal_component", "Răspuns validat")
        out, route = respond("Salut!", answer, consent=True, enabled=True,
                             budget_reserved=True, provider=lambda *a: "Altceva")
        self.assertIs(out, answer)
        self.assertEqual(route, "existing")

    def test_generates_only_with_all_gates(self):
        calls = []
        def provider(history, question):
            calls.append(question)
            return "No, putem povesti liber!"
        out, route = respond("Salut, ce mai faci?", self.fallback,
                             consent=True, enabled=True, budget_reserved=True,
                             provider=provider)
        self.assertEqual(route, "generative")
        self.assertEqual(len(calls), 1)
        self.assertIn("povesti", out.text)

    def test_no_network_without_quota(self):
        def forbidden(*args):
            raise AssertionError("Provider must not be invoked")
        out, route = respond("Salut, ce mai faci?", self.fallback,
                             consent=True, enabled=True, budget_reserved=False,
                             provider=forbidden)
        self.assertIs(out, self.fallback)

    def test_tutorial_not_sent_to_provider(self):
        def forbidden(*args):
            raise AssertionError("School help stays local")
        out, route = respond("Cum introduc notele in aplicatia profesorului?",
                             self.fallback, consent=True, enabled=True,
                             budget_reserved=True, provider=forbidden)
        self.assertEqual(route, "tutorial")
        self.assertIn("Notele", out.text)

    def test_provider_failure_keeps_existing(self):
        out, route = respond("Salut, ce mai faci?", self.fallback,
                             consent=True, enabled=True, budget_reserved=True,
                             provider=lambda *args: None)
        self.assertIs(out, self.fallback)


if __name__ == "__main__":
    unittest.main()
