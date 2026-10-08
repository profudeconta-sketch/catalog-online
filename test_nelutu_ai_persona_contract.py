"""Persona contract checks. Static checks do not certify model behavior."""
import unittest
from nelutu_ai_experiment import NELUTU_PERSONA

class PersonaContractTests(unittest.TestCase):
    def test_unconditional_civility(self):
        self.assertIn("Politețea este necondiționată", NELUTU_PERSONA)
        self.assertIn("nu răspunzi cu insulte", NELUTU_PERSONA)

    def test_no_manipulation_or_school_propaganda(self):
        self.assertIn("Nu faci propagandă", NELUTU_PERSONA)
        self.assertIn("nu manipulezi emoțiile", NELUTU_PERSONA)

    def test_no_impersonation_of_human_or_teacher(self):
        self.assertIn("Nu pretinzi că ești om", NELUTU_PERSONA)
        self.assertIn("nu înlocuiește dirigintele", NELUTU_PERSONA)

    def test_supports_legitimate_criticism(self):
        self.assertIn("Recunoști nemulțumirile legitime", NELUTU_PERSONA)

if __name__ == "__main__":
    unittest.main()
