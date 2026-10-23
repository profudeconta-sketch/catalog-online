"""Proces-verbal al consiliului clasei: PDF read-only, fără salvări în registre.

Model: PV_note_la_purtare[1].docx, furnizat de diriginte (două pagini).
Datele fără dovadă verificată se afișează ca necompletate; PDF este proiect
până la asumare, semnare și validarea instituțională corespunzătoare.
"""
from __future__ import annotations

import base64
import datetime as dt
import io
import os
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from annual_closure_engine import CLJ_2026_2027_COURSE_INTERVALS
from conduct_council_header_assets import CREST_JPEG_B64, MINISTRY_JPEG_B64


class ConductReportError(ValueError):
    pass


SCHOOL_NAME = 'Colegiul „Emil Negruțiu”'
SCHOOL_CLASS = 'a IX-a TH'
DIRIGINTE = 'Gherman Octavian-Theodor'
SCHOOL_CONTACT = (
    'Str. Agriculturii nr. 27, Turda, 401100, jud. Cluj',
    'Tel./fax: 0264312637',
    'E-mail: emilnegrutiu@gmail.com | www.emilnegrutiu.ro',
)


def _font_names():
    paths = (
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
         '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'),
    )
    for normal_path, bold_path in paths:
        if os.path.isfile(normal_path) and os.path.isfile(bold_path):
            for name, path in (('PVUnicode', normal_path), ('PVUnicodeBold', bold_path)):
                if name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(name, path))
            return 'PVUnicode', 'PVUnicodeBold'
    raise ConductReportError('Nu sunt disponibile fonturi Unicode pentru diacritice.')


def _safe(value):
    return escape(str(value if value is not None else '').strip())


def _date_local(value):
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('Missing timezone')
        return parsed.astimezone(ZoneInfo('Europe/Bucharest')).strftime('%d.%m.%Y')
    except (TypeError, ValueError, OverflowError) as exc:
        raise ConductReportError('O dată a documentelor este invalidă.') from exc


def _validate_inputs(interval_number, students, conduct_records, details_by_student):
    intervals = {x.number: x for x in CLJ_2026_2027_COURSE_INTERVALS}
    if type(interval_number) is not int or interval_number not in intervals:
        raise ConductReportError('Intervalul de cursuri nu este valid.')
    if not students or not isinstance(students, (list, tuple)):
        raise ConductReportError('Lista clasei lipsește.')
    if not isinstance(conduct_records, list):
        raise ConductReportError('Registrul de purtare nu are formatul așteptat.')
    if not isinstance(details_by_student, dict):
        raise ConductReportError('Datele suplimentare au un format invalid.')

    student_keys = []
    for item in students:
        if len(item) < 4 or not str(item[1]).strip() or not str(item[3]).strip():
            raise ConductReportError('Lista clasei conține identități incomplete.')
        student_keys.append(str(item[3]).strip())
    if len(set(student_keys)) != len(student_keys):
        raise ConductReportError('Există elevi cu identificatori duplicați.')

    relevant = {}
    for rec in conduct_records:
        if not isinstance(rec, dict):
            raise ConductReportError('Registrul la purtare conține înregistrări invalide.')
        number = rec.get('interval_number')
        if type(number) is not int or number not in intervals:
            raise ConductReportError('Registrul la purtare conține intervale invalide.')
        key = str(rec.get('student_key') or '').strip()
        grade = rec.get('grade')
        if not key or type(grade) is not int or not 1 <= grade <= 10:
            raise ConductReportError('Registrul la purtare conține o notă sau identitate invalidă.')
        if number == interval_number:
            if key in relevant:
                raise ConductReportError('O notă la purtare este duplicată; raportul a fost blocat.')
            relevant[key] = grade
    for key, detail in details_by_student.items():
        if key not in student_keys or not isinstance(detail, dict):
            raise ConductReportError('Asociere elev-document invalidă.')
    return intervals[interval_number], relevant


def _draw_header(canvas, doc, regular, bold):
    canvas.saveState()
    pw, ph = A4
    # Siglele sunt extrase din modelul Word atașat, nu redesenate sau inventate.
    emblem = ImageReader(io.BytesIO(base64.b64decode(CREST_JPEG_B64, validate=True)))
    ministry = ImageReader(io.BytesIO(base64.b64decode(MINISTRY_JPEG_B64, validate=True)))
    canvas.drawImage(emblem, 14 * mm, ph - 31 * mm,
                     width=20 * mm, height=22 * mm, mask='auto')
    canvas.drawImage(ministry, pw - 76 * mm, ph - 25 * mm,
                     width=62 * mm, height=16 * mm, mask='auto')
    canvas.setFont(bold, 8)
    canvas.drawString(37 * mm, ph - 15 * mm, SCHOOL_NAME)
    canvas.setFont(regular, 6.7)
    for index, line in enumerate(SCHOOL_CONTACT):
        canvas.drawString(37 * mm, ph - (20 + 4 * index) * mm, line)
    canvas.setStrokeColor(colors.HexColor('#64748b'))
    canvas.setLineWidth(0.4)
    canvas.line(14 * mm, ph - 34 * mm, pw - 14 * mm, ph - 34 * mm)
    canvas.restoreState()


def generate_conduct_council_pdf(
    *, interval_number, students, conduct_records,
    details_by_student=None, teacher_names=(), class_name='a IX-a TH',
):
    """Returnează PDF în memorie; NU modifică sau transmite niciun registru."""
    details_by_student = details_by_student or {}
    interval, grades = _validate_inputs(
        interval_number, students, conduct_records, details_by_student
    )
    if not isinstance(teacher_names, (tuple, list)):
        raise ConductReportError('Lista profesorilor este invalidă.')
    teacher_names = [str(name).strip() for name in teacher_names if str(name).strip()]
    if len(teacher_names) > 40 or len(set(teacher_names)) != len(teacher_names):
        raise ConductReportError('Lista profesorilor este duplicată sau prea lungă.')

    font, bold = _font_names()
    styles = {
        'title': ParagraphStyle('PVTitle', fontName=bold, fontSize=13, leading=16, alignment=1, spaceAfter=10),
        'body': ParagraphStyle('PVBody', fontName=font, fontSize=8.1, leading=11.5, spaceAfter=7),
        'section': ParagraphStyle('PVSection', fontName=font, fontSize=9, leading=13, spaceBefore=6, spaceAfter=7),
        'cell': ParagraphStyle('PVCell', fontName=font, fontSize=7.1, leading=9),
        'small': ParagraphStyle('PVSmall', fontName=font, fontSize=6, leading=7.5),
        'bold': ParagraphStyle('PVBoldCell', fontName=bold, fontSize=7, leading=8.5),
        'footer': ParagraphStyle('PVFooter', fontName=font, fontSize=8, leading=12),
    }
    def p(txt, style='cell'):
        return Paragraph(_safe(txt), styles[style])

    start = interval.start_date.strftime('%d.%m.%Y')
    end = interval.end_date.strftime('%d.%m.%Y')
    period = f'{start} – {end}'
    report_date = end
    missing_notes = sum(str(item[3]).strip() not in grades for item in students)
    missing_reasons = sum(
        grades.get(str(item[3]).strip(), 10) < 10
        and not str(details_by_student.get(str(item[3]).strip(), {}).get('reason') or '').strip()
        for item in students
    )
    incomplete = bool(missing_notes or missing_reasons or not teacher_names)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=39 * mm, bottomMargin=14 * mm,
        title=f'PV Note la purtare — intervalul {interval_number} — {end}',
        author=SCHOOL_NAME, pageCompression=1,
    )
    story = [
        Paragraph('Proces-verbal', styles['title']),
        Paragraph(
            f'Încheiat la data de <b>{_safe(report_date)}</b>, pentru intervalul de cursuri '
            f'<b>{interval_number}</b> ({_safe(period)}), cu ocazia analizării notelor '
            f'la purtare propuse de dirigintele clasei {_safe(class_name)}, '
            f'prof. {_safe(DIRIGINTE)}. Membrii consiliului clasei au analizat '
            'situația fiecărui elev, după cum urmează:',
            styles['body']
        ),
    ]
    if incomplete:
        story.append(Paragraph(
            '<b>PROIECT — necesită verificarea rubricilor incomplete, '
            'validarea deciziilor și semnăturile membrilor consiliului.</b>',
            styles['body'],
        ))
    else:
        story.append(Paragraph(
            '<b>Document generat automat pentru verificare și semnare. '
            'Semnăturile și validările instituționale nu sunt generate automat.</b>',
            styles['body'],
        ))

    table_rows = [[p('Nr. crt.', 'bold'), p('Nume prenume elev', 'bold'),
                   p('Nota la purtare', 'bold'), p('Observații', 'bold')]]
    proposed_below_seven = []
    for index, item in enumerate(students, 1):
        key = str(item[3]).strip()
        grade = grades.get(key)
        notes = []
        detail = details_by_student.get(key, {})
        if grade is None:
            notes.append('Notă neacordată — de completat')
        elif grade < 10:
            reason = str(detail.get('reason') or '').strip()
            notes.append(f'Motiv (conform PV): {reason}' if reason else 'Motiv scădere: de verificat în PV')
            doc_id = str(detail.get('document_id') or '').strip()
            if doc_id:
                sent = _date_local(detail.get('sent_at_utc'))
                notice_num = str(detail.get('registration_number') or '').strip()
                notes.append(f'Înștiințare: {sent or "dată necunoscută"}'
                             + (f', nr. {notice_num}' if notice_num else f', ID {doc_id}'))
                confirmation_date = _date_local(detail.get('received_at_utc'))
                confirmation_id = str(detail.get('confirmation_id') or '').strip()
                if confirmation_date and confirmation_id:
                    notes.append(f'Confirmare prima accesare: {confirmation_date}, ID {confirmation_id}')
                elif confirmation_date:
                    notes.append(f'Prima accesare: {confirmation_date}; ID confirmare lipsă')
                else:
                    notes.append('Confirmarea primirii: neînregistrată')
            else:
                notes.append('Înștiințare asociată: neidentificată')
            if grade < 7:
                proposed_below_seven.append((item[1], grade, reason or 'De completat din PV'))
        table_rows.append([
            p(str(index)),
            p(str(item[1])),
            p(str(grade) if grade is not None else '—', 'bold'),
            p(' | '.join(notes), 'small') if notes else p(''),
        ])
    while len(table_rows) < 37:
        table_rows.append([p(''), p(''), p(''), p('')])
    t = Table(table_rows, colWidths=[10 * mm, 72 * mm, 22 * mm, 78 * mm], repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), .35, colors.HexColor('#364152')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9eef4')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story += [t, PageBreak()]
    story.append(Paragraph(
        'Se trimit spre validare Consiliului profesoral al Colegiului „Emil Negruțiu” '
        'Turda următoarele propuneri de note sub 7:',
        styles['section'],
    ))
    sanction_rows = [[p('Nr. crt.', 'bold'), p('Nume prenume elev', 'bold'),
                      p('Nota la purtare', 'bold'), p('Motivul sancțiunii', 'bold')]]
    for index, (name, grade, reason) in enumerate(proposed_below_seven, 1):
        sanction_rows.append([p(index), p(name), p(grade), p(reason)])
    while len(sanction_rows) < 5:
        sanction_rows.append([p(''), p(''), p(''), p('')])
    s_table = Table(sanction_rows, colWidths=[14*mm, 68*mm, 28*mm, 72*mm], repeatRows=1)
    s_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), .5, colors.HexColor('#354253')),
        ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#e9eef4')),
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    story += [s_table, Spacer(1, 12*mm),
              Paragraph(f'Colectivul profesoral al clasei {_safe(class_name)}',
                        styles['section'])]
    teacher_rows = [[p('Nr. crt.', 'bold'),p('Nume prenume profesor', 'bold'),p('Semnătura','bold')]]
    for index in range(max(15, len(teacher_names))):
        name = teacher_names[index] if index < len(teacher_names) else ''
        teacher_rows.append([p(str(index+1)),p(name),p('')])
    teacher_table = Table(teacher_rows, colWidths=[14*mm, 100*mm, 68*mm], repeatRows=1)
    teacher_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1), .5, colors.HexColor('#354253')),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef4')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    story += [teacher_table, Spacer(1, 10*mm),
              Paragraph('<b>Întocmit,</b>', styles['footer']),
              Paragraph(f'Diriginte: {_safe(DIRIGINTE)}', styles['footer']),
              Paragraph('Semnătura: ______________________', styles['footer'])]
    doc.build(story,
              onFirstPage=lambda c, d: _draw_header(c,d,font,bold),
              onLaterPages=lambda c, d: _draw_header(c,d,font,bold))
    return buffer.getvalue()
