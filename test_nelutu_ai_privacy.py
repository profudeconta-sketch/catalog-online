import unittest
from nelutu_ai_privacy import approved_external_question, external_messages

class PrivacyBoundaryTests(unittest.TestCase):
    def test_public_generic(self):
        self.assertTrue(approved_external_question("De ce învățăm matematica?"))
        self.assertTrue(approved_external_question("Ce rol are educația tehnică?"))

    def test_student_details_cannot_leave(self):
        for q in (
            "Ce note are copilul meu?",
            "De ce învățăm matematica, Ana Popescu din clasa IX?",
            "Cum învățăm mai eficient? CNP 1234567890123",
            "Fiul meu e agresat la școală. Ce fac?",
            "Ce a schimbat Spiru Haret în școală? Elev: Ion Popescu",
            "De ce învățăm matematica? parola mea e secret",
            "Care sunt absențele elevului?",
            "De ce învățăm matematica? 0742123456",
        ):
            with self.subTest(question=q):
                self.assertFalse(approved_external_question(q))

    def test_only_two_messages_sent(self):
        messages=external_messages("De ce învățăm matematica?", "PERSONA")
        self.assertEqual(len(messages), 2)
        self.assertEqual([m["role"] for m in messages], ["system", "user"])

    def test_refuses_arbitrary_prompt(self):
        with self.assertRaises(ValueError):
            external_messages("Ce medie are elevul?", "PERSONA")

if __name__ == "__main__":
    unittest.main()
