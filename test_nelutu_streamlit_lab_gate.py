"""Offline gate regression checks: no external connections."""
import unittest
from unittest.mock import patch

from nelutu_streamlit_lab_gate import LabAccess, lab_remaining, lab_reserve


class LabGateTests(unittest.TestCase):
    @patch("nelutu_streamlit_lab_gate.IsolatedLabBudget")
    def test_disabled_or_unapproved_never_connects(self, budget):
        variants = [
            LabAccess(),
            LabAccess(enabled=True, dedicated_dsn="postgresql://test"),
            LabAccess(enabled=True, private_access_verified=True, dedicated_dsn="postgresql://test"),
            LabAccess(enabled=True, operator_confirmed=True, dedicated_dsn="postgresql://test"),
            LabAccess(enabled=True, private_access_verified=True, operator_confirmed=True),
            LabAccess(enabled=True, private_access_verified=True, operator_confirmed=True, dedicated_dsn="invalid"),
        ]
        for config in variants:
            with self.subTest(config=config):
                self.assertEqual(lab_remaining(config), 0)
                self.assertFalse(lab_reserve(config))
        budget.assert_not_called()

    @patch("nelutu_streamlit_lab_gate.IsolatedLabBudget")
    def test_explicit_approval_routes_only_to_lab(self, budget):
        config = LabAccess(
            enabled=True,
            private_access_verified=True,
            operator_confirmed=True,
            dedicated_dsn="postgresql://test",
        )
        budget.return_value.remaining.return_value = 2
        budget.return_value.reserve.return_value = True
        self.assertEqual(lab_remaining(config), 2)
        self.assertTrue(lab_reserve(config))
        budget.assert_called_with("postgresql://test", enabled=True)

    @patch("nelutu_streamlit_lab_gate.IsolatedLabBudget", side_effect=OSError("offline"))
    def test_errors_fail_closed(self, _):
        config = LabAccess(True, True, True, "postgresql://test")
        self.assertEqual(lab_remaining(config), 0)
        self.assertFalse(lab_reserve(config))


if __name__ == "__main__":
    unittest.main()
