"""No network calls: verify safe early exits and no credential leakage."""
import unittest
from nelutu_neon_isolated_diagnostic import diagnose_isolated_neon


class NeonDiagnosticTests(unittest.TestCase):
    def test_missing_connection(self):
        self.assertEqual(diagnose_isolated_neon(None), "missing_secret")

    def test_invalid_connection(self):
        self.assertEqual(diagnose_isolated_neon("not-a-dsn"), "invalid_scheme")

    def test_no_secret_in_status(self):
        secret = "private-password"
        result = diagnose_isolated_neon("invalid:" + secret)
        self.assertNotIn(secret, result)


if __name__ == "__main__":
    unittest.main()
