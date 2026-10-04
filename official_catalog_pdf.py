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


# Harta fizică de lucru a tipizatului. None = rubrică existentă, dar necompletată.
# Geometria NU se comprimă atunci când o rubrică este goală.
CATALOG_P3_SLOTS = (
    "Limba și literatura română",
    None,  # Limba și literatura maternă – rubrică fizică neutilizată la IX TH
    "Limba modernă 1 – Limba engleză",
    "Limba modernă 2 – Limba franceză",
    None,  # Limba modernă 3 – rubrică fizică neutilizată la IX TH
    "Matematică",
    "Fizică",
    "Chimie",
    "Biologie",
    "Istorie",
    "Geografie",
)

CATALOG_P4_SLOTS = (
    "Logică, argumentare și comunicare",
    "Religie",
    "Educație vizuală",
    "Educație fizică și sport",
    "Tehnologia informației și a comunicațiilor (TIC)",
    "M1 – Bazele contabilității",
    "M2 – Etică și comunicare",
    "M3 – Structuri de primire turistică",
    "M4 – Procese și calitate în HoReCa",
    "M5 – CDEOȘ – Stagii de pregătire practică",
    "M6 – Curriculum pentru aprofundare și inserție profesională",
    None,
    None,
    None,
)


# Maparea de citire este separată de harta fizică. Cheile de mai jos sunt
# denumirile EXISTENTE în aplicație/Excel; None înseamnă că poziția fizică
# rămâne goală și nu se încearcă nicio citire.
CATALOG_P3_SOURCE_KEYS = (
    "Limba și literatura română",
    None,
    "Limba engleză (L1)",
    "Limba franceză (L2)",
    None,
    "Matematică",
    "Fizică",
    "Chimie",
    "Biologie",
    "Istorie",
    "Geografie",
)

CATALOG_P4_SOURCE_KEYS = (
    "Logică, argumentare și comunicare",
    "Religie",
    "Arte vizuale și educație plastică",
    "Educație fizică",
    "Informatică / TIC",
    "M1: Bazele contabilității",
    "M2: Etică și comunicare",
    "M3: Structuri de primire turistică",
    "M4: Procese și calitate în HoReCa",
    "M5: CDEOȘ (IP) - Instruire Practică",
    "M6: Curriculum de aprofundare și inserție profesională",
    None,
    None,
    None,
)


# Structura de coloane este aceeași cu aplicația existentă. Generatorul oficial
# doar citește aceste poziții; nu recalculează și nu scrie nimic în workbook.
CG_START_COLUMNS = {
    "Limba și literatura română": 8,
    "Limba engleză (L1)": 61,
    "Limba franceză (L2)": 114,
    "Matematică": 167,
    "Fizică": 220,
    "Chimie": 273,
    "Biologie": 326,
    "Istorie": 379,
    "Geografie": 432,
    "Logică, argumentare și comunicare": 485,
    "Informatică / TIC": 538,
    "Educație fizică": 591,
    "Religie": 644,
    "Arte vizuale și educație plastică": 697,
}

TH_START_COLUMNS = {
    "M1: Bazele contabilității": 8,
    "M2: Etică și comunicare": 61,
    "M3: Structuri de primire turistică": 114,
    "M4: Procese și calitate în HoReCa": 167,
    "M5: CDEOȘ (IP) - Instruire Practică": 220,
    "M6: Curriculum de aprofundare și inserție profesională": 273,
}


def _validate_physical_source_mapping() -> None:
    """Oprește generarea dacă harta fizică și sursele Excel se desincronizează."""
    for physical, sources, page in (
        (CATALOG_P3_SLOTS, CATALOG_P3_SOURCE_KEYS, "P3"),
        (CATALOG_P4_SLOTS, CATALOG_P4_SOURCE_KEYS, "P4"),
    ):
        if len(physical) != len(sources):
            raise OfficialCatalogError(f"Harta fizică și maparea surselor diferă ca lungime pe {page}.")
        for label, source_key in zip(physical, sources):
            if source_key is None:
                if label is not None:
                    raise OfficialCatalogError(
                        f"Rubrica {label!r} de pe {page} nu are o sursă Excel validată."
                    )
                continue
            if source_key not in OFFICIAL_SUBJECT_NAMES:
                raise OfficialCatalogError(
                    f"Sursa Excel {source_key!r} de pe {page} nu are denumire oficială mapată."
                )
            if OFFICIAL_SUBJECT_NAMES[source_key] != label:
                raise OfficialCatalogError(
                    f"Maparea {source_key!r} nu corespunde rubricii fizice {label!r} de pe {page}."
                )
            _source_location(source_key)


@dataclass(frozen=True)
class StudentIdentity:
    name: str
    nr_matr: str
    rm_pg: str
    row: int


@dataclass(frozen=True)
class GradeEntry:
    grade: object
    date: object


def _source_location(source_key: str) -> tuple[str, int]:
    if source_key in CG_START_COLUMNS:
        return "Cultură Generală", CG_START_COLUMNS[source_key]
    if source_key in TH_START_COLUMNS:
        return "Module Tehnologice", TH_START_COLUMNS[source_key]
    raise OfficialCatalogError(f"Nu există poziție Excel validată pentru {source_key!r}.")


def extract_grade_entries(wb, student: StudentIdentity, source_key: str) -> tuple[GradeEntry, ...]:
    """Citește cele 10 perechi Notă/Data exact ca aplicația existentă."""
    sheet_name, start_col = _source_location(source_key)
    ws = wb[sheet_name]
    entries: list[GradeEntry] = []
    for k in range(10):
        grade = ws.cell(row=student.row, column=start_col + k * 2).value
        date = ws.cell(row=student.row, column=start_col + k * 2 + 1).value
        if grade is not None and _norm(grade):
            entries.append(GradeEntry(grade=grade, date=date))
    return tuple(entries)


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
    ordered = sorted(resolved, key=lambda s: s.name.casefold())
    if len(ordered) > 39:
        raise OfficialCatalogError(
            "Tipizatul P3–P28 are 39 de poziții; lista validată conține mai mult de 39 de elevi."
        )
    return ordered


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
    """Geometrie P3/P4 apropiată de tipizatul oficial; datele școlare nu sunt încă populate."""
    width, height = A4
    left, right = 18, width - 16
    top, bottom = height - 47, 47
    header_h = 48
    gap = 5
    usable_h = top - bottom - header_h - 2 * gap
    block_h = usable_h / 3
    mean_h = 34
    identity_w = 132

    c.setLineWidth(0.65)

    if side == "stângă":
        grid_left = left + identity_w
        slots = CATALOG_P3_SLOTS
        pair_w = (right - grid_left) / len(slots)

        c.rect(left, top - header_h, identity_w, header_h)
        c.setFont(PDF_FONT_BOLD, 13)
        c.drawCentredString(left + identity_w / 2, top - 28, "ELEVII")
        c.rect(grid_left, top - header_h, right - grid_left, header_h)
        c.setFont(PDF_FONT_BOLD, 7.8)
        c.drawRightString(right - 4, top - 10, "DISCIPLINELE/MODULELE***  DE")
        c.line(grid_left, top - 27, right, top - 27)
        for j in range(len(slots)):
            gx = grid_left + j * pair_w
            c.line(gx, top - header_h, gx, top - 27)
            c.line(gx + pair_w / 2, top - header_h, gx + pair_w / 2, top - 27)
            c.setFont(PDF_FONT, 2.8)
            c.drawCentredString(gx + pair_w * .25, top - 38, "Absențe")
            c.drawCentredString(gx + pair_w * .75, top - 38, "Note")
        c.line(right, top - header_h, right, top - 27)
    else:
        slots = CATALOG_P4_SLOTS
        terminal_w = 76
        grid_right = right - terminal_w
        pair_w = (grid_right - left) / len(slots)

        c.rect(left, top - header_h, right - left, header_h)
        c.setFont(PDF_FONT_BOLD, 7.8)
        c.drawString(left + 16, top - 10, "ÎNVĂȚĂMÂNT")
        c.setFont(PDF_FONT_BOLD, 5.0)
        c.drawCentredString(grid_right + terminal_w * .72, top - 10, "ABSENȚE")
        c.line(left, top - 25, grid_right, top - 27)
        for j in range(len(slots)):
            gx = left + j * pair_w
            c.line(gx, top - header_h, gx, top - 27)
            c.line(gx + pair_w / 2, top - header_h, gx + pair_w / 2, top - 27)
            c.setFont(PDF_FONT, 2.8)
            c.drawCentredString(gx + pair_w * .25, top - 38, "Absențe")
            c.drawCentredString(gx + pair_w * .75, top - 38, "Note")
        c.line(grid_right, top - header_h, grid_right, top)

    for idx in range(3):
        y_top = top - header_h - idx * (block_h + gap)
        y_bottom = y_top - block_h

        if side == "stângă":
            grid_left = left + identity_w
            slots = CATALOG_P3_SLOTS
            pair_w = (right - grid_left) / len(slots)
            c.rect(left, y_bottom, right - left, block_h)
            c.line(grid_left, y_bottom, grid_left, y_top)

            student = students[idx] if idx < len(students) else None
            x = left + 5
            identity_right = grid_left - 4

            # Blocul de identificare reproduce numai rubricile tipizatului;
            # nu inventează stări școlare și nu completează câmpuri manuale.
            c.setFont(PDF_FONT_BOLD, 5.4)
            c.drawString(x, y_top - 14, student.name if student else "....................................................")
            c.setFont(PDF_FONT, 4.4)
            c.drawString(x, y_top - 28, "Prenumele tatălui (mamei) ........................")
            c.drawString(x, y_top - 41, "Data și locul nașterii ...............................")

            c.line(left, y_top - 51, grid_left, y_top - 51)
            c.setFont(PDF_FONT, 4.3)
            c.drawString(x, y_top - 63, "Nr. matricol")
            c.drawRightString(identity_right, y_top - 63, student.nr_matr if student else ".............")
            c.drawString(x, y_top - 76, "Registrul matricol: vol. .......... pag.")
            c.drawRightString(identity_right, y_top - 76, student.rm_pg if student else ".......")

            c.line(left, y_top - 86, grid_left, y_top - 86)
            c.setFont(PDF_FONT_BOLD, 4.8)
            c.drawCentredString((left + grid_left) / 2, y_top - 98, "SITUAȚIA ȘCOLARĂ")
            c.setFont(PDF_FONT, 4.2)
            c.drawString(x, y_top - 112, "La încheierea cursurilor .........................")
            c.drawString(x, y_top - 125, "La sfârșitul anului școlar .......................")
            c.drawString(x, y_top - 140, "Media generală ......................................")

            c.line(left, y_top - 150, grid_left, y_top - 150)
            c.setFont(PDF_FONT, 4.0)
            c.drawString(x, y_top - 162, "Mențiuni .................................................")
            c.drawString(x, y_top - 174, "............................................................")

            for j, slot in enumerate(slots):
                gx = grid_left + j * pair_w
                c.line(gx, y_bottom, gx, y_top)
                # Separarea Absențe/Note aparține numai corpului de înregistrare.
                # Zona mediilor rămâne o singură celulă pe lățimea disciplinei.
                c.line(gx + pair_w / 2, y_bottom + mean_h, gx + pair_w / 2, y_top)
                if slot:
                    c.saveState()
                    c.translate(gx + pair_w * .55, y_bottom + mean_h + 5)
                    c.rotate(90)
                    c.setFont(PDF_FONT, 3.0)
                    c.drawString(0, 0, slot)
                    c.restoreState()
            c.line(right, y_bottom, right, y_top)

            # Cele trei rânduri de medii traversează rubricile disciplinelor,
            # fără subdiviziunea verticală Absențe/Note.
            mean_row_h = mean_h / 3
            for k in range(1, 3):
                yy = y_bottom + k * mean_row_h
                c.line(grid_left, yy, right, yy)

            # Etichetele apar în zona de situație școlară, nu într-o
            # pseudo-coloană de disciplină.
            c.setFont(PDF_FONT, 3.5)
            label_x = left + identity_w - 48
            c.drawRightString(label_x, y_bottom + 2 * mean_row_h + 2, "Media")
            c.drawRightString(label_x, y_bottom + mean_row_h + 2, "Media la ex. de corig.")
            c.drawRightString(label_x, y_bottom + 2, "Media anuală")
        else:
            slots = CATALOG_P4_SLOTS
            terminal_w = 76
            grid_right = right - terminal_w
            pair_w = (grid_right - left) / len(slots)
            c.rect(left, y_bottom, right - left, block_h)

            for j, slot in enumerate(slots):
                gx = left + j * pair_w
                c.line(gx, y_bottom, gx, y_top)
                # Separarea Absențe/Note aparține numai corpului de înregistrare.
                # Zona mediilor rămâne o singură celulă pe lățimea disciplinei.
                c.line(gx + pair_w / 2, y_bottom + mean_h, gx + pair_w / 2, y_top)
                if slot:
                    c.saveState()
                    c.translate(gx + pair_w * .55, y_bottom + mean_h + 5)
                    c.rotate(90)
                    c.setFont(PDF_FONT, 2.9)
                    c.drawString(0, 0, slot)
                    c.restoreState()
            c.line(grid_right, y_bottom, grid_right, y_top)

            conduct_w = 32
            total_w = 22
            unmotiv_w = terminal_w - conduct_w - total_w
            x_conduct = grid_right
            x_total = x_conduct + conduct_w
            x_unmotiv = x_total + total_w
            c.line(x_total, y_bottom, x_total, y_top)
            c.line(x_unmotiv, y_bottom, x_unmotiv, y_top)

            # Geometria specială a tipizatului: Consiliere/orientare sus, Purtare jos,
            # diagonală în corpul coloanei și celula de medie barată cu X.
            conduct_split_y = y_top - 26
            c.line(x_conduct, conduct_split_y, x_total, conduct_split_y)
            c.setFont(PDF_FONT, 3.2)
            c.drawCentredString((x_conduct + x_total) / 2, y_top - 9, "Consiliere")
            c.drawCentredString((x_conduct + x_total) / 2, y_top - 16, "și orientare")
            c.setFont(PDF_FONT_BOLD, 3.6)
            c.drawCentredString((x_conduct + x_total) / 2, y_top - 38, "PURTARE")
            c.line(x_conduct, y_bottom + mean_h, x_total, conduct_split_y)

            c.saveState()
            c.translate(x_total + total_w * .55, y_top - 38)
            c.rotate(90)
            c.setFont(PDF_FONT_BOLD, 4.0)
            c.drawString(0, 0, "TOTAL")
            c.restoreState()
            c.saveState()
            c.translate(x_unmotiv + unmotiv_w * .55, y_top - 58)
            c.rotate(90)
            c.setFont(PDF_FONT_BOLD, 3.3)
            c.drawString(0, 0, "din care nemotivate")
            c.restoreState()

            # Rândurile de medii continuă prin cele 14 rubrici; blocul
            # terminal își păstrează propria geometrie oficială.
            mean_row_h = mean_h / 3
            for k in range(1, 3):
                yy = y_bottom + k * mean_row_h
                c.line(left, yy, grid_right, yy)
                c.line(x_conduct, yy, right, yy)

            # X-ul tipărit în celula mediană a rubricii Purtare.
            x1, x2 = x_conduct, x_total
            yy1, yy2 = y_bottom + mean_row_h, y_bottom + 2 * mean_row_h
            c.line(x1, yy1, x2, yy2)
            c.line(x1, yy2, x2, yy1)

    if side == "stângă":
        c.setFont(PDF_FONT, 4.2)
        c.drawString(
            left,
            bottom - 12,
            "***) Disciplinele/modulele de învățământ se înscriu în ordinea Planului-cadru, cu denumirile complete.",
        )

def generate_official_catalog_prototype(
    excel_path: str,
    gest_data: Sequence[Mapping],
) -> bytes:
    """Generează prototipul PDF exclusiv prin citire.

    Nu apelează save(), nu scrie fișiere și nu sincronizează repository-uri.
    """
    _register_unicode_fonts()
    _validate_physical_source_mapping()
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
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

        # P3–P28: 13 deschideri consecutive, exact 3 poziții fizice/deschidere.
        # Felierea păstrează ordinea alfabetică validată; dacă o grupă are sub
        # 3 elevi, _draw_marks_spread_placeholder() lasă pozițiile rămase goale.
        for spread_index in range(13):
            start_pos = spread_index * 3
            group = students[start_pos : start_pos + 3]
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
