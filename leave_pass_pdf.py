"""Generator PDF pentru biletul de voie aprobat."""

from __future__ import annotations

import datetime as dt
import html
from io import BytesIO
from zoneinfo import ZoneInfo

import fontpkg
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

SCHOOL_NAME = "COLEGIUL „EMIL NEGRUȚIU” TURDA"
SCHOOL_YEAR = "2026–2027"
CLASS_NAME = "CLASA a IX-a TH (TURISM ȘI ALIMENTAȚIE)"
TEACHER_NAME = "Prof. Ec. Gherman Octavian-Theodor"
FONT_REGULAR = "LeavePassNoto"
FONT_BOLD = "LeavePassNotoBold"


def _safe(value):
    return html.escape(str(value or "").strip())


def _register_fonts():
    font_path = str(fontpkg.path("Noto Sans"))
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, font_path))
    if FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_BOLD, font_path))
    pdfmetrics.registerFontFamily(
        FONT_REGULAR,
        normal=FONT_REGULAR,
        bold=FONT_BOLD,
        italic=FONT_REGULAR,
        boldItalic=FONT_BOLD,
    )


def _local_display(value):
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(ZoneInfo("Europe/Bucharest")).strftime("%d.%m.%Y, ora %H:%M")


def generate_leave_pass_pdf(*, parent_name, student_name, request_date, departure_time,
                            reason_label, transmitted_at_utc, approved_at_utc,
                            request_id):
    required = [parent_name, student_name, request_date, departure_time, reason_label,
                transmitted_at_utc, approved_at_utc, request_id]
    if not all(str(v or "").strip() for v in required):
        raise ValueError("Date insuficiente pentru generarea biletului de voie.")

    _register_fonts()
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm,
        topMargin=18*mm, bottomMargin=18*mm, title="Bilet de voie",
        author=SCHOOL_NAME, invariant=1,
    )
    styles = getSampleStyleSheet()
    centered = ParagraphStyle("LeaveCentered", parent=styles["Normal"], fontName=FONT_REGULAR,
                              fontSize=10, leading=13, alignment=TA_CENTER)
    title = ParagraphStyle("LeaveTitle", parent=styles["Title"], fontName=FONT_BOLD,
                           fontSize=16, leading=20, alignment=TA_CENTER, spaceBefore=12, spaceAfter=16)
    body = ParagraphStyle("LeaveBody", parent=styles["BodyText"], fontName=FONT_REGULAR,
                          fontSize=11, leading=17, alignment=TA_JUSTIFY, spaceAfter=10)
    note = ParagraphStyle("LeaveNote", parent=body, fontSize=9, leading=13, spaceBefore=10)

    date_display = dt.date.fromisoformat(str(request_date)).strftime("%d.%m.%Y")
    story = [
        Paragraph(SCHOOL_NAME, centered),
        Paragraph(f"AN ȘCOLAR {SCHOOL_YEAR} | {CLASS_NAME}", centered),
        Spacer(1, 10),
        Paragraph("BILET DE VOIE", title),
        Paragraph(
            f"Subsemnatul/Subsemnata <b>{_safe(parent_name)}</b>, în calitate de părinte/reprezentant legal "
            f"al elevului/elevei <b>{_safe(student_name)}</b>, vă rog să aprobați învoirea fiului/fiicei mele "
            f"în data de <b>{date_display}</b>, începând cu ora <b>{_safe(departure_time)}</b>, "
            f"din <b>{_safe(reason_label).lower()}</b>.", body),
        Paragraph(
            "Am luat la cunoștință că prezentul bilet de voie <b>nu reprezintă o motivare/scutire</b> "
            "și că, pentru absențele consemnate în catalog ca urmare a prezentei învoiri, trebuie să "
            "prezint o motivare/scutire valabilă, în conformitate cu procedurile aplicabile.", body),
        Spacer(1, 8),
        Paragraph(f"Părinte/Reprezentant legal: <b>{_safe(parent_name)}</b>", body),
        Paragraph(f"Solicitare transmisă prin contul autentificat aferent elevului la: "
                  f"<b>{_local_display(transmitted_at_utc)}</b>", body),
        Spacer(1, 12),
        Paragraph("<b>SE APROBĂ</b>", body),
        Paragraph(f"Profesor diriginte: <b>{TEACHER_NAME}</b>", body),
        Paragraph(f"Aprobat la: <b>{_local_display(approved_at_utc)}</b>", body),
        Paragraph(
            "Document generat automat de sistemul informatic pe baza solicitării transmise prin contul "
            "autentificat aferent elevului și a aprobării profesorului diriginte.", note),
        Paragraph(f"ID solicitare: {_safe(request_id)}", note),
    ]
    doc.build(story)
    return output.getvalue()
