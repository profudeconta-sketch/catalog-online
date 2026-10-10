"""Offline regression checks for isolated PostgreSQL concurrency probe.

These checks do not connect to Neon, GitHub Actions, or Gemini.
"""
import ast
import pathlib
import unittest

PROBE = pathlib.Path(__file__).with_name("nelutu_neon_concurrency_probe.py")

class LiveProbeSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROBE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_probe_uses_isolated_schema(self):
        self.assertIn('sql.Identifier("nelutu_test_concurenta", name)', self.source)

    def test_probe_never_names_real_budget_table_in_sql(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if any(keyword in node.value.upper() for keyword in ("CREATE TABLE", "UPDATE ", "DROP TABLE", "SELECT used")):
                    self.assertNotIn("nelutu_gemini_budget", node.value)

    def test_probe_is_explicit_opt_in(self):
        self.assertIn('os.environ.get(DSN_ENV)', self.source)
        self.assertIn('if __name__ == "__main__":', self.source)

    def test_success_is_reported_only_after_cleanup(self):
        cleanup_pos = self.source.index('if not cleanup_ok:')
        success_pos = self.source.index('print("PASS" if passed else "FAIL"')
        self.assertGreater(success_pos, cleanup_pos)
        self.assertIn('raise RuntimeError("Isolated test table cleanup could not be verified")', self.source)

    def test_failures_do_not_count_as_refusals(self):
        self.assertIn('raise RuntimeError("Reservation failed; test is inconclusive")', self.source)

if __name__ == "__main__":
    unittest.main()
