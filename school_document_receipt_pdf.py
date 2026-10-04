"""Generator PDF pentru confirmarea primei accesări a documentelor Școală → Părinte."""
from __future__ import annotations

import datetime as dt
import io

import fontpkg
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

FONT_REGULAR = "SchoolReceiptNoto"
FONT_BOLD = "SchoolReceiptNotoBold"


def _register_unicode_fonts():
    font_path = str(fontpkg.path("Noto Sans"))
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, font_path))
    if FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BOLD, font_path))
    pdfmetrics.registerFontFamily("SchoolReceiptNoto", normal=FONT_REGULAR, bold=FONT_BOLD, italic=FONT_REGULAR, boldItalic=FONT_BOLD)


def _safe(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _as_utc_datetime(value):
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        parsed = dt.datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def generate_school_document_receipt_pdf(*, student_name, source_document_name, accessed_at_utc, source_document_id):
    student_name = str(student_name or "").strip()
    source_document_name = str(source_document_name or "").strip()
    source_document_id = str(source_document_id or "").strip()
    if not student_name or not source_document_name or not source_document_id:
        raise ValueError("Date obligatorii lipsă pentru generarea confirmării.")

    accessed = _as_utc_datetime(accessed_at_utc)
    _register_unicode_fonts()
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm, topMargin=18*mm, bottomMargin=18*mm, title="Confirmare de primire și luare la cunoștință", author=SCHOOL_NAME, invariant=1)
    styles = getSampleStyleSheet()
    header = ParagraphStyle("ReceiptHeader", parent=styles["Normal"], fontName=FONT_REGULAR, fontSize=10, leading=13, alignment=TA_LEFT)
    title = ParagraphStyle("ReceiptTitle", parent=styles["Title"], fontName=FONT_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, spaceBefore=12, spaceAfter=16)
    body = ParagraphStyle("ReceiptBody", parent=styles["BodyText"], fontName=FONT_REGULAR, fontSize=11, leading=17, alignment=TA_JUSTIFY, spaceAfter=10)
    note = ParagraphStyle("ReceiptNote", parent=styles["BodyText"], fontName=FONT_REGULAR, fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceBefore=10)
    date_text = accessed.strftime("%d.%m.%Y")
    time_text = accessed.strftime("%H:%M UTC")

    story = [
        Paragraph(f"<b>{_safe(SCHOOL_NAME)}</b>", header),
        Paragraph(_safe(SCHOOL_ADDRESS), header),
        Paragraph(_safe(SCHOOL_PHONE), header),
        Paragraph(_safe(SCHOOL_FAX), header),
        Paragraph(_safe(SCHOOL_EMAIL), header),
        Spacer(1, 5*mm),
        Paragraph("Confirmare de primire și luare la cunoștință", title),
        Paragraph(f"Documentul transmis de unitatea de învățământ a fost accesat prin contul autentificat aferent elevului <b>{_safe(student_name)}</b>, la data de <b>{date_text}</b>, ora <b>{time_text}</b>. Prin accesarea documentului se confirmă luarea la cunoștință a conținutului acestuia de către părintele/reprezentantul legal al elevului.", body),
        Paragraph(f"Document accesat: <b>{_safe(source_document_name)}</b>", body),
        Paragraph(f"Identificator document: <b>{_safe(source_document_id)}</b>", note),
        Paragraph("Prezenta confirmare a fost generată automat de sistemul informatic la prima accesare a documentului și atestă data și ora la care documentul a fost pus în consultare prin contul autentificat aferent elevului.", note),
    ]
    doc.build(story)
    return output.getvalue()
