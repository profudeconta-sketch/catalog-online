"""Regresii pentru fișa PDF completă a elevului, fără acces la date reale."""
import io
import unittest

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from pypdf import PdfReader

from student_profile_pdf import (
    append_student_profile_pdf, find_student_profile, profile_sections,
)


def _record():
    return {
        "id": 1, "nume": "TEST", "initiala": "V.", "prenume": "ANA",
        "nume_complet": "TEST V. ANA", "rand_excel": "1", "matricol": "126/1",
        "cnp": "1234567890123", "telefon": "0700000000", "pin": "CONFIDENTIAL-9999",
        "nationalitate": "Română", "cetatenie": "Română", "etnie": "Română",
        "localitate": "Turda", "judet": "Cluj", "strada": "Test <script>alert(1)</script> & Co",
        "numar_strada": "2", "bloc": "B2", "apartament": "10",
        "nume_mama": "Maria Test", "telefon_mama": "0700000001",
        "mama_plecata": False, "tara_mama": "",
        "nume_tata": "Ion Test", "telefon_tata": "0700000002",
        "tata_plecat": True, "tara_tata": "Germania",
        "parinte_unic_sustinator_plecat": False,
        "parinte_unic_sustinator_plecat_tip": "Nu",
        "stare_civila_parinti": "Divorțați", "locuieste_cu": "Bunici",
        "revenit_strainatate_peste_un_an": False,
        "ingrijitor_nume": "Bunica Test", "ingrijitor_telefon": "0700000003",
        "ces": False, "orfan": False, "plasament": False,
        "bursa_medicala": True, "bursa_venit": False,
        "status_scolar": "TRANSFERAT",
        "istoric_miscare": [
            {"tip": "ADAUGAT", "data": "2026-09-07"},
            {"tip": "TRANSFERAT", "data": "2026-11-12", "unitate": "Alta scoala"},
        ],
        "rubrica_personalizata": "Detaliu suplimentar",
        "secret_token": "NU-EXPORTA",
    }


class StudentProfilePdfTests(unittest.TestCase):
    def test_rejects_wrong_student_or_duplicate_before_pdf(self):
        row = _record()
        identity = (1, "TEST V. ANA", "1", "126/1", "SECRET")
        self.assertEqual(find_student_profile([row], identity)["matricol"], "126/1")
        with self.assertRaises(ValueError):
            find_student_profile([row, dict(row)], identity)
        with self.assertRaises(ValueError):
            find_student_profile([row], (2, "TEST V. ANA", "1", "126/1", "SECRET"))
        with self.assertRaises(ValueError):
            find_student_profile([row], (1, "ALT ELEV", "1", "126/1", "SECRET"))

    def test_every_management_field_except_credentials_is_exported(self):
        row = _record()
        sections = profile_sections(row)
        self.assertEqual(len(sections), 7)
        labels_values = [x for _, group in sections for x in group]
        all_displayed = " ".join(str(value) for _, value in labels_values)
        self.assertEqual(len(labels_values), len(row) - 2)
        for value in ("1234567890123", "Germania", "Bunica Test",
                      "Divorțați", "TRANSFERAT", "2026-11-12",
                      "Detaliu suplimentar", "Maria Test"):
            self.assertIn(value, all_displayed)
        self.assertNotIn("CONFIDENTIAL-9999", all_displayed)
        self.assertNotIn("NU-EXPORTA", all_displayed)
        self.assertIn(("Mamă plecată în străinătate", "Nu"), labels_values)
        self.assertIn(("Tată plecat în străinătate", "Da"), labels_values)

    def test_pdf_renders_before_school_results_with_unicode_and_escaped_markup(self):
        row = _record()
        styles = getSampleStyleSheet()
        stream = io.BytesIO()
        story = [Paragraph("FIȘĂ ELEV", styles["Heading1"])]
        append_student_profile_pdf(
            story, row,
            heading_style=styles["Heading2"],
            cell_style=styles["Normal"],
            cell_bold=styles["Normal"],
            pdf_clean=lambda value: value,
        )
        story.append(Paragraph("ACADEMIC_RESULTS_BEGIN", styles["Heading2"]))
        SimpleDocTemplate(
            stream, pagesize=A4, rightMargin=36, leftMargin=36,
            topMargin=36, bottomMargin=36,
        ).build(story)
        pdf_bytes = stream.getvalue()
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        pdf = PdfReader(io.BytesIO(pdf_bytes))
        body = "\n".join(page.extract_text() for page in pdf.pages)
        self.assertLess(body.index("DATE DE IDENTIFICARE"), body.index("ACADEMIC_RESULTS_BEGIN"))
        self.assertIn("1234567890123", body)
        self.assertIn("TRANSFERAT", body)
        self.assertIn("Detaliu suplimentar", body)
        self.assertNotIn("CONFIDENTIAL-9999", body)
        self.assertNotIn("NU-EXPORTA", body)


if __name__ == "__main__":
    unittest.main()
