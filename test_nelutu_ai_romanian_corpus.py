"""Extended offline Romanian quality corpus from synthetic, non-personal text.

Checks reviewed grammar repairs, idempotence, dialect preservation and
conservative behavior. Not a full grammar or generative-quality certificate.
"""
import unittest
from nelutu_ai_romanian import polish_romanian

ERROR_CASES = (
    ("Matematica ajută, pasând prin economie și artă.", "Matematica ajută, trecând prin economie și artă."),
    ("Explică folosind cu cuvinte tale.", "Explică folosind cu propriile tale cuvinte."),
    ("Te rog, nu ezita să cere ajutorul.", "Te rog, nu ezita să ceri ajutor."),
    ("Elevii învață să devină autonome în domenii concrete.", "Elevii învață să devină autonomi în domenii concrete."),
    ("Curiozitatea e ca un seminț de curiozitate.", "Curiozitatea e ca o sămânță de curiozitate."),
    ("Am citit știriile.", "Am citit informațiile."),
    ("Învăță activ pentru examen.", "Învață activ pentru examen."),
    ("Repetați cu timp și răbdare.", "Repetă la intervale regulate și răbdare."),
    ("Încearcă metoda: repetai la intervale crescute.", "Încearcă metoda: repetă la intervale din ce în ce mai mari."),
)

PRESERVE_CASES = (
    "No, așe-i! Câte un pic, în fiecare zi.",
    "No, amu să vedem cum stă treaba!",
    "Matematica ne ajută să socotim cheltuielile.",
    "Ele devin autonome și învață meserii.",
    "Cere ajutorul profesorului când nu înțelegi.",
    "Elevii pot învăța mai bine prin exerciții practice.",
    "Părinții au dreptul să ceară explicații.",
    "În caz de pericol imediat, sunați la 112.",
    "Nu am acces la catalog și nu pot confirma o trimitere.",
    "Nu cunosc datele altor elevi.",
    "Am spus «No, așe-i!» și am zâmbit.",
)

class RomanianCorpusTests(unittest.TestCase):
    def test_known_error_corpus(self):
        for source, expected in ERROR_CASES:
            with self.subTest(source=source):
                self.assertEqual(polish_romanian(source), expected)

    def test_preserve_correct_and_dialect(self):
        for source in PRESERVE_CASES:
            with self.subTest(source=source):
                self.assertEqual(polish_romanian(source), source)

    def test_idempotence_across_corpus(self):
        for source in (*PRESERVE_CASES, *(x for x, _ in ERROR_CASES)):
            with self.subTest(source=source):
                once = polish_romanian(source)
                self.assertEqual(polish_romanian(once), once)

    def test_non_string_rejected(self):
        for value in (None, 3, [], {}):
            with self.subTest(value=repr(value)):
                with self.assertRaises(TypeError):
                    polish_romanian(value)

if __name__ == "__main__":
    unittest.main()
