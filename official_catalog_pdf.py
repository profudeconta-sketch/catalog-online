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
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


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
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 42, title)
    c.setFont("Helvetica", 7)
    c.drawRightString(width - 30, 30, f"Pagina {page_no}")


def _draw_prototype_notice(c: canvas.Canvas) -> None:
    c.setFont("Helvetica-Bold", 7)
    c.drawString(30, 30, "PROTOTIP ETAPA 5.5 – NU REPREZINTĂ CATALOG ÎNCHEIAT")


def _draw_admin_page(c: canvas.Canvas) -> None:
    width, height = A4
    y = height - 78
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "CATALOG – ÎNVĂȚĂMÂNT LICEAL")
    y -= 30
    c.setFont("Helvetica", 9)
    for label, key in (
        ("Unitatea de învățământ", "unitate"),
        ("Clasa", "clasa"),
        ("An școlar", "an_scolar"),
        ("Filiera", "filiera"),
        ("Profilul", "profil"),
        ("Domeniul pregătirii de bază", "domeniu"),
        ("Specializarea/Calificarea profesională", "calificare"),
        ("Director", "director"),
        ("Diriginte", "diriginte"),
    ):
        c.drawString(42, y, f"{label}:")
        c.drawString(220, y, str(CATALOG_CONFIG[key]))
        y -= 17

    y -= 10
    c.setFont("Helvetica-Bold", 8)
    c.drawString(42, y, "DISCIPLINĂ / MODUL")
    c.drawString(340, y, "CADRU DIDACTIC")
    y -= 13
    c.setFont("Helvetica", 6.5)
    for subject, professor in PROFESSORS.items():
        c.drawString(42, y, subject[:75])
        c.drawString(340, y, professor)
        y -= 12


def _draw_students_grid(c: canvas.Canvas, students: Sequence[StudentIdentity], page_no: int) -> None:
    width, height = A4
    left, right = 32, width - 32
    top, bottom = height - 72, 55
    rows = 35
    row_h = (top - bottom) / (rows + 1)
    cols = [left, left + 24, left + 245, left + 315, right]

    c.setFont("Helvetica-Bold", 6.5)
    headers = ("Nr.", "Numele și prenumele", "Nr. matr.", "RM/PG")
    for i, text in enumerate(headers):
        c.drawCentredString((cols[i] + cols[i + 1]) / 2, top - row_h + 4, text)

    c.setLineWidth(0.35)
    for x in cols:
        c.line(x, bottom, x, top)
    for r in range(rows + 2):
        y = top - r * row_h
        c.line(left, y, right, y)

    c.setFont("Helvetica", 6.2)
    for idx in range(rows):
        y = top - (idx + 2) * row_h + 4
        c.drawCentredString((cols[0] + cols[1]) / 2, y, str(idx + 1))
        if idx < len(students):
            s = students[idx]
            c.drawString(cols[1] + 3, y, s.name[:50])
            c.drawCentredString((cols[2] + cols[3]) / 2, y, s.nr_matr)
            c.drawCentredString((cols[3] + cols[4]) / 2, y, s.rm_pg)


def _draw_marks_spread_placeholder(c: canvas.Canvas, students: Sequence[StudentIdentity], side: str) -> None:
    """Schelet geometric pentru paginile 3–4.

    În 5.5 nu se inventează încă geometria finală a rubricilor Note/Absențe.
    Scopul este validarea fluxului read-only și a continuității paginilor.
    """
    width, height = A4
    left, right = 28, width - 28
    top, bottom = height - 70, 55
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left, top + 8, f"Corp catalog – jumătatea {side}")
    c.setLineWidth(0.35)
    c.rect(left, bottom, right - left, top - bottom)

    subject_names = list(PROFESSORS)
    half = (len(subject_names) + 1) // 2
    subset = subject_names[:half] if side == "stângă" else subject_names[half:]
    col_w = (right - left - 125) / max(1, len(subset))
    c.line(left + 125, bottom, left + 125, top)
    c.setFont("Helvetica", 5)
    for i, subject in enumerate(subset):
        x = left + 125 + i * col_w
        c.line(x, bottom, x, top)
        c.saveState()
        c.translate(x + col_w / 2, top - 4)
        c.rotate(90)
        c.drawRightString(0, 0, subject[:55])
        c.restoreState()
    c.line(right, bottom, right, top)

    usable_top = top - 120
    row_h = (usable_top - bottom) / max(35, 1)
    c.line(left, usable_top, right, usable_top)
    c.setFont("Helvetica", 5.5)
    for idx in range(35):
        y = usable_top - idx * row_h
        c.line(left, y, right, y)
        if idx < len(students):
            c.drawString(left + 3, y - row_h + 2, students[idx].name[:28])


def generate_official_catalog_prototype(
    excel_path: str,
    gest_data: Sequence[Mapping],
) -> bytes:
    """Generează prototipul PDF exclusiv prin citire.

    Nu apelează save(), nu scrie fișiere și nu sincronizează repository-uri.
    """
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    try:
        students = validate_and_resolve_students(wb, gest_data)

        out = io.BytesIO()
        c = canvas.Canvas(out, pagesize=A4, pageCompression=1, invariant=1)

        _draw_page_frame(c, 1, "Instrucțiuni / norme – structură prototip")
        _draw_prototype_notice(c)
        c.setFont("Helvetica", 8)
        c.drawString(42, A4[1] - 85, "Conținutul normativ exact va fi reprodus numai după validarea finală a tipizatului.")
        c.showPage()

        _draw_page_frame(c, 2, "Date de identificare și cadre didactice")
        _draw_admin_page(c)
        _draw_prototype_notice(c)
        c.showPage()

        _draw_page_frame(c, 3, "Situația școlară – corp catalog")
        _draw_marks_spread_placeholder(c, students, "stângă")
        _draw_prototype_notice(c)
        c.showPage()

        _draw_page_frame(c, 4, "Situația școlară – corp catalog")
        _draw_marks_spread_placeholder(c, students, "dreaptă")
        _draw_prototype_notice(c)
        c.showPage()

        _draw_page_frame(c, 5, "Situația generală a clasei – structură prototip")
        _draw_prototype_notice(c)
        c.setFont("Helvetica", 8)
        c.drawString(42, A4[1] - 85, "Rubricile administrative finale nu sunt deduse automat în prototip.")
        c.showPage()

        _draw_page_frame(c, 6, "Date personale ale elevilor")
        _draw_students_grid(c, students, 6)
        _draw_prototype_notice(c)
        c.showPage()

        _draw_page_frame(c, 7, "Mențiuni / încheiere – structură prototip")
        _draw_prototype_notice(c)
        c.setFont("Helvetica", 8)
        c.drawString(42, A4[1] - 85, "Semnăturile și constatările administrative nu sunt generate automat.")
        c.showPage()

        _draw_page_frame(c, 8, "Pagină tehnică – rezervată validării tipizatului")
        _draw_prototype_notice(c)
        c.setFont("Helvetica", 8)
        c.drawString(42, A4[1] - 85, "Această pagină rămâne intenționat neutră până la verificarea finală a structurii PDF oficial.")
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
