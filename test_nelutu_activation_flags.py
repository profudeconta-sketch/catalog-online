"""Stage 56: optional Gemini flags must be explicit booleans and OFF by default."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class FlagTests(unittest.TestCase):
    def test_default_is_disabled(self):
        self.assertEqual(AdapterSettings(), AdapterSettings(False, False, False))

    def test_invalid_flags_do_not_send(self):
        configurations = [
            AdapterSettings(enabled="true", privacy_approved=True, infrastructure_verified=True),
            AdapterSettings(enabled=True, privacy_approved="yes", infrastructure_verified=True),
            AdapterSettings(enabled=True, privacy_approved=True, infrastructure_verified=1),
        ]
        for settings in configurations:
            with self.subTest(settings=settings), tempfile.TemporaryDirectory() as folder:
                outbound = []
                result = route_single_answer(
                    DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                    settings=settings, confirmed=True, provider_key_present=True,
                    durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                    session_budget=DemoBudget(),
                    instance_gate=SharedBudgetGate(InstanceBudget()),
                    sender=lambda message: outbound.append(message) or "Experimental")
                self.assertEqual((result.source, result.provider_status),
                                 ("local", "invalid_settings"))
                self.assertEqual(outbound, [])

    def test_disabled_flags_preserve_local(self):
        with tempfile.TemporaryDirectory() as folder:
            outbound = []
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                settings=AdapterSettings(), confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda message: outbound.append(message) or "Experimental")
            self.assertEqual(result.source, "local")
            self.assertEqual(outbound, [])


if __name__ == "__main__":
    unittest.main()
