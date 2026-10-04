"""Prototip izolat pentru catalogul oficial al clasei IX TH.

ETAPA 5.5:
- modul strict read-only;
- nu salvează workbook-ul;
- nu sincronizează GitHub;
- nu modifică registre sau gestiune_elevi.json;
- oprește generarea dacă identitatea elevilor nu este coerentă.

Integrarea în Streamlit se face numai într-o etapă ulterioară, după validarea
vizuală și funcțională a prototipului.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import openpyxl
import fontpkg
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


REQUIRED_SHEETS = (
    "Cultură Generală",
    "Module Tehnologice",
    "Absențe & Purtare",
    "Centralizator Medii",
)

CATALOG_CONFIG = {
    "unitate": "Colegiul „Emil Negruțiu” Turda",
    "clasa": "a IX-a TH",
    "an_scolar": "2026–2027",
    "filiera": "Tehnologică",
    "profil": "Servicii",
    "domeniu": "Turism și alimentație",
    "calificare": "Tehnician în turism / Lucrător hotelier",
    "director": "Gavrilescu Timea Karola",
    "diriginte": "Prof. Ec. Gherman Octavian-Theodor",
}

# Cheia este denumirea internă din aplicație/Excel. Valoarea este denumirea
# afișată în catalogul oficial. Nu se redenumește nicio coloană din Excel.
OFFICIAL_SUBJECT_NAMES = {
    "Limba și literatura română": "Limba și literatura română",
    "Limba engleză (L1)": "Limba modernă 1 – Limba engleză",
    "Limba franceză (L2)": "Limba modernă 2 – Limba franceză",
    "Matematică": "Matematică",
    "Fizică": "Fizică",
    "Chimie": "Chimie",
    "Biologie": "Biologie",
    "Istorie": "Istorie",
    "Geografie": "Geografie",
    "Logică, argumentare și comunicare": "Logică, argumentare și comunicare",
    "Informatică / TIC": "Tehnologia informației și a comunicațiilor (TIC)",
    "Educație fizică": "Educație fizică și sport",
    "Religie": "Religie",
    "Arte vizuale și educație plastică": "Educație vizuală",
    "M1: Bazele contabilității": "M1 – Bazele contabilității",
    "M2: Etică și comunicare": "M2 – Etică și comunicare",
    "M3: Structuri de primire turistică": "M3 – Structuri de primire turistică",
    "M4: Procese și calitate în HoReCa": "M4 – Procese și calitate în HoReCa",
    "M5: CDEOȘ (IP) - Instruire Practică": "M5 – CDEOȘ – Stagii de pregătire practică",
    "M6: Curriculum de aprofundare și inserție profesională": (
        "M6 – Curriculum pentru aprofundare și inserție profesională"
    ),
}

PROFESSORS = {
    "Limba și literatura română": "FEKETE IOANA",
    "Limba modernă 1 – Limba engleză": "HÂLMĂ ALEXANDRA",
    "Limba modernă 2 – Limba franceză": "FELHAZI CARMEN",
    "Matematică": "CRĂCIUN ALEXANDRA",
    "Fizică": "DOMOKOȘ IOAN",
    "Chimie": "TĂMAȘ LIANA",
    "Biologie": "IANCU CLAUDIA",
    "Istorie": "VICENȚIA VOMIR",
    "Geografie": "POPA RAREȘ",
    "Logică, argumentare și comunicare": "MUNCACIU RADU",
    "Tehnologia informației și a comunicațiilor (TIC)": "CĂTANĂ MONICA",
    "Educație fizică și sport": "BĂL OLIMPIU",
    "Religie": "SOAMEȘ DĂNILĂ",
    "Educație vizuală": "MOLDOVAN HORAȚIU",
    "M1 – Bazele contabilității": "GHERMAN OCTAVIAN",
    "M2 – Etică și comunicare": "FRUNZĂREANU MIHAELA",
    "M3 – Structuri de primire turistică": "LECHINȚAN COSMIN",
    "M4 – Procese și calitate în HoReCa": "FRĂSILĂ BRIGITA",
    "M5 – CDEOȘ – Stagii de pregătire practică": "LECHINȚAN COSMIN",
    "M6 – Curriculum pentru aprofundare și inserție profesională": "LECHINȚAN COSMIN",
}


@dataclass(frozen=True)
class StudentIdentity:
    name: str
    nr_matr: str
    rm_pg: str
    row: int


PDF_FONT = "OfficialCatalogNoto"
PDF_FONT_BOLD = "OfficialCatalogNotoBold"


def _register_unicode_fonts() -> None:
    """Înregistrează fonturi Unicode; oprește generarea dacă lipsesc."""
    try:
        font_path = str(fontpkg.path("Noto Sans"))
        if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(PDF_FONT, font_path))
        if PDF_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, font_path))
    except Exception as ex:
        raise OfficialCatalogError("Fontul Unicode necesar catalogului nu este disponibil.") from ex


class OfficialCatalogError(RuntimeError):
    """Eroare fail-closed a generatorului catalogului oficial."""


def _norm(value) -> str:
    return " ".join(str(value or "").split())


def _student_from_gestiune(row: Mapping) -> tuple[str, str, str]:
    name = _norm(
        row.get("nume_complet")
        or f"{row.get('nume', '')} {row.get('initiala', '')} {row.get('prenume', '')}"
    )
    nr_matr = _norm(row.get("rand_excel"))
    rm_pg = _norm(row.get("matricol"))
    if not name or not nr_matr or not rm_pg:
        raise OfficialCatalogError("Există un elev cu identitate structurală incompletă.")
    return name, nr_matr, rm_pg


def validate_and_resolve_students(wb, gest_data: Sequence[Mapping]) -> list[StudentIdentity]:
    """Validează identitatea în toate foile și returnează rândurile sigure.

    Funcția nu modifică workbook-ul.
    """
    for sheet_name in REQUIRED_SHEETS:
        if sheet_name not in wb.sheetnames:
            raise OfficialCatalogError(f"Lipsește foaia obligatorie: {sheet_name}")

    if not isinstance(gest_data, Sequence) or isinstance(gest_data, (str, bytes)) or not gest_data:
        raise OfficialCatalogError("Datele elevilor sunt goale sau invalide.")

    seen_nr: set[str] = set()
    seen_rm: set[str] = set()
    resolved: list[StudentIdentity] = []

    for item in gest_data:
        name, nr_matr, rm_pg = _student_from_gestiune(item)
        rm_key = rm_pg.casefold()
        if nr_matr in seen_nr or rm_key in seen_rm:
            raise OfficialCatalogError("NR. MATR. sau RM/PG nu este unic în datele elevilor.")
        seen_nr.add(nr_matr)
        seen_rm.add(rm_key)

        rows: list[int] = []
        for sheet_name in REQUIRED_SHEETS:
            ws = wb[sheet_name]
            matches = [
                r for r in range(9, ws.max_row + 1)
                if _norm(ws.cell(r, 4).value).casefold() == rm_key
            ]
            if len(matches) != 1:
                raise OfficialCatalogError(f"RM/PG {rm_pg} nu este unic în {sheet_name}.")
            r = matches[0]
            if _norm(ws.cell(r, 2).value) != name or _norm(ws.cell(r, 3).value) != nr_matr:
                raise OfficialCatalogError(f"Identitatea cu RM/PG {rm_pg} diferă în {sheet_name}.")
            rows.append(r)

        if len(set(rows)) != 1:
            raise OfficialCatalogError(f"RM/PG {rm_pg} nu este pe același rând în toate foile.")
        resolved.append(StudentIdentity(name, nr_matr, rm_pg, rows[0]))

    # Catalogul oficial se prezintă alfabetic, fără a altera ordinea din Excel.
    return sorted(resolved, key=lambda s: s.name.casefold())


def _draw_page_frame(c: canvas.Canvas, page_no: int, title: str) -> None:
    width, height = A4
    c.setLineWidth(0.6)
    c.rect(24, 24, width - 48, height - 48)
    c.setFont(PDF_FONT_BOLD, 10)
    c.drawCentredString(width / 2, height - 42, title)
    c.setFont(PDF_FONT, 7)
    c.drawRightString(width - 30, 30, f"Pagina {page_no}")


def _draw_prototype_notice(c: canvas.Canvas) -> None:
    c.setFont(PDF_FONT_BOLD, 7)
    c.drawString(30, 30, "PROTOTIP ETAPA 5.5 – NU REPREZINTĂ CATALOG ÎNCHEIAT")


def _fit_text(c: canvas.Canvas, text: str, max_width: float, font: str, size: float, min_size: float = 5.0) -> float:
    """Micșorează numai cât este necesar; nu trunchiază denumirile oficiale."""
    current = size
    while current > min_size and pdfmetrics.stringWidth(text, font, current) > max_width:
        current -= 0.2
    if pdfmetrics.stringWidth(text, font, current) > max_width:
        raise OfficialCatalogError(f"Textul nu încape în rubrica oficială: {text}")
    return current


def _draw_labeled_line(c: canvas.Canvas, label: str, value: str, y: float, x: float = 178, end_x: float = 442) -> None:
    c.setFont(PDF_FONT, 8.2)
    c.drawString(x, y, label)
    line_x = x + pdfmetrics.stringWidth(label, PDF_FONT, 8.2) + 5
    c.line(line_x, y - 1, end_x, y - 1)
    size = _fit_text(c, value, end_x - line_x - 6, PDF_FONT_BOLD, 8.2)
    c.setFont(PDF_FONT_BOLD, size)
    c.drawCentredString((line_x + end_x) / 2, y + 1, value)


def _draw_admin_page(c: canvas.Canvas) -> None:
    """Pagina 2, construită după geometria tipizatului oficial."""
    width, height = A4

    c.setFont(PDF_FONT_BOLD, 23)
    c.drawCentredString(width / 2, height - 58, "MINISTERUL EDUCAȚIEI*")

    c.setLineWidth(1.4)
    c.line(34, height - 75, width - 34, height - 75)
    c.setFont(PDF_FONT_BOLD, 8.5)
    c.drawCentredString(width / 2, height - 69, CATALOG_CONFIG["unitate"])
    c.setFont(PDF_FONT, 6.5)
    c.drawCentredString(width / 2, height - 84, "(Unitatea de învățământ)")

    locality = "Turda, județul Cluj"
    c.setLineWidth(0.7)
    c.line(145, height - 108, width - 145, height - 108)
    c.setFont(PDF_FONT_BOLD, 8.2)
    c.drawCentredString(width / 2, height - 104, locality)
    c.setFont(PDF_FONT, 6.5)
    c.drawCentredString(width / 2, height - 121, "(Localitatea și județul)")

    c.setFont(PDF_FONT, 22)
    c.drawString(140, height - 159, "Catalogul clasei")
    c.setFont(PDF_FONT_BOLD, 16)
    c.drawString(360, height - 158, CATALOG_CONFIG["clasa"])
    c.line(355, height - 162, 445, height - 162)
    c.setFont(PDF_FONT, 7.5)
    c.drawCentredString(width / 2, height - 178, "(Învățământ liceal)")

    _draw_labeled_line(c, "Filiera", CATALOG_CONFIG["filiera"], height - 203)
    _draw_labeled_line(c, "Profilul", CATALOG_CONFIG["profil"], height - 222)
    _draw_labeled_line(
        c,
        "Domeniul pregătirii de bază** (Clasa a IX-a și a X-a)",
        CATALOG_CONFIG["domeniu"],
        height - 241,
    )
    _draw_labeled_line(
        c,
        "Specializarea/Calificarea profesională**",
        CATALOG_CONFIG["calificare"],
        height - 260,
    )

    c.setFont(PDF_FONT, 16)
    c.drawString(194, height - 290, "Anul școlar")
    c.line(302, height - 293, 405, height - 293)
    c.setFont(PDF_FONT_BOLD, 11)
    c.drawCentredString(353, height - 289, CATALOG_CONFIG["an_scolar"])

    c.setFont(PDF_FONT_BOLD, 10)
    c.drawString(96, height - 333, "DIRECTOR,")
    c.drawString(410, height - 333, "DIRIGINTE,")
    c.setFont(PDF_FONT, 8)
    c.drawString(96, height - 350, CATALOG_CONFIG["director"])
    c.drawRightString(width - 58, height - 350, CATALOG_CONFIG["diriginte"])
    c.drawString(96, height - 369, "L.S.")

    c.setFont(PDF_FONT_BOLD, 12)
    c.drawCentredString(width / 2, height - 397, "PROFESORI")

    left = 34
    right = width - 34
    top = height - 407
    bottom = 117
    mid = width / 2
    col_x = [left, 143, mid, mid + 109, right]
    header_h = 24
    row_h = (top - bottom - header_h) / 10

    c.setLineWidth(0.8)
    c.rect(left, bottom, right - left, top - bottom)
    for x in col_x[1:-1]:
        c.line(x, bottom, x, top)
    c.line(left, top - header_h, right, top - header_h)
    for i in range(1, 10):
        y = top - header_h - i * row_h
        c.line(left, y, right, y)

    c.setFont(PDF_FONT_BOLD, 6.7)
    headers = ("DISCIPLINA/MODUL", "PROFESOR", "DISCIPLINA/MODUL", "PROFESOR")
    for i, header in enumerate(headers):
        c.drawCentredString((col_x[i] + col_x[i + 1]) / 2, top - 15, header)

    entries = list(PROFESSORS.items())
    c.setFont(PDF_FONT, 5.5)
    for row in range(10):
        y = top - header_h - (row + 0.67) * row_h
        for side, entry_index in ((0, row), (2, row + 10)):
            subject, professor = entries[entry_index]
            subject_size = _fit_text(c, subject, col_x[side + 1] - col_x[side] - 6, PDF_FONT, 5.5, 4.0)
            professor_size = _fit_text(c, professor, col_x[side + 2] - col_x[side + 1] - 6, PDF_FONT, 5.5, 4.0)
            c.setFont(PDF_FONT, subject_size)
            c.drawString(col_x[side] + 3, y, subject)
            c.setFont(PDF_FONT, professor_size)
            c.drawString(col_x[side + 1] + 3, y, professor)

    c.setFont(PDF_FONT, 5.7)
    c.drawString(34, 101, "*) denumirea curentă a ministerului")
    c.drawString(34, 92, "**) se completează pentru filierea tehnologică")

def _draw_students_grid(c: canvas.Canvas, students: Sequence[StudentIdentity], page_no: int) -> None:
    width, height = A4
    left, right = 32, width - 32
    top, bottom = height - 72, 55
    rows = 35
    row_h = (top - bottom) / (rows + 1)
    cols = [left, left + 24, left + 245, left + 315, right]

    c.setFont(PDF_FONT_BOLD, 6.5)
    headers = ("Nr.", "Numele și prenumele", "Nr. matr.", "RM/PG")
    for i, text in enumerate(headers):
        c.drawCentredString((cols[i] + cols[i + 1]) / 2, top - row_h + 4, text)

    c.setLineWidth(0.35)
    for x in cols:
        c.line(x, bottom, x, top)
    for r in range(rows + 2):
        y = top - r * row_h
        c.line(left, y, right, y)

    c.setFont(PDF_FONT, 6.2)
    for idx in range(rows):
        y = top - (idx + 2) * row_h + 4
        c.drawCentredString((cols[0] + cols[1]) / 2, y, str(idx + 1))
        if idx < len(students):
            s = students[idx]
            c.drawString(cols[1] + 3, y, s.name[:50])
            c.drawCentredString((cols[2] + cols[3]) / 2, y, s.nr_matr)
            c.drawCentredString((cols[3] + cols[4]) / 2, y, s.rm_pg)


def _draw_marks_spread_placeholder(c: canvas.Canvas, students: Sequence[StudentIdentity], side: str) -> None:
    """Geometrie prototip pentru o deschidere oficială de 3 elevi.

    Rubricile sunt desenate după structura tipizatului; conectarea notelor,
    absențelor și mediilor se face numai după validarea vizuală a geometriei.
    """
    width, height = A4
    left, right = 30, width - 20
    top, bottom = height - 62, 54
    block_h = (top - bottom) / 3
    identity_w = 142

    c.setLineWidth(0.55)
    c.setFont(PDF_FONT_BOLD, 7.2)
    c.drawString(left, top + 12, "SITUAȚIA ȘCOLARĂ – DESCHIDERE MODEL")

    for idx in range(3):
        y_top = top - idx * block_h
        y_bottom = y_top - block_h
        c.rect(left, y_bottom, right - left, block_h)

        if side == "stângă":
            c.line(left + identity_w, y_bottom, left + identity_w, y_top)
            student = students[idx] if idx < len(students) else None
            x = left + 5
            c.setFont(PDF_FONT_BOLD, 5.8)
            c.drawString(x, y_top - 13, student.name if student else f"Elev {idx + 1}")
            c.setFont(PDF_FONT, 4.8)
            c.drawString(x, y_top - 27, f"Nr. matricol: {student.nr_matr if student else '........'}")
            c.drawString(x, y_top - 39, f"Registrul matricol: {student.rm_pg if student else '........'}")
            c.drawString(x, y_top - 57, "Situația la încheierea cursurilor: ................")
            c.drawString(x, y_top - 69, "Situația la finalul anului școlar: .................")
            c.drawString(x, y_top - 81, "Media generală: ....................................")
            c.drawString(x, y_top - 98, "Mențiuni: ..........................................")

            grid_left = left + identity_w
            pair_count = 10
            pair_w = (right - grid_left) / pair_count
            for j in range(pair_count + 1):
                gx = grid_left + j * pair_w
                c.line(gx, y_bottom, gx, y_top)
                if j < pair_count:
                    c.line(gx + pair_w / 2, y_bottom + 28, gx + pair_w / 2, y_top)
                    c.setFont(PDF_FONT, 3.2)
                    c.drawCentredString(gx + pair_w * .25, y_top - 10, "Abs.")
                    c.drawCentredString(gx + pair_w * .75, y_top - 10, "Note")
            for k, label in enumerate(("Media", "Media la ex. de corig.", "Media anuală")):
                yy = y_bottom + (k + 1) * (28 / 3)
                c.line(grid_left, yy, right, yy)
                c.setFont(PDF_FONT, 3.1)
                c.drawString(grid_left + 2, yy + 1, label)
        else:
            terminal_w = 72
            grid_right = right - terminal_w
            pair_count = 13
            pair_w = (grid_right - left) / pair_count
            for j in range(pair_count + 1):
                gx = left + j * pair_w
                c.line(gx, y_bottom, gx, y_top)
                if j < pair_count:
                    c.line(gx + pair_w / 2, y_bottom + 28, gx + pair_w / 2, y_top)
                    c.setFont(PDF_FONT, 3.2)
                    c.drawCentredString(gx + pair_w * .25, y_top - 10, "Abs.")
                    c.drawCentredString(gx + pair_w * .75, y_top - 10, "Note")
            c.line(grid_right, y_bottom, grid_right, y_top)
            c.line(grid_right + 30, y_bottom, grid_right + 30, y_top)
            c.line(grid_right + 48, y_bottom, grid_right + 48, y_top)
            c.setFont(PDF_FONT, 3.8)
            c.drawCentredString(grid_right + 15, y_top - 12, "Consiliere")
            c.drawCentredString(grid_right + 15, y_top - 20, "și orientare")
            c.drawCentredString(grid_right + 15, y_top - 32, "Purtare")
            c.saveState()
            c.translate(grid_right + 39, y_bottom + 12)
            c.rotate(90)
            c.drawString(0, 0, "TOTAL ABSENȚE")
            c.restoreState()
            c.saveState()
            c.translate(grid_right + 58, y_bottom + 12)
            c.rotate(90)
            c.drawString(0, 0, "NEMOTIVATE")
            c.restoreState()
            for k in range(1, 4):
                c.line(left, y_bottom + k * (28 / 3), right, y_bottom + k * (28 / 3))

    if side == "stângă":
        c.setFont(PDF_FONT, 4.5)
        c.drawString(left, bottom - 10, "Disciplinele/modulele se înscriu cu denumirile complete, în ordinea planului-cadru.")

def generate_official_catalog_prototype(
    excel_path: str,
    gest_data: Sequence[Mapping],
) -> bytes:
    """Generează prototipul PDF exclusiv prin citire.

    Nu apelează save(), nu scrie fișiere și nu sincronizează repository-uri.
    """
    _register_unicode_fonts()\n    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    try:
        students = validate_and_resolve_students(wb, gest_data)

        out = io.BytesIO()
        c = canvas.Canvas(out, pagesize=A4, pageCompression=1, invariant=1)

        # P1: datele clasei/unității și cadrele didactice.
        _draw_page_frame(c, 1, "Date de identificare și cadre didactice")
        _draw_admin_page(c)
        _draw_prototype_notice(c)
        c.showPage()

        # P2: normele din tipizatul oficial.
        _draw_page_frame(c, 2, "NORME pentru completarea și utilizarea catalogului clasei")
        _draw_prototype_notice(c)
        c.setFont(PDF_FONT, 8)
        c.drawString(42, A4[1] - 85, "Pagina rezervată reproducerii fidele a normelor din tipizatul oficial.")
        c.showPage()

        # P3–P28: 13 deschideri consecutive, câte 3 poziții de elevi/deschidere.
        for spread_index in range(13):
            group = students[spread_index * 3 : spread_index * 3 + 3]
            left_page = 3 + spread_index * 2
            right_page = left_page + 1

            _draw_page_frame(c, left_page, "Situația școlară – corp catalog")
            _draw_marks_spread_placeholder(c, group, "stângă")
            _draw_prototype_notice(c)
            c.showPage()

            _draw_page_frame(c, right_page, "Situația școlară – corp catalog")
            _draw_marks_spread_placeholder(c, group, "dreaptă")
            _draw_prototype_notice(c)
            c.showPage()

        # P29: date personale – 35 poziții conform planșei oficiale.
        _draw_page_frame(c, 29, "DATE PERSONALE ALE ELEVILOR")
        _draw_students_grid(c, students, 29)
        _draw_prototype_notice(c)
        c.showPage()

        # P30: statistica anuală; fără inferențe administrative.
        _draw_page_frame(c, 30, "Situația generală asupra mișcării și frecvenței elevilor și a rezultatelor obținute")
        _draw_prototype_notice(c)
        c.setFont(PDF_FONT, 8)
        c.drawString(42, A4[1] - 85, "Rubricile statistice vor fi populate numai din surse validate.")
        c.showPage()

        # P31: ultima pagină utilizată – proces-verbal.
        _draw_page_frame(c, 31, "PROCES-VERBAL")
        _draw_prototype_notice(c)
        c.setFont(PDF_FONT, 8)
        c.drawString(42, A4[1] - 85, "Semnăturile și constatările administrative rămân necompletate automat.")
        c.showPage()

        # P32: verso-ul ultimei file este intenționat complet alb.
        c.showPage()

        c.save()
        return out.getvalue()
    finally:
        wb.close()


def assert_read_only_contract() -> bool:
    """Contract verificabil simplu pentru auditul prototipului."""
    forbidden_names = {
        "save",
        "push_to_github",
        "update_excel_computed_values",
        "save_gestiune_data",
    }
    names = set(generate_official_catalog_prototype.__code__.co_names)
    if names & forbidden_names:
        raise OfficialCatalogError("Generatorul încalcă contractul read-only.")
    return True
