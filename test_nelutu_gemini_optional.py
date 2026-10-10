"""Offline safety and contract tests: no real Gemini calls or credentials."""
import json
import unittest
from unittest.mock import patch
import nelutu_gemini_optional as gemini


class GeminiOptionalTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.object(gemini.request, "urlopen") as opener:
            self.assertIsNone(gemini.generate("Ce mai faci?", api_key="dummy"))
            opener.assert_not_called()

    def test_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(gemini.generate("Ce mai faci?", enabled=True))

    def test_blocks_private_and_school_content(self):
        for question in (
            "Ce note are elevul?", "Am nevoie de catalog",
            "Numarul meu e 0742123456", "Scrie la test@example.com",
            "Am un diagnostic medical", "PIN 123456",
        ):
            with self.subTest(question=question):
                self.assertFalse(gemini.is_public_general_chat(question))
                self.assertIsNone(gemini.generate(question, api_key="dummy", enabled=True))

    def test_rejects_unsafe_history(self):
        self.assertIsNone(gemini.generate(
            "Ce mai faci?", (("user", "Notele elevului sunt bune"),),
            api_key="dummy", enabled=True, public_text_confirmed=True,
        ))

    def test_confirmation_required(self):
        self.assertIsNone(gemini.generate("Ce mai faci?", api_key="dummy", enabled=True))

    def test_public_conversation_can_use_mocked_provider(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "candidates": [{"content": {"parts": [{"text": "No, bine! 🤠"}]}}]
                }).encode()
        with patch.object(gemini.request, "urlopen", return_value=Response()) as opener:
            result = gemini.generate(
                "Și eu sunt bine.",
                api_key="dummy", enabled=True, public_text_confirmed=True,
            )
            self.assertEqual(result, "No, bine! 🤠")
            args, kwargs = opener.call_args
            self.assertEqual(kwargs["timeout"], gemini.TIMEOUT)
            payload = json.loads(args[0].data)
            self.assertEqual(len(payload["contents"]), 1)
            self.assertEqual(payload["contents"][-1]["parts"][0]["text"], "Și eu sunt bine.")


if __name__ == "__main__":
    unittest.main()
