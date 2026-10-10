"""Stage 61: optional integration must never break the existing local response."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class BrokenQuota:
    def reserve(self):
        raise OSError("simulated persistent volume outage")


class BrokenSession:
    def allowed(self):
        raise RuntimeError("simulated session quota failure")


class GateOutageTests(unittest.TestCase):
    def params(self, directory):
        return dict(
            local_answer=lambda _: "Neluțu local.",
            settings=AdapterSettings(enabled=True, privacy_approved=True,
                                     infrastructure_verified=True),
            confirmed=True, provider_key_present=True,
            durable_budget=DurableBudget(str(Path(directory) / "quota.sqlite3")),
            session_budget=DemoBudget(),
            instance_gate=SharedBudgetGate(InstanceBudget()))

    def test_durable_backend_exception_never_sends(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.params(folder)
            args["durable_budget"] = BrokenQuota()
            sent = []
            result = route_single_answer(DEMO_PROMPTS[0],
                sender=lambda msg: sent.append(msg) or "Experimental", **args)
            self.assertEqual((result.source, result.provider_status),
                             ("local", "quota_gate_error"))
            self.assertEqual(sent, [])

    def test_session_backend_exception_never_sends(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.params(folder)
            args["session_budget"] = BrokenSession()
            sent = []
            result = route_single_answer(DEMO_PROMPTS[0],
                sender=lambda msg: sent.append(msg) or "Experimental", **args)
            self.assertEqual((result.source, result.provider_status),
                             ("local", "quota_gate_error"))
            self.assertEqual(sent, [])

    def test_invalid_optional_settings_preserve_local(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.params(folder)
            args["settings"] = None
            sent = []
            result = route_single_answer(DEMO_PROMPTS[0],
                sender=lambda msg: sent.append(msg) or "Experimental", **args)
            self.assertEqual((result.source, result.provider_status),
                             ("local", "invalid_settings"))
            self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
