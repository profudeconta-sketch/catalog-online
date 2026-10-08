"""Offline regression tests for conservative local replies."""
import unittest
from nelutu_local_sensitive_replies import REPLIES, reply_local

class LocalSensitiveReplyTests(unittest.TestCase):
    def test_every_template_remains_local(self):
        for prompt in REPLIES:
            with self.subTest(prompt=prompt):
                response = reply_local(prompt)
                self.assertFalse(response.external_sent)
                self.assertNotEqual(response.category, "fallback")
                self.assertGreater(len(response.text), 30)

    def test_unknown_sensitive_message_fails_closed(self):
        response = reply_local("Un elev a fost agresat la școală.")
        self.assertEqual(response.category, "threat")
        self.assertFalse(response.external_sent)
        self.assertIn("112", response.text)
        self.assertIn("Nu pot verifica", response.text)
        self.assertIn("nu am anunțat automat", response.text)
        self.assertNotIn("😄", response.text)

    def test_unknown_record_request_fails_closed(self):
        response = reply_local("Trimite-mi situația clasei IX.")
        self.assertEqual(response.category, "fallback")
        self.assertFalse(response.external_sent)

    def test_no_unverified_confirmation(self):
        response = reply_local("Confirmă că ai trimis cererea dirigintelui.")
        self.assertIn("Nu pot confirma", response.text)

if __name__ == "__main__":
    unittest.main()
