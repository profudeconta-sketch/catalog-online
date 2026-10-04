"""Generator PDF pentru cererile de motivare/scutire transmise de parinte."""
from __future__ import annotations
import datetime as dt
import io
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

SCHOOL_NAME = 'Colegiul "Emil Negrutiu" Turda'
SCHOOL_ADDRESS = "Str. Agriculturii nr. 27"
SCHOOL_PHONE = "telefon: 0264/312637; 0728 972264"
SCHOOL_FAX = "fax: 0264/317051"
SCHOOL_EMAIL = "email: emilnegrutiu@gmail.com"

def _safe(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_parent_excuse_pdf(*, parent_name, parent_role, student_name, student_address, nr_matr, absence_date, hours, generated_date=None):
    parent_name, parent_role = str(parent_name or "").strip(), str(parent_role or "").strip()
    student_name, student_address = str(student_name or "").strip(), str(student_address or "").strip()
    nr_matr = str(nr_matr or "").strip()
    if not all([parent_name, parent_role, student_name, nr_matr]):
        raise ValueError("Date obligatorii lipsa pentru generarea cererii.")
    try:
        hours = int(hours)
    except (TypeError, ValueError) as ex:
        raise ValueError("Numarul de ore nu este valid.") from ex
    if hours < 1:
        raise ValueError("Cererea trebuie sa contina cel putin o ora.")
    if isinstance(absence_date, str):
        absence_date = dt.date.fromisoformat(absence_date)
    if not isinstance(absence_date, dt.date) or absence_date > dt.date.today():
        raise ValueError("Data absentei nu este valida.")
    generated_date = generated_date or dt.date.today()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm, topMargin=18*mm, bottomMargin=18*mm, title="Scutire/Motivare Absente", author=SCHOOL_NAME)
    styles = getSampleStyleSheet()
    header = ParagraphStyle("Header", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=13, alignment=TA_LEFT)
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=TA_CENTER, spaceBefore=12, spaceAfter=16)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=11, leading=17, alignment=TA_JUSTIFY, spaceAfter=10)
    note = ParagraphStyle("Note", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceBefore=10)

    story = [
        Paragraph(f"<b>{_safe(SCHOOL_NAME)}</b>", header), Paragraph(_safe(SCHOOL_ADDRESS), header),
        Paragraph(_safe(SCHOOL_PHONE), header), Paragraph(_safe(SCHOOL_FAX), header), Paragraph(_safe(SCHOOL_EMAIL), header),
        Paragraph(f"Data documentului: {generated_date.strftime('%d.%m.%Y')}", header), Spacer(1, 5*mm),
        Paragraph("Scutire/Motivare Absente", title),
        Paragraph(f"Subsemnatul/Subsemnata <b>{_safe(parent_name)}</b>, in calitate de <b>{_safe(parent_role)}</b> al/a elevului/elevei <b>{_safe(student_name)}</b>, cu adresa <b>{_safe(student_address) or '-'}</b>, NR. MATR. <b>{_safe(nr_matr)}</b>, va rog sa luati in considerare motivarea absentelor din data de <b>{absence_date.strftime('%d.%m.%Y')}</b>, in numar de <b>{hours}</b> ore de curs.", body),
        Paragraph("Va multumesc.", body), Spacer(1, 8*mm),
        Paragraph(f"Parinte/Reprezentant legal: <b>{_safe(parent_name)}</b>", body),
        Paragraph("Prezentul document a fost generat si transmis prin contul autentificat al parintelui/reprezentantului legal, sistemul informatic inregistrand data si ora transmiterii.", note),
        Paragraph("Prin transmiterea documentului prin intermediul platformei, cererea este considerata inaintata dirigintelui si este luata in considerare in aceleasi conditii administrative ca o cerere predata personal dirigintelui la unitatea de invatamant. Nu este necesara depunerea suplimentara a aceluiasi document in format tiparit.", note),
        Paragraph("In situatia in care sunt necesare informatii, documente sau clarificari suplimentare, dirigintele va contacta parintele/reprezentantul legal pentru remedierea situatiei.", note),
    ]
    doc.build(story)
    return output.getvalue()
