"""Teste sintetice, fara date de elevi reale si fara acces la repo-ul privat."""
import copy
import io
import unittest

from openpyxl import load_workbook
from isj_cluj_statistica_excel import build_isj_statistica_clasa


def pupil(name, cnp, etnie="Română", nationality="Română", **extra):
    return {
        "nume_complet": name,
        "cnp": cnp,
        "etnie": etnie,
        "nationalitate": nationality,
        **extra,
    }


class TestISJClujStatistics(unittest.TestCase):
    def test_layout_and_nominal_ethnicity(self):
        students = [
            pupil("ELEV A", "5110612123456", "Română"),
            pupil("ELEV B", "6121223123456", "Maghiară"),
            pupil("ELEV C", "6121224123456", "Romă", "Germană"),
        ]
        untouched = copy.deepcopy(students)
        buffer = io.BytesIO(build_isj_statistica_clasa(students))
        self.assertEqual(students, untouched, "Exportul nu poate altera gestiunea.")
        wb = load_workbook(buffer)
        ws = wb.active
        self.assertEqual(ws.page_setup.orientation, "landscape")
        self.assertEqual(str(ws.page_setup.paperSize), str(ws.PAPERSIZE_A4))
        self.assertEqual(ws.page_setup.fitToWidth, 1)
        self.assertEqual(ws.page_setup.fitToHeight, 1)
        self.assertIn("AR", str(ws.print_area))
        self.assertEqual(ws["A7"].value, "IX TH")
        self.assertEqual(ws["B7"].value, "Tehnician în turism")
        self.assertEqual(ws["C7"].value, 3)
        self.assertEqual(ws["D7"].value, 2)  # doua fete din CNP
        self.assertEqual(ws["K7"].value, 1)  # 15 ani la 01.01.2027
        self.assertEqual(ws["I7"].value, 2)  # 14 ani la 01.01.2027
        self.assertEqual(ws["AG7"].value, 2)  # cetatenie romana
        self.assertEqual(ws["AQ7"].value, 1)  # alta cetatenie
        self.assertEqual(ws["AI7"].value, 1)  # etnie romana
        self.assertEqual(ws["AK7"].value, 1)  # etnie maghiara
        self.assertEqual(ws["AM7"].value, 1)  # etnie roma
        self.assertEqual(ws["E7"].value, ws["C7"].value)
        self.assertEqual(ws["F7"].value, ws["D7"].value)
        self.assertEqual(ws["G7"].value, ws["C7"].value)
        self.assertEqual(ws["H7"].value, ws["D7"].value)
        self.assertEqual(ws["A10"].value, "Diriginte: Gherman Octavian-Theodor")
        self.assertEqual(ws["A14"].value, "ELEV B")
        self.assertEqual(ws["AI14"].value, "Maghiară")
        self.assertEqual(ws["A15"].value, "ELEV C")
        self.assertEqual(ws["AI15"].value, "Romă")
        for row in (13, 14, 15):
            for col in ("A", "B", "AH", "AI", "AJ", "AR"):
                self.assertEqual(ws[f"{col}{row}"].border.top.style, "medium")
                self.assertEqual(ws[f"{col}{row}"].border.bottom.style, "medium")
            self.assertEqual(ws[f"A{row}"].border.left.style, "medium")
            self.assertEqual(ws[f"AH{row}"].border.right.style, "medium")
            self.assertEqual(ws[f"AI{row}"].border.left.style, "medium")
            self.assertEqual(ws[f"AR{row}"].border.right.style, "medium")
        wb.close()

    def test_missing_cnp_does_not_guess_gender_or_age(self):
        students = [pupil("NUME CARE POATE INDUCE IN EROARE", "", "Română")]
        ws = load_workbook(io.BytesIO(build_isj_statistica_clasa(students))).active
        self.assertEqual(ws["C7"].value, 1)
        self.assertIsNone(ws["D7"].value)
        self.assertIsNone(ws["I7"].value)
        self.assertIsNone(ws["K7"].value)
        self.assertIn("Verificare date", ws["A17"].value)

    def test_a_student_added_after_the_start_does_not_change_start_totals(self):
        original = pupil("ELEV ORIGINAL", "5110612123456")
        later = pupil("ELEV VENIT", "6121223123456",
                      istoric_miscare=[{"tip": "ADAUGAT", "data": "2026-10-05"}])
        ws = load_workbook(io.BytesIO(build_isj_statistica_clasa([original, later]))).active
        self.assertEqual(ws["C7"].value, 1)

    def test_initial_enrollment_is_repeated_in_both_din_care_columns(self):
        student = pupil("ELEV TEST", "5110612123456",
                        prima_inscriere_nivel=True,
                        din_promotia_curenta=False,
                        provenit_din_repetentie=True)
        ws = load_workbook(io.BytesIO(build_isj_statistica_clasa([student]))).active
        self.assertEqual(ws["E7"].value, 1)
        self.assertEqual(ws["G7"].value, 1)
        self.assertEqual(ws["AE7"].value, 1)


if __name__ == "__main__":
    unittest.main()
