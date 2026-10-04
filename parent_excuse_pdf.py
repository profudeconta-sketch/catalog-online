"""Generator PDF pentru cererile de motivare/scutire transmise de parinte."""
from __future__ import annotations
import datetime as dt
import io
import os
import reportlab
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

SCHOOL_NAME = 'Colegiul "Emil Negruțiu" Turda'
SCHOOL_ADDRESS = "Str. Agriculturii nr. 27"
SCHOOL_PHONE = "telefon: 0264/312637; 0728 972264"
SCHOOL_FAX = "fax: 0264/317051"
SCHOOL_EMAIL = "email: emilnegrutiu@gmail.com"

FONT_REGULAR = "ParentExcuseVera"
FONT_BOLD = "ParentExcuseVeraBold"


def _register_unicode_fonts():
    fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    regular_path = os.path.join(fonts_dir, "Vera.ttf")
    bold_path = os.path.join(fonts_dir, "VeraBd.ttf")
    if not os.path.isfile(regular_path) or not os.path.isfile(bold_path):
        raise RuntimeError("Fonturile Unicode necesare pentru PDF nu sunt disponibile.")
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, regular_path))
    if FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
    pdfmetrics.registerFontFamily(
        "ParentExcuseVera",
        normal=FONT_REGULAR,
        bold=FONT_BOLD,
        italic=FONT_REGULAR,
        boldItalic=FONT_BOLD,
    )


def _safe(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_parent_excuse_pdf(*, parent_name, parent_role, student_name, student_address, nr_matr, absence_date, hours, generated_date=None):
    parent_name, parent_role = str(parent_name or "").strip(), str(parent_role or "").strip()
    student_name, student_address = str(student_name or "").strip(), str(student_address or "").strip()
    nr_matr = str(nr_matr or "").strip()
    if not all([parent_name, parent_role, student_name, nr_matr]):
        raise ValueError("Date obligatorii lipsă pentru generarea cererii.")
    try:
        hours = int(hours)
    except (TypeError, ValueError) as ex:
        raise ValueError("Numărul de ore nu este valid.") from ex
    if hours < 1:
        raise ValueError("Cererea trebuie să conțină cel puțin o oră.")
    if isinstance(absence_date, str):
        absence_date = dt.date.fromisoformat(absence_date)
    if not isinstance(absence_date, dt.date) or absence_date > dt.date.today():
        raise ValueError("Data absenței nu este validă.")
    generated_date = generated_date or dt.date.today()

    _register_unicode_fonts()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm, topMargin=18*mm, bottomMargin=18*mm, title="Scutire/Motivare Absențe", author=SCHOOL_NAME, invariant=1)
    styles = getSampleStyleSheet()
    header = ParagraphStyle("Header", parent=styles["Normal"], fontName=FONT_REGULAR, fontSize=10, leading=13, alignment=TA_LEFT)
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName=FONT_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, spaceBefore=12, spaceAfter=16)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontName=FONT_REGULAR, fontSize=11, leading=17, alignment=TA_JUSTIFY, spaceAfter=10)
    note = ParagraphStyle("Note", parent=styles["BodyText"], fontName=FONT_REGULAR, fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceBefore=10)

    story = [
        Paragraph(f"<b>{_safe(SCHOOL_NAME)}</b>", header), Paragraph(_safe(SCHOOL_ADDRESS), header),
        Paragraph(_safe(SCHOOL_PHONE), header), Paragraph(_safe(SCHOOL_FAX), header), Paragraph(_safe(SCHOOL_EMAIL), header),
        Paragraph(f"Data documentului: {generated_date.strftime('%d.%m.%Y')}", header), Spacer(1, 5*mm),
        Paragraph("Scutire/Motivare Absențe", title),
        Paragraph(f"Subsemnatul/Subsemnata <b>{_safe(parent_name)}</b>, în calitate de <b>{_safe(parent_role)}</b> al/a elevului/elevei <b>{_safe(student_name)}</b>, cu adresa <b>{_safe(student_address) or '-'}</b>, NR. MATR. <b>{_safe(nr_matr)}</b>, vă rog să luați în considerare motivarea absențelor din data de <b>{absence_date.strftime('%d.%m.%Y')}</b>, în număr de <b>{hours}</b> ore de curs.", body),
        Paragraph("Vă mulțumesc.", body), Spacer(1, 8*mm),
        Paragraph(f"Părinte/Reprezentant legal: <b>{_safe(parent_name)}</b>", body),
        Paragraph("Prezentul document a fost generat și transmis prin contul autentificat al părintelui/reprezentantului legal, sistemul informatic înregistrând data și ora transmiterii.", note),
        Paragraph("Prin transmiterea documentului prin intermediul platformei, cererea este considerată înaintată dirigintelui și este luată în considerare în aceleași condiții administrative ca o cerere predată personal dirigintelui la unitatea de învățământ. Nu este necesară depunerea suplimentară a aceluiași document în format tipărit.", note),
        Paragraph("În situația în care sunt necesare informații, documente sau clarificări suplimentare, dirigintele va contacta părintele/reprezentantul legal pentru remedierea situației.", note),
    ]
    doc.build(story)
    return output.getvalue()
