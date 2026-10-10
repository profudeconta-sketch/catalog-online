"""Stage 52: fail closed when the local answer engine cannot respond."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class LocalFailureTests(unittest.TestCase):
    def test_local_exception_blocks_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            outbound = []
            budget = DurableBudget(str(Path(directory) / "quota.sqlite3"))
            def failed_local(_):
                raise RuntimeError("simulated local failure")
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=failed_local,
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=budget, session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda m: outbound.append(m) or "Should not be sent")
            self.assertEqual(result.source, "local")
            self.assertEqual(result.provider_status, "local_error")
            self.assertFalse(outbound)
            self.assertTrue(budget.reserve())

    def test_invalid_local_result_blocks_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            outbound = []
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: None,
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(directory) / "quota.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda m: outbound.append(m) or "Should not be sent")
            self.assertEqual(result.provider_status, "local_invalid")
            self.assertFalse(outbound)


if __name__ == "__main__":
    unittest.main()
