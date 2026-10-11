"""Stage 50: prove that the local school context never reaches demo sender."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class DataBoundaryTests(unittest.TestCase):
    def test_local_answer_and_context_not_sent_to_demo_provider(self):
        private_marker = "PRIVATE_SCHOOL_CONTEXT_DO_NOT_SEND"
        with tempfile.TemporaryDirectory() as folder:
            outbound = []
            result = route_single_answer(
                DEMO_PROMPTS[0],
                local_answer=lambda _: "Date locale: " + private_marker,
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "budget.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda message: outbound.append(message) or "Răspuns demonstrativ.",
            )
            self.assertEqual(result.source, "experimental")
            self.assertEqual(outbound, [DEMO_PROMPTS[0]])
            self.assertFalse(any(private_marker in text for text in outbound))

    def test_school_question_never_sent_even_with_all_gates_enabled(self):
        with tempfile.TemporaryDirectory() as folder:
            outbound = []
            result = route_single_answer(
                "Ce absențe are elevul meu?",
                local_answer=lambda _: "Răspuns școlar local.",
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "budget.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda message: outbound.append(message) or "Nu trebuie apelat.",
            )
            self.assertEqual(result.text, "Răspuns școlar local.")
            self.assertEqual(result.source, "local")
            self.assertEqual(outbound, [])


if __name__ == "__main__":
    unittest.main()
