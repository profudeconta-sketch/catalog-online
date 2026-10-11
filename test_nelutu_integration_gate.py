"""Stage 44 integration boundary tests: no network, no school records."""
import unittest

from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_integration_gate import authorize_experimental_request


class IntegrationGateTests(unittest.TestCase):
    def test_all_prerequisites_required(self):
        args = dict(explicitly_enabled=True, confirmed=True,
                    provider_key_present=True, durable_gate_ready=True)
        self.assertTrue(authorize_experimental_request(DEMO_PROMPTS[0], **args).allowed)
        for field in args:
            with self.subTest(field=field):
                disabled = dict(args)
                disabled[field] = False
                self.assertFalse(
                    authorize_experimental_request(DEMO_PROMPTS[0], **disabled).allowed)

    def test_arbitrary_and_sensitive_text_denied(self):
        args = dict(explicitly_enabled=True, confirmed=True,
                    provider_key_present=True, durable_gate_ready=True)
        for message in ("Salut, Neluțu!", "Elevul are media 9", "", DEMO_PROMPTS[0] + " "):
            with self.subTest(message=message):
                self.assertFalse(authorize_experimental_request(message, **args).allowed)


if __name__ == "__main__":
    unittest.main()
