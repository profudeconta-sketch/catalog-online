"""Teste fără date reale pentru procesul-verbal al notelor la purtare."""
import datetime
import io
import unittest

from pypdf import PdfReader
from annual_closure_engine import CLJ_2026_2027_COURSE_INTERVALS
from conduct_council_report_pdf import ConductReportError, generate_conduct_council_pdf


def fixtures():
    students = [(i, f"Elev Exemplu {i:02d}", i + 8, f"TEST-{i:02d}", "1234") for i in range(1, 33)]
    end = CLJ_2026_2027_COURSE_INTERVALS[0].end_date.isoformat()
    grades = [
        {
            "student_key": f"TEST-{i:02d}",
            "interval_number": 1,
            "grade": 8 if i == 2 else (6 if i == 3 else 10),
            "awarded_on": end,
        }
        for i in range(1, 33)
    ]
    teachers = [f"Profesor exemplu {i}" for i in range(1, 16)]
    details = {
        "TEST-02": {
            "reason": "Abatere consemnată în PV de test",
            "document_id": "a" * 32,
            "sent_at_utc": "2026-10-23T09:00:00+00:00",
            "received_at_utc": "2026-10-23T12:00:00+00:00",
            "confirmation_id": "b" * 32,
            "registration_number": "TEST/25",
        },
        "TEST-03": {"reason": "Faptă înscrisă în PV de test"},
    }
    return students, grades, teachers, details


class ConductMinutesPdfTests(unittest.TestCase):
    def test_report_has_full_class_and_two_model_sections(self):
        students, grades, teachers, details = fixtures()
        pdf = generate_conduct_council_pdf(
            interval_number=1, students=students, conduct_records=grades,
            teacher_names=teachers, details_by_student=details,
        )
        self.assertTrue(pdf.startswith(b"%PDF-"))
        reader = PdfReader(io.BytesIO(pdf))
        self.assertEqual(len(reader.pages), 2, 'Modelul trebuie să încapă pe exact două pagini A4')
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Elev Exemplu 01", text)
        self.assertIn("Elev Exemplu 32", text)
        self.assertIn("Profesor exemplu 15", text)
        self.assertIn("TEST/25", text)
        self.assertIn("23.10.2026", text)
        self.assertIn("TEST-02", str(students))
        self.assertIn("sub 7", text)
        self.assertIn("Întocmit", text)

    def test_missing_grades_are_marked_and_never_fabricated(self):
        students, grades, teachers, details = fixtures()
        pdf = generate_conduct_council_pdf(
            interval_number=2, students=students, conduct_records=grades,
            teacher_names=teachers, details_by_student={},
        )
        reader = PdfReader(io.BytesIO(pdf))
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("PROIECT", text)
        self.assertIn("Notă neacordată", text)
        self.assertIn("22.12.2026", text)

    def test_duplicate_grade_fails_closed(self):
        students, grades, teachers, details = fixtures()
        grades.append(dict(grades[0]))
        with self.assertRaises(ConductReportError):
            generate_conduct_council_pdf(
                interval_number=1, students=students, conduct_records=grades,
                teacher_names=teachers, details_by_student=details,
            )

    def test_duplicate_student_identity_fails_closed(self):
        students, grades, teachers, details = fixtures()
        students[1] = (2, "Elev Duplicat", 10, students[0][3], "1234")
        with self.assertRaises(ConductReportError):
            generate_conduct_council_pdf(
                interval_number=1, students=students, conduct_records=grades,
                teacher_names=teachers, details_by_student=details,
            )

    def test_unverified_date_or_unassigned_student_blocks_report(self):
        students, grades, teachers, details = fixtures()
        details["TEST-02"]["received_at_utc"] = "bad-date"
        with self.assertRaises(ConductReportError):
            generate_conduct_council_pdf(
                interval_number=1, students=students, conduct_records=grades,
                teacher_names=teachers, details_by_student=details,
            )
        details["TEST-02"]["received_at_utc"] = "2026-10-23T12:00:00+00:00"
        details["OTHER_STUDENT"] = {"reason": "no"}
        with self.assertRaises(ConductReportError):
            generate_conduct_council_pdf(
                interval_number=1, students=students, conduct_records=grades,
                teacher_names=teachers, details_by_student=details,
            )


if __name__ == "__main__":
    unittest.main()
