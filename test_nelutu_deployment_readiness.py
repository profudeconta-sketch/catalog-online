"""Stage 62: no implicit positive deployment verdict from passing offline tests."""
import unittest
from dataclasses import replace
from nelutu_deployment_readiness import DeploymentEvidence, deployment_ready


class ReadinessTests(unittest.TestCase):
    def test_defaults_block(self):
        self.assertFalse(deployment_ready(DeploymentEvidence()))

    def test_every_external_condition_is_mandatory(self):
        approved = DeploymentEvidence(True, True, True, True, True, True, True)
        self.assertTrue(deployment_ready(approved))
        for field in vars(approved):
            with self.subTest(field=field):
                self.assertFalse(deployment_ready(replace(approved, **{field: False})))

    def test_truthy_values_do_not_count_as_verified(self):
        approved = DeploymentEvidence(True, True, True, True, True, True, True)
        for field in vars(approved):
            with self.subTest(field=field):
                self.assertFalse(deployment_ready(replace(approved, **{field: "yes"})))

    def test_invalid_evidence_blocks(self):
        self.assertFalse(deployment_ready(None))
        self.assertFalse(deployment_ready({"explicit_production_approval": True}))


if __name__ == "__main__":
    unittest.main()
