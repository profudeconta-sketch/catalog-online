"""Stage 53: malformed experimental responses must not replace local answers."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class ProviderResponseTests(unittest.TestCase):
    def test_invalid_provider_text_falls_back_to_local(self):
        for response in ("\x00", "salut\x01", "\n", 123, None):
            with self.subTest(response=repr(response)), tempfile.TemporaryDirectory() as folder:
                result = route_single_answer(
                    DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                    settings=AdapterSettings(enabled=True, privacy_approved=True,
                                             infrastructure_verified=True),
                    confirmed=True, provider_key_present=True,
                    durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                    session_budget=DemoBudget(),
                    instance_gate=SharedBudgetGate(InstanceBudget()),
                    sender=lambda _: response)
                self.assertEqual((result.source, result.text), ("local", "Răspuns local."))

    def test_trimmed_valid_provider_reply_is_one_response(self):
        with tempfile.TemporaryDirectory() as folder:
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda _: "  Servus!  ")
            self.assertEqual((result.source, result.text), ("experimental", "Servus!"))


if __name__ == "__main__":
    unittest.main()
