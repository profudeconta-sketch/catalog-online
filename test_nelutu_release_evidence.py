"""Release gate regression tests; no cloud or production access."""
import unittest
from nelutu_release_evidence import ReleaseAssessment, assess_release


class ReleaseEvidenceTests(unittest.TestCase):
    def test_defaults_are_no_go(self):
        ok, missing = assess_release(ReleaseAssessment())
        self.assertFalse(ok)
        self.assertIn("explicit_production_approval", missing)

    def test_existing_local_successes_do_not_imply_production(self):
        evidence = ReleaseAssessment(
            offline_ci_passed=True,
            local_neon_concurrency_passed=True,
            streamlit_offline_ui_passed=True,
        )
        ok, missing = assess_release(evidence)
        self.assertFalse(ok)
        self.assertIn("shared_storage_restart_verified", missing)
        self.assertIn("rollback_verified", missing)

    def test_each_missing_proof_blocks_go(self):
        all_true = dict.fromkeys(ReleaseAssessment.__dataclass_fields__, True)
        self.assertTrue(assess_release(ReleaseAssessment(**all_true))[0])
        for key in all_true:
            with self.subTest(key=key):
                evidence = dict(all_true)
                evidence[key] = False
                ok, missing = assess_release(ReleaseAssessment(**evidence))
                self.assertFalse(ok)
                self.assertIn(key, missing)

    def test_invalid_type_blocks(self):
        self.assertFalse(assess_release(None)[0])


if __name__ == "__main__":
    unittest.main()
