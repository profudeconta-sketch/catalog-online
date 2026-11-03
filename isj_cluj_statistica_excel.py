"""Exportul statistic ISJ Cluj, clasa IX TH, an scolar 2026-2027.

Read-only: citeste gestiunea elevilor in memorie, fara scrieri in surse.
Model: fotografia formularului ISJ Cluj furnizata de diriginte.
"""
import datetime
import io
import unicodedata

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

SCHOOL_YEAR_START = datetime.date(2026, 9, 7)
AGE_REFERENCE_DATE = datetime.date(2027, 1, 1)
AGE_BUCKETS = tuple(range(14, 24)) + (24,)


def _norm(value):
    text = unicodedata.normalize("NFD", str(value or "").casefold().strip())
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def _is_true(value):
    return value is True or (isinstance(value, (int, str)) and _norm(value) in {"1", "da", "true"})


def _binary_field(student, keys):
    """True / False / None (lipsa sursei, nu presupunem raspunsul)."""
    for key in keys:
        if key not in student:
            continue
        val = student[key]
        if val is True or _norm(val) in {"1", "da", "true"}:
            return True
        if val is False or _norm(val) in {"0", "nu", "false"}:
            return False
    return None


def _date(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    val = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(val, fmt).date()
        except ValueError:
            pass
    return None


def _enrolled_at_start(student):
    """Pastreaza transferatii ulterior inceperii anului; exclude adaugarile ulterioare."""
    history = student.get("istoric_miscare", [])
    if not isinstance(history, list):
        return True
    for event in history:
        if not isinstance(event, dict):
            continue
        event_type = _norm(event.get("tip", ""))
        event_date = _date(event.get("data"))
        if event_type in {"adaugat", "inscris"} and event_date and event_date > SCHOOL_YEAR_START:
            return False
        if event_type in {"transferat", "retras"} and event_date and event_date <= SCHOOL_YEAR_START:
            return False
    return True


def _sex_age(student):
    """Sex si varsta din CNP valid calendaristic, fara inferente din prenume."""
    cnp = str(student.get("cnp") or "").strip()
    if len(cnp) == 13 and cnp.isdigit() and cnp[0] in "123456":
        century = {"1": 1900, "2": 1900, "3": 1800, "4": 1800,
                   "5": 2000, "6": 2000}[cnp[0]]
        try:
            born = datetime.date(
                century + int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7])
            )
        except ValueError:
            born = None
        if born and born <= AGE_REFERENCE_DATE:
            age = AGE_REFERENCE_DATE.year - born.year
            if (AGE_REFERENCE_DATE.month, AGE_REFERENCE_DATE.day) < (born.month, born.day):
                age -= 1
            return ("F" if int(cnp[0]) % 2 == 0 else "M"), age
    # Date explicite, daca exista; nu folosim presupuneri pe baza prenumelui.
    raw_sex = _norm(student.get("sex", student.get("gen", "")))
    sex = "F" if raw_sex in {"f", "fata", "feminin"} else (
        "M" if raw_sex in {"m", "baiat", "masculin"} else None
    )
    born = _date(student.get("data_nasterii"))
    age = None
    if born and born <= AGE_REFERENCE_DATE:
        age = AGE_REFERENCE_DATE.year - born.year
        if (AGE_REFERENCE_DATE.month, AGE_REFERENCE_DATE.day) < (born.month, born.day):
            age -= 1
    return sex, age


def _ethnicity(student):
    raw = student.get("etnie")
    if not str(raw or "").strip():
        return None, ""
    value = _norm(raw)
    if value in {"romana", "roman", "romani", "romanesc", "romaneasca"}:
        return "romana", str(raw).strip()
    if value in {"maghiara", "maghiar", "ungur", "unguroaica"}:
        return "maghiara", str(raw).strip()
    if value in {"roma", "rom", "rrom", "rroma", "rromi", "romi", "romani/roma"}:
        return "roma", str(raw).strip()
    return "alte", str(raw).strip()


def _citizenship(student):
    val = student.get("cetatenie", student.get("nationalitate", ""))
    norm = _norm(val)
    if not norm:
        return None
    return "romana" if norm in {"romana", "roman", "romania"} else "alta"


def _pair(students, predicate, *, source_complete=True):
    matching = [p for p in students if predicate(p)]
    total = len(matching) if source_complete else None
    females = (sum(p["_sex"] == "F" for p in matching)
               if source_complete and all(p["_sex"] in {"F", "M"} for p in matching)
               else None)
    return total, females


def build_isj_statistica_clasa(gest_data):
    """Intoarce continutul .xlsx, pentru butonul existent din Gestiune Elevi."""
    if not isinstance(gest_data, list):
        raise ValueError("Datele de gestiune trebuie sa fie o lista.")
    students = []
    for record in gest_data:
        if not isinstance(record, dict):
            raise ValueError("Inregistrare de elev invalida; exportul a fost oprit.")
        if not _enrolled_at_start(record):
            continue
        student = dict(record)
        student["_sex"], student["_age"] = _sex_age(record)
        student["_ethnie"], student["_ethnie_text"] = _ethnicity(record)
        student["_cetatenie"] = _citizenship(record)
        student["_first"] = _binary_field(
            record, ("prima_inscriere_nivel", "inscris_pentru_prima_oara", "prima_data_nivel")
        )
        student["_promotion"] = _binary_field(
            record, ("din_promotia_curenta", "promotia_curenta", "absolvent_2026")
        )
        student["_repeater"] = _binary_field(
            record, ("provenit_din_repetentie", "provenit_repetentie", "repetent_la_inscriere")
        )
        students.append(student)

    all_known_first = all(p["_first"] is not None for p in students)
    all_known_promotion = all(p["_promotion"] is not None for p in students)
    all_known_repeaters = all(p["_repeater"] is not None for p in students)
    all_known_ages = all(p["_age"] is not None and p["_age"] >= 14 for p in students)
    all_known_ethnicities = all(p["_ethnie"] is not None for p in students)
    all_known_citizenships = all(p["_cetatenie"] is not None for p in students)

    pairs = []
    initial_enrollment = _pair(students, lambda p: True)
    pairs.append(initial_enrollment)
    # Conform instructiunii dirigintelui pentru formularul ISJ Cluj,
    # ambele rubrici "din care" repeta efectivul de la inceputul anului
    # (inclusiv numarul de fete). Nu estimam din alte date.
    pairs.append(initial_enrollment)
    pairs.append(initial_enrollment)
    for age in AGE_BUCKETS:
        pairs.append(_pair(
            students,
            (lambda p, n=age: p["_age"] == n) if age != 24
            else (lambda p: p["_age"] is not None and p["_age"] >= 24),
            source_complete=all_known_ages,
        ))
    pairs.append(_pair(students, lambda p: p["_repeater"] is True,
                       source_complete=all_known_repeaters))
    pairs.append(_pair(students, lambda p: p["_cetatenie"] == "romana",
                       source_complete=all_known_citizenships))
    for etnie in ("romana", "maghiara", "roma", "alte"):
        pairs.append(_pair(students, lambda p, e=etnie: p["_ethnie"] == e,
                           source_complete=all_known_ethnicities))
    pairs.append(_pair(students, lambda p: p["_cetatenie"] == "alta",
                       source_complete=all_known_citizenships))
    if len(pairs) != 21:
        raise AssertionError("Structura ISJ trebuie sa contina exact 21 indicatori pereche.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Statistica IX TH - ISJ Cluj"
    ws.sheet_view.showGridLines = False

    # Intregul formular are 44 de coloane, conform machetei ISJ.
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 22
    for col in range(3, 45):
        ws.column_dimensions[get_column_letter(col)].width = 4.7

    dark = "303943"
    muted = "E9EDF1"
    light = "F5F7F9"
    edge = Side(style="thin", color="72777E")
    thin = Border(left=edge, right=edge, top=edge, bottom=edge)

    ws.merge_cells("A1:AR1")
    ws["A1"] = 'COLEGIUL „EMIL NEGRUȚIU” TURDA'
    ws.merge_cells("A2:AR2")
    ws["A2"] = "ANUL ȘCOLAR 2026–2027"
    for r in (1, 2):
        ws.cell(r, 1).font = Font(name="Arial", size=8, bold=True, color=dark)
        ws.cell(r, 1).alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 14
    ws.row_dimensions[2].height = 13

    group_headers = [
        ("C3:H3", "Secțiunea 1: Elevi înscriși"),
        ("I3:AF3", "Secțiunea 2: Elevi înscriși pe vârste (= ani împliniți la 01.01.2027)"),
        ("AG3:AR3", "Secțiunea 3: Elevi înscriși pe cetățenie / etnii"),
    ]
    for area, label in group_headers:
        ws.merge_cells(area)
        ws[area.split(":")[0]] = label

    ws.merge_cells("A3:A6")
    ws["A3"] = "Clasa"
    ws.merge_cells("B3:B6")
    ws["B3"] = "Specializarea/\nCalificarea profesională"

    labels = [
        "Nr. elevi înscriși la început de an școlar 2026",
        "** din care: pentru prima oară",
        "*** din care: din promoția curentă",
    ]
    labels.extend(f"{age} ani" if age != 24 else "24 ani și peste"
                  for age in AGE_BUCKETS)
    labels.extend([
        "proveniți din repetenție",
        "Elevi de cetățenie română",
        "Etnie: Română",
        "Etnie: Maghiară",
        "Etnie: Romă",
        "Alte etnii",
        "Elevi de altă cetățenie decât cea ROMÂNĂ",
    ])
    for index, label in enumerate(labels):
        first_col = 3 + index * 2
        last_col = first_col + 1
        ws.merge_cells(
            start_row=4, start_column=first_col,
            end_row=5, end_column=last_col
        )
        cell = ws.cell(4, first_col)
        cell.value = label
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        for offset, sublabel in enumerate(("Total", "din care:\nfete")):
            ws.cell(6, first_col + offset, sublabel)

    for row in range(3, 7):
        for col in range(1, 45):
            cell = ws.cell(row, col)
            cell.fill = PatternFill("solid", fgColor=muted if row <= 5 else light)
            cell.border = thin
            cell.font = Font(name="Arial", size=6.1 if row < 6 else 6.2,
                             color="202428", bold=(row == 3))
            if row != 4:
                cell.alignment = Alignment(horizontal="center", vertical="center",
                                           wrap_text=True)
    ws.row_dimensions[3].height = 15
    ws.row_dimensions[4].height = 35
    ws.row_dimensions[5].height = 22
    ws.row_dimensions[6].height = 25

    values = ["IX TH", "Tehnician în turism"]
    for count, females in pairs:
        values.extend((count, females))
    if len(values) != 44:
        raise AssertionError("Statistica trebuie sa aiba 44 de coloane.")
    for col, value in enumerate(values, 1):
        cell = ws.cell(7, col, value)
        cell.border = thin
        cell.font = Font(name="Arial", size=7, bold=(col in (1, 2)))
        cell.alignment = Alignment(
            horizontal="left" if col == 2 else "center",
            vertical="center", shrink_to_fit=(col == 2)
        )
    ws.row_dimensions[7].height = 19
    for col in range(1, 45):
        ws.cell(8, col).border = thin
    ws.row_dimensions[8].height = 10
    ws.merge_cells("A9:B9")
    ws["A9"] = "TOTAL"
    ws["A9"].font = Font(name="Arial", size=7, bold=True)
    ws["A9"].alignment = Alignment(horizontal="center", vertical="center")
    for col in range(1, 45):
        cell = ws.cell(9, col)
        cell.fill = PatternFill("solid", fgColor=muted)
        cell.border = thin
        if col >= 3 and values[col - 1] is not None:
            cell.value = values[col - 1]
        cell.font = Font(name="Arial", size=7, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[9].height = 19

    ws.merge_cells("A10:U10")
    ws["A10"] = "Diriginte: Gherman Octavian-Theodor"
    ws["A10"].font = Font(name="Arial", size=8, bold=True)
    ws.row_dimensions[10].height = 21

    ws.merge_cells("A12:AR12")
    ws["A12"] = "ELEVII DE ALTĂ ETNIE DECÂT CEA ROMÂNĂ — EVIDENȚĂ NOMINALĂ"
    ws["A12"].fill = PatternFill("solid", fgColor=muted)
    ws["A12"].font = Font(name="Arial", size=8, bold=True)
    ws["A12"].alignment = Alignment(vertical="center")
    ws.row_dimensions[12].height = 18

    def named_row(row, name, ethnicity, header=False):
        # Borduri complete pe intreaga latime a fiecarei celule unite:
        # A:AH = nume, AI:AR = etnie. Doar conturul celulei din stanga
        # nu este suficient pentru a reda corect liniatura la imprimare.
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=34)
        ws.merge_cells(start_row=row, start_column=35, end_row=row, end_column=44)
        outline = Side(style="medium", color="4B5563")
        empty = Side(style=None)
        fill = PatternFill("solid", fgColor=muted if header else "FFFFFF")
        for col in range(1, 45):
            cell = ws.cell(row, col)
            cell.border = Border(
                left=outline if col in (1, 35) else empty,
                right=outline if col in (34, 44) else empty,
                top=outline,
                bottom=outline,
            )
            cell.fill = fill
        for col, value in ((1, name), (35, ethnicity)):
            cell = ws.cell(row, col, value)
            cell.font = Font(name="Arial", size=8 if header else 7.5,
                             bold=header)
            cell.alignment = Alignment(vertical="center", horizontal="left", indent=1)
        ws.row_dimensions[row].height = 19 if header else 17

    named_row(13, "Numele și prenumele elevului", "Etnia", header=True)
    non_romanian = sorted(
        (p for p in students if p["_ethnie"] in {"maghiara", "roma", "alte"}),
        key=lambda p: _norm(p.get("nume_complet", "")),
    )
    for offset, student in enumerate(non_romanian, start=14):
        name = str(student.get("nume_complet") or " ".join(
            str(student.get(k) or "") for k in ("nume", "initiala", "prenume")
        )).strip()
        named_row(offset, name, student["_ethnie_text"])
    last_nominal = 13 + len(non_romanian)
    if not non_romanian:
        named_row(14, "Nu sunt înscriși elevi de altă etnie în datele completate.", "—")
        last_nominal = 14

    ws.merge_cells(start_row=last_nominal + 2, start_column=1,
                   end_row=last_nominal + 2, end_column=44)
    footnote = ws.cell(last_nominal + 2, 1)
    footnote.value = (
        "** doar clasa a IX-a / Anul I postliceal: înscriși pentru prima dată la nivelul respectiv. "
        "*** promoția 2026. Conform cerinței școlii, cele două rubrici «din care» preiau "
        "efectivul inițial. Alte câmpuri fără sursă explicită rămân necompletate."
    )
    footnote.font = Font(name="Arial", size=6, italic=True)
    footnote.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[last_nominal + 2].height = 19

    issues = []
    if not all(p["_sex"] in {"M", "F"} for p in students):
        issues.append("sex necunoscut pentru unele înregistrări")
    if not all_known_ages:
        issues.append("vârsta la 01.01.2027 incompletă (CNP/data nașterii)")
    if not all_known_ethnicities:
        issues.append("etnie necompletată")
    if not all_known_citizenships:
        issues.append("cetățenie/naționalitate necompletată")
    if not all_known_repeaters:
        issues.append("repetenție fără sursă explicită")
    if issues:
        ws.merge_cells(start_row=last_nominal + 3, start_column=1,
                       end_row=last_nominal + 3, end_column=44)
        c = ws.cell(last_nominal + 3, 1, "Verificare date: " + "; ".join(issues) + ".")
        c.font = Font(name="Arial", size=6, color="8A3418")
        c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.row_dimensions[last_nominal + 3].height = 22
        final_row = last_nominal + 3
    else:
        final_row = last_nominal + 2

    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.print_options.horizontalCentered = True
    ws.print_area = f"A1:AR{final_row}"
    ws.page_margins = PageMargins(left=0.15, right=0.15, top=0.2, bottom=0.2,
                                  header=0.05, footer=0.05)
    wb.calculation.fullCalcOnLoad = True
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()
