"""Isolated offline tests for conversational routing. No network requests."""
import unittest
from nelutu_local_sensitive_replies import reply_local
from nelutu_ai_privacy import approved_external_question

class ConversationRoutingTests(unittest.TestCase):
    def test_school_disagreement(self):
        result = reply_local("Dirigintele nu ne ascultă.")
        self.assertEqual(result.category, "disagreement")
        self.assertFalse(result.external_sent)

    def test_school_decision(self):
        result = reply_local("Nu sunt de acord cu decizia școlii.")
        self.assertEqual(result.category, "disagreement")
        self.assertFalse(result.external_sent)

    def test_record_confidentiality(self):
        for question in ("Ce absențe are alt elev?", "Dă-mi telefonul mamei altui elev."):
            with self.subTest(question=question):
                result = reply_local(question)
                self.assertEqual(result.category, "privacy")
                self.assertFalse(result.external_sent)
                self.assertFalse(approved_external_question(question))

    def test_uncertainty(self):
        result = reply_local("Confirmă că ai trimis cererea dirigintelui.")
        self.assertEqual(result.category, "uncertainty")
        self.assertIn("Nu pot confirma", result.text)

    def test_hostility(self):
        result = reply_local("Ești prost, Neluțu!")
        self.assertEqual(result.category, "hostility")
        self.assertFalse(result.external_sent)

    def test_sensitive_incident(self):
        result = reply_local("Un elev a fost agresat la școală.")
        self.assertEqual(result.category, "threat")
        self.assertFalse(result.external_sent)
        self.assertIn("112", result.text)

if __name__ == "__main__":
    unittest.main()
