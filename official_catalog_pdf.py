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
from datetime import date, datetime
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import openpyxl
import fontpkg
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from annual_closure_engine import (
    AnnualClosureSnapshot,
    AnnualFinalizationRecord,
    AnnualDeferredSituationRecord,
    DeferredToCorigentRecord,
    CorigentSessionRecord,
    ReexaminationApprovalRecord,
    verify_annual_closure_snapshot,
    verify_annual_finalization_record,
    verify_annual_deferred_situation_record,
    verify_deferred_to_corigent_record,
    verify_corigent_session_record,
    verify_reexamination_approval_record,
)


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


ROMAN_MONTHS = (
    "",
    "I", "II", "III", "IV", "V", "VI",
    "VII", "VIII", "IX", "X", "XI", "XII",
)


def _coerce_catalog_date(value: object) -> date:
    """Interpretează o dată fără a modifica valoarea din workbook."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _norm(value)
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise OfficialCatalogError(f"Data {text!r} nu poate fi reprezentată sigur în catalog.")


def format_catalog_grade(entry: GradeEntry) -> str:
    """Ex.: nota 10 din 07.10.2026 -> 10/07.X."""
    if entry.date is None or not _norm(entry.date):
        raise OfficialCatalogError("O notă fără dată nu poate fi tipărită în catalogul oficial.")
    d = _coerce_catalog_date(entry.date)
    grade = _norm(entry.grade)
    if not grade:
        raise OfficialCatalogError("Nota este goală.")
    return f"{grade}/{d.day:02d}.{ROMAN_MONTHS[d.month]}"


@dataclass(frozen=True)
class AbsenceEntry:
    date: date
    motivated: bool


def _parse_existing_absence(value: object) -> AbsenceEntry:
    """Interpretează convenția existentă: sufixul m/M marchează motivarea."""
    raw = _norm(value)
    if not raw:
        raise OfficialCatalogError("Absența este goală.")
    motivated = raw.endswith(("m", "M"))
    date_text = raw[:-1].strip() if motivated else raw
    return AbsenceEntry(date=_coerce_catalog_date(date_text), motivated=motivated)


def extract_absence_entries(wb, student: StudentIdentity, source_key: str) -> tuple[AbsenceEntry, ...]:
    """Citește exclusiv cele 30 de celule de absențe ale disciplinei/modulului."""
    sheet_name, start_col = _source_location(source_key)
    ws = wb[sheet_name]
    entries: list[AbsenceEntry] = []
    for k in range(30):
        value = ws.cell(row=student.row, column=start_col + 21 + k).value
        if value is not None and _norm(value):
            entries.append(_parse_existing_absence(value))
    return tuple(entries)


def format_catalog_absence_dates(values: Sequence[AbsenceEntry]) -> tuple[str, ...]:
    """Formă textuală de control; randarea PDF va încercui zilele motivate."""
    grouped: dict[int, list[AbsenceEntry]] = {}
    for entry in values:
        grouped.setdefault(entry.date.month, []).append(entry)

    result: list[str] = []
    for month in sorted(grouped):
        days = ",".join(f"{entry.date.day:02d}" for entry in sorted(grouped[month], key=lambda x: x.date.day))
        result.append(f"{ROMAN_MONTHS[month]}:{days}")
    return tuple(result)


def draw_catalog_absence_line(
    c: canvas.Canvas,
    entries: Sequence[AbsenceEntry],
    x: float,
    y: float,
    font_size: float = 5.2,
) -> float:
    """Desenează luna/zilele; ziua motivată primește oval grafic, nu simbol textual."""
    if not entries:
        return x
    month = entries[0].date.month
    if any(entry.date.month != month for entry in entries):
        raise OfficialCatalogError("O linie de absențe poate conține o singură lună.")

    c.setFont(PDF_FONT, font_size)
    prefix = f"{ROMAN_MONTHS[month]}:"
    c.drawString(x, y, prefix)
    cursor = x + pdfmetrics.stringWidth(prefix, PDF_FONT, font_size)

    for index, entry in enumerate(sorted(entries, key=lambda item: item.date.day)):
        if index:
            c.drawString(cursor, y, ",")
            cursor += pdfmetrics.stringWidth(",", PDF_FONT, font_size)

        day_text = f"{entry.date.day:02d}"
        day_w = pdfmetrics.stringWidth(day_text, PDF_FONT, font_size)
        c.drawString(cursor, y, day_text)
        if entry.motivated:
            pad_x = 1.1
            pad_y = 1.2
            c.ellipse(
                cursor - pad_x,
                y - pad_y,
                cursor + day_w + pad_x,
                y + font_size + pad_y,
                stroke=1,
                fill=0,
            )
        cursor += day_w
    return cursor


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


def extract_existing_average(wb, student: StudentIdentity, source_key: str) -> object | None:
    """Citește media existentă la +20; nu o calculează și nu o modifică."""
    sheet_name, start_col = _source_location(source_key)
    value = wb[sheet_name].cell(row=student.row, column=start_col + 20).value
    if value is None or not _norm(value):
        return None
    return value


@dataclass(frozen=True)
class ExistingAttendanceSummary:
    unmotivated: object | None
    motivated: object | None
    total: object | None
    conduct: object | None


def extract_existing_attendance_summary(wb, student: StudentIdentity) -> ExistingAttendanceSummary:
    """Citește valorile persistente din «Absențe & Purtare», fără recalculare."""
    ws = wb["Absențe & Purtare"]

    def existing(column: int) -> object | None:
        value = ws.cell(row=student.row, column=column).value
        return None if value is None or not _norm(value) else value

    return ExistingAttendanceSummary(
        unmotivated=existing(5),
        motivated=existing(6),
        total=existing(7),
        conduct=existing(8),
    )


def extract_existing_general_average(wb, student: StudentIdentity) -> object | None:
    """Citește media generală persistentă din Centralizator Medii, coloana 7."""
    value = wb["Centralizator Medii"].cell(row=student.row, column=7).value
    return None if value is None or not _norm(value) else value


@dataclass(frozen=True)
class PhysicalSubjectData:
    label: str | None
    source_key: str | None
    grades: tuple[GradeEntry, ...]
    absences: tuple[AbsenceEntry, ...]
    average: object | None


@dataclass(frozen=True)
class OfficialCatalogSubjectPrintState:
    """Cele trei rubrici fizice ale unei discipline, fără a inventa rezultate de examen."""
    source_key: str
    end_of_courses_average: object | None
    corigency_exam_average: object | None
    annual_average: object | None


@dataclass(frozen=True)
class OfficialCatalogAnnualState:
    """Valori anuale validate folosite numai la randarea catalogului."""
    student_key: str
    subject_annual_averages: tuple[tuple[str, int], ...]
    conduct_annual_average: object | None
    general_average: object | None
    end_of_courses_status: str
    final_status: str

    def subject_average(self, source_key: str) -> object | None:
        values = dict(self.subject_annual_averages)
        return values.get(source_key)

    def subject_print_state(
        self,
        source_key: str,
        existing_end_of_courses_average: object | None,
    ) -> OfficialCatalogSubjectPrintState:
        """Media de examen rămâne goală până când există o sursă explicită pentru ea."""
        return OfficialCatalogSubjectPrintState(
            source_key=source_key,
            end_of_courses_average=existing_end_of_courses_average,
            corigency_exam_average=None,
            annual_average=self.subject_average(source_key),
        )


AnnualAuditRecord = (
    AnnualDeferredSituationRecord
    | DeferredToCorigentRecord
    | CorigentSessionRecord
    | ReexaminationApprovalRecord
)


def validate_finalization_audit_chain_for_print(
    snapshot: AnnualClosureSnapshot,
    finalization: AnnualFinalizationRecord,
    audit_records: Sequence[AnnualAuditRecord],
) -> None:
    """Verifică fail-closed fiecare SHA declarat de actul final înainte de tipărire."""
    declared = tuple(finalization.audit_chain_sha256)
    if len(audit_records) != len(declared):
        raise OfficialCatalogError(
            "Lanțul de audit declarat de actul final nu a fost furnizat integral."
        )

    actual: list[str] = []
    previous_deferred: AnnualDeferredSituationRecord | None = None
    previous_transition: DeferredToCorigentRecord | None = None
    previous_session: CorigentSessionRecord | None = None

    for record in audit_records:
        if isinstance(record, AnnualDeferredSituationRecord):
            if not verify_annual_deferred_situation_record(record):
                raise OfficialCatalogError("Anexa AMÂNAT din lanț nu trece verificarea SHA-256.")
            if (
                record.source_snapshot_sha256 != snapshot.integrity_sha256
                or record.student_key != snapshot.student_key
                or record.school_year != snapshot.school_year
            ):
                raise OfficialCatalogError("Anexa AMÂNAT nu aparține snapshotului tipărit.")
            previous_deferred = record
        elif isinstance(record, DeferredToCorigentRecord):
            if not verify_deferred_to_corigent_record(record):
                raise OfficialCatalogError("Tranziția AMÂNAT→CORIGENT nu trece verificarea SHA-256.")
            if (
                previous_deferred is None
                or record.source_snapshot_sha256 != snapshot.integrity_sha256
                or record.deferred_record_sha256 != previous_deferred.integrity_sha256
                or record.student_key != snapshot.student_key
                or record.school_year != snapshot.school_year
            ):
                raise OfficialCatalogError("Tranziția AMÂNAT→CORIGENT nu continuă lanțul furnizat.")
            previous_transition = record
        elif isinstance(record, CorigentSessionRecord):
            if not verify_corigent_session_record(record):
                raise OfficialCatalogError("Actul primei corigențe nu trece verificarea SHA-256.")
            if (
                record.source_snapshot_sha256 != snapshot.integrity_sha256
                or record.student_key != snapshot.student_key
                or record.school_year != snapshot.school_year
            ):
                raise OfficialCatalogError("Actul primei corigențe nu aparține snapshotului tipărit.")
            expected_upstream = tuple(actual)
            if record.upstream_audit_chain_sha256 != expected_upstream:
                raise OfficialCatalogError(
                    "Actul primei corigențe nu confirmă exact lanțul anterior furnizat."
                )
            previous_session = record
        elif isinstance(record, ReexaminationApprovalRecord):
            if not verify_reexamination_approval_record(record):
                raise OfficialCatalogError("Aprobarea reexaminării nu trece verificarea SHA-256.")
            if (
                previous_session is None
                or record.source_snapshot_sha256 != snapshot.integrity_sha256
                or record.corigent_session_sha256 != previous_session.integrity_sha256
                or record.student_key != snapshot.student_key
                or record.school_year != snapshot.school_year
            ):
                raise OfficialCatalogError("Aprobarea reexaminării nu continuă lanțul furnizat.")
        else:
            raise OfficialCatalogError("Lanțul de audit conține un tip de act necunoscut.")
        actual.append(record.integrity_sha256)

    if tuple(actual) != declared:
        raise OfficialCatalogError(
            "Ordinea sau SHA-urile actelor furnizate diferă de lanțul declarat de actul final."
        )

    if previous_transition is not None and previous_deferred is None:
        raise OfficialCatalogError("Tranziția CORIGENT nu are anexă AMÂNAT anterioară.")


def official_catalog_state_from_records(
    snapshot: AnnualClosureSnapshot,
    finalization: AnnualFinalizationRecord | None = None,
    audit_records: Sequence[AnnualAuditRecord] = (),
) -> OfficialCatalogAnnualState:
    """Adaptează numai înregistrări SHA-256 valide la modelul read-only de tipărire."""
    if not verify_annual_closure_snapshot(snapshot):
        raise OfficialCatalogError("Snapshotul anual nu trece verificarea SHA-256.")

    subject_values: dict[str, int] = {}
    for row in snapshot.subjects:
        if len(row) != 5:
            raise OfficialCatalogError("Structura disciplinelor din snapshot este invalidă.")
        name = str(row[0]).strip()
        average = row[2]
        if (
            not name
            or name in subject_values
            or name not in OFFICIAL_SUBJECT_NAMES
            or not isinstance(average, int)
            or isinstance(average, bool)
            or not 1 <= average <= 10
        ):
            raise OfficialCatalogError("Snapshotul conține o disciplină sau o medie invalidă.")
        subject_values[name] = average

    final_status = snapshot.final_status
    general_average = snapshot.general_average

    if finalization is None and audit_records:
        raise OfficialCatalogError(
            "Au fost furnizate acte intermediare fără un act final de definitivare."
        )

    if finalization is not None:
        if not verify_annual_finalization_record(finalization):
            raise OfficialCatalogError("Actul de definitivare nu trece verificarea SHA-256.")
        if (
            finalization.source_snapshot_sha256 != snapshot.integrity_sha256
            or finalization.student_key != snapshot.student_key
            or finalization.school_year != snapshot.school_year
            or finalization.source_status != snapshot.final_status
        ):
            raise OfficialCatalogError("Actul de definitivare nu aparține snapshotului anual.")
        validate_finalization_audit_chain_for_print(
            snapshot, finalization, audit_records
        )
        for result in finalization.subject_results:
            name = str(result.subject_name).strip()
            if name not in subject_values:
                raise OfficialCatalogError(
                    f"Actul de definitivare conține disciplina necunoscută {name!r}."
                )
            subject_values[name] = result.resulting_annual_average
        final_status = finalization.final_status
        general_average = finalization.final_general_average

    return OfficialCatalogAnnualState(
        student_key=str(snapshot.student_key).strip(),
        subject_annual_averages=tuple(sorted(subject_values.items())),
        conduct_annual_average=snapshot.conduct_annual_average,
        general_average=general_average,
        end_of_courses_status=snapshot.final_status,
        final_status=final_status,
    )


def validate_official_catalog_annual_states(
    students: Sequence[StudentIdentity],
    annual_states: Mapping[str, OfficialCatalogAnnualState],
) -> None:
    """Fail-closed: fiecare elev tipărit trebuie să aibă exact o situație anuală coerentă."""
    allowed_statuses = {"PROMOVAT", "CORIGENT", "REPETENT", "AMANAT"}
    expected = {student.rm_pg for student in students}
    provided = {str(key).strip() for key in annual_states}
    if provided != expected:
        raise OfficialCatalogError(
            "Situațiile anuale validate nu corespund exact elevilor din catalog."
        )
    valid_subjects = set(OFFICIAL_SUBJECT_NAMES)
    for student in students:
        state = annual_states[student.rm_pg]
        if str(state.student_key).strip() != student.rm_pg:
            raise OfficialCatalogError(
                f"Situația anuală nu corespunde elevului cu RM/PG {student.rm_pg!r}."
            )
        subject_values = dict(state.subject_annual_averages)
        if len(subject_values) != len(state.subject_annual_averages):
            raise OfficialCatalogError(
                f"Situația anuală pentru {student.rm_pg!r} conține discipline duplicate."
            )
        if set(subject_values) != valid_subjects:
            raise OfficialCatalogError(
                f"Situația anuală pentru {student.rm_pg!r} nu conține exact disciplinele clasei."
            )
        for subject, average in subject_values.items():
            if not isinstance(average, int) or isinstance(average, bool) or not 1 <= average <= 10:
                raise OfficialCatalogError(
                    f"{subject}: media anuală validată este invalidă pentru {student.rm_pg!r}."
                )
        if state.end_of_courses_status not in allowed_statuses or state.final_status not in allowed_statuses:
            raise OfficialCatalogError(
                f"Statut anual invalid pentru {student.rm_pg!r}."
            )


def extract_physical_subject_data(
    wb,
    student: StudentIdentity,
    physical_slots: Sequence[str | None],
    source_keys: Sequence[str | None],
) -> tuple[PhysicalSubjectData, ...]:
    """Leagă fiecare rubrică fizică de datele ei, fără a desena sau modifica sursa."""
    if len(physical_slots) != len(source_keys):
        raise OfficialCatalogError("Harta fizică și sursele nu au aceeași lungime.")

    result: list[PhysicalSubjectData] = []
    for label, source_key in zip(physical_slots, source_keys):
        if label is None or source_key is None:
            if label is not None or source_key is not None:
                raise OfficialCatalogError("Rubrică fizică/sursă incomplet mapată.")
            result.append(PhysicalSubjectData(None, None, (), (), None))
            continue

        if OFFICIAL_SUBJECT_NAMES.get(source_key) != label:
            raise OfficialCatalogError(
                f"Rubrica {label!r} nu corespunde sursei validate {source_key!r}."
            )
        result.append(
            PhysicalSubjectData(
                label=label,
                source_key=source_key,
                grades=extract_grade_entries(wb, student, source_key),
                absences=extract_absence_entries(wb, student, source_key),
                average=extract_existing_average(wb, student, source_key),
            )
        )
    return tuple(result)


def extract_student_spread_grade_data(
    wb, student: StudentIdentity
) -> tuple[tuple[PhysicalSubjectData, ...], tuple[PhysicalSubjectData, ...]]:
    """Returnează P3 și P4 în ordinea fizică exactă a tipizatului."""
    return (
        extract_physical_subject_data(wb, student, CATALOG_P3_SLOTS, CATALOG_P3_SOURCE_KEYS),
        extract_physical_subject_data(wb, student, CATALOG_P4_SLOTS, CATALOG_P4_SOURCE_KEYS),
    )


PDF_FONT = "OfficialCatalogNoto"
PDF_FONT_BOLD = "OfficialCatalogNotoBold"


ROMANIAN_DIACRITICS_TEST = "ĂÂÎȘȚ ăâîșț"


def _register_unicode_fonts() -> None:
    """Înregistrează și validează fonturile Unicode pentru limba română."""
    try:
        font_path = str(fontpkg.path("Noto Sans"))
        if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(PDF_FONT, font_path))
        if PDF_FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, font_path))

        # Fail-closed: fontul trebuie să poată măsura explicit toate
        # diacriticele românești folosite în catalog, inclusiv Ș/Ț cu virgulă.
        for font_name in (PDF_FONT, PDF_FONT_BOLD):
            width = pdfmetrics.stringWidth(ROMANIAN_DIACRITICS_TEST, font_name, 10)
            if width <= 0:
                raise OfficialCatalogError(
                    f"Fontul {font_name!r} nu poate reda diacriticele românești."
                )
    except OfficialCatalogError:
        raise
    except Exception as ex:
        raise OfficialCatalogError(
            "Fontul Unicode necesar catalogului și diacriticelor românești nu este disponibil."
        ) from ex


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
            subject_width = col_x[side + 1] - col_x[side] - 6
            professor_width = col_x[side + 2] - col_x[side + 1] - 6
            try:
                subject_size = _fit_text(c, subject, subject_width, PDF_FONT, 5.5, 4.0)
                subject_lines = (subject,)
            except OfficialCatalogError:
                words = subject.split()
                split_at = min(
                    range(1, len(words)),
                    key=lambda index: abs(
                        pdfmetrics.stringWidth(" ".join(words[:index]), PDF_FONT, 4.2)
                        - pdfmetrics.stringWidth(" ".join(words[index:]), PDF_FONT, 4.2)
                    ),
                )
                subject_lines = (" ".join(words[:split_at]), " ".join(words[split_at:]))
                subject_size = min(
                    _fit_text(c, line, subject_width, PDF_FONT, 4.6, 4.0)
                    for line in subject_lines
                )
            professor_size = _fit_text(c, professor, professor_width, PDF_FONT, 5.5, 4.0)
            c.setFont(PDF_FONT, subject_size)
            if len(subject_lines) == 1:
                c.drawString(col_x[side] + 3, y, subject_lines[0])
            else:
                c.drawString(col_x[side] + 3, y + 2.4, subject_lines[0])
                c.drawString(col_x[side] + 3, y - 3.0, subject_lines[1])
            c.setFont(PDF_FONT, professor_size)
            c.drawString(col_x[side + 1] + 3, y, professor)

    c.setFont(PDF_FONT, 5.7)
    c.drawString(34, 101, "*) denumirea curentă a ministerului")
    c.drawString(34, 92, "**) se completează pentru filierea tehnologică")

def _gest_by_identity(gest_data: Sequence[Mapping], students: Sequence[StudentIdentity]) -> dict[str, Mapping]:
    """Leagă datele personale numai prin RM/PG deja validat."""
    by_rm: dict[str, Mapping] = {}
    for row in gest_data:
        rm_pg = _norm(row.get("matricol"))
        if rm_pg:
            if rm_pg in by_rm:
                raise OfficialCatalogError(f"RM/PG duplicat în gestiune: {rm_pg!r}.")
            by_rm[rm_pg] = row
    for student in students:
        if student.rm_pg not in by_rm:
            raise OfficialCatalogError(f"Lipsesc datele de gestiune pentru RM/PG {student.rm_pg!r}.")
    return by_rm


def _birth_date_from_cnp(cnp_value: object) -> str:
    """Derivă data nașterii numai dintr-un CNP valid; nu modifică sursa."""
    cnp = _norm(cnp_value)
    if len(cnp) != 13 or not cnp.isdigit():
        return ""
    sex_century = int(cnp[0])
    year2, month, day = int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7])
    century = {1: 1900, 2: 1900, 3: 1800, 4: 1800, 5: 2000, 6: 2000}.get(sex_century)
    if century is None:
        return ""
    try:
        born = date(century + year2, month, day)
    except ValueError:
        return ""
    return born.strftime("%d.%m.%Y")


def _draw_students_grid(
    c: canvas.Canvas,
    students: Sequence[StudentIdentity],
    gest_by_rm: Mapping[str, Mapping],
    page_no: int,
) -> None:
    """P29 – Date personale: numai rubricile confirmate ale tipizatului."""
    width, height = A4
    left, right = 18, width - 16
    top, bottom = height - 72, 48
    rows = 35
    row_h = (top - bottom) / (rows + 2)
    widths = (18, 34, 45, 100, 46, 90, 66, 66, 70)
    scale = (right - left) / sum(widths)
    cols = [left]
    for w in widths:
        cols.append(cols[-1] + w * scale)

    headers = (
        "Nr. crt.",
        "Nr. matricol",
        "Registru matricol / pag.",
        "Nume, inițiala tatălui, prenume",
        "Data nașterii",
        "Adresa elevului",
        "Nume și prenume mamă",
        "Nume și prenume tată",
        "Observații",
    )
    c.setFont(PDF_FONT_BOLD, 4.1)
    for i, label in enumerate(headers):
        c.drawCentredString((cols[i] + cols[i + 1]) / 2, top - row_h + 4, label)

    c.setLineWidth(0.35)
    for x in cols:
        c.line(x, bottom, x, top)
    for r in range(rows + 2):
        y = top - r * row_h
        c.line(left, y, right, y)

    c.setFont(PDF_FONT, 3.9)
    for idx in range(rows):
        y = top - (idx + 2) * row_h + 4
        c.drawCentredString((cols[0] + cols[1]) / 2, y, str(idx + 1))
        if idx >= len(students):
            continue
        student = students[idx]
        p = gest_by_rm[student.rm_pg]
        c.drawCentredString((cols[1] + cols[2]) / 2, y, student.nr_matr)
        c.drawCentredString((cols[2] + cols[3]) / 2, y, student.rm_pg)
        c.drawString(cols[3] + 1, y, student.name[:38])
        birth = _birth_date_from_cnp(p.get("cnp"))
        if birth:
            c.drawCentredString((cols[4] + cols[5]) / 2, y, birth)
        address = ", ".join(v for v in (
            _norm(p.get("localitate")), _norm(p.get("judet")), _norm(p.get("strada")),
            _norm(p.get("numar_strada")), _norm(p.get("bloc")), _norm(p.get("apartament"))
        ) if v)
        c.drawString(cols[5] + 1, y, address[:32])
        c.drawString(cols[6] + 1, y, _norm(p.get("nume_mama"))[:24])
        c.drawString(cols[7] + 1, y, _norm(p.get("nume_tata"))[:24])
        phones = " / ".join(v for v in (
            _norm(p.get("telefon_mama")), _norm(p.get("telefon_tata"))
        ) if v)
        if phones:
            c.drawString(cols[8] + 1, y, phones[:24])

@dataclass(frozen=True)
class GeneralStatistics:
    recorded_students: int
    active_students: int
    transferred_students: int
    withdrawn_students: int
    added_dated_students: int
    departed_dated_students: int
    total_absences: int
    unmotivated_absences: int
    promoted_students: int | None = None
    corigent_students: int | None = None
    repeat_students: int | None = None
    deferred_students: int | None = None


def extract_general_statistics(wb, students: Sequence[StudentIdentity], gest_by_rm: Mapping[str, Mapping]) -> GeneralStatistics:
    """P30: numai valori direct verificabile; fără inferențe privind rezultatul școlar."""
    active = transferred = withdrawn = added_dated = departed_dated = total_abs = unmotivated = 0
    ws = wb["Absențe & Purtare"]
    for student in students:
        status = _norm(gest_by_rm[student.rm_pg].get("status_scolar", "ACTIV")).upper()
        if status == "ACTIV":
            active += 1
        elif status == "TRANSFERAT":
            transferred += 1
        elif status == "RETRAS":
            withdrawn += 1
        else:
            raise OfficialCatalogError(f"Stare școlară necunoscută pentru {student.rm_pg!r}: {status!r}.")

        history = gest_by_rm[student.rm_pg].get("istoric_miscare", [])
        if history is not None and not isinstance(history, list):
            raise OfficialCatalogError(f"Istoric de mișcare invalid pentru {student.rm_pg!r}.")
        event_types = []
        for event in history or []:
            if not isinstance(event, Mapping) or not _norm(event.get("data")):
                raise OfficialCatalogError(f"Eveniment de mișcare invalid pentru {student.rm_pg!r}.")
            event_types.append(_norm(event.get("tip")).upper())
        if "ADAUGAT" in event_types:
            added_dated += 1
        if any(t in {"TRANSFERAT", "RETRAS"} for t in event_types):
            departed_dated += 1

        total_value = ws.cell(row=student.row, column=7).value
        unmotivated_value = ws.cell(row=student.row, column=5).value
        if total_value not in (None, ""):
            total_abs += int(total_value)
        if unmotivated_value not in (None, ""):
            unmotivated += int(unmotivated_value)

    return GeneralStatistics(
        recorded_students=len(students),
        active_students=active,
        transferred_students=transferred,
        withdrawn_students=withdrawn,
        added_dated_students=added_dated,
        departed_dated_students=departed_dated,
        total_absences=total_abs,
        unmotivated_absences=unmotivated,
    )


def _draw_general_statistics(c: canvas.Canvas, stats: GeneralStatistics) -> None:
    """Prototip P30; rubricile fără sursă administrativă rămân necompletate."""
    x_label, x_value = 42, 430
    y, step = A4[1] - 92, 24
    rows = (
        ("Elevi existenți în evidența clasei", stats.recorded_students),
        ("Elevi activi în evidența curentă", stats.active_students),
        ("Elevi cu starea curentă TRANSFERAT", stats.transferred_students),
        ("Elevi cu starea curentă RETRAS", stats.withdrawn_students),
        ("Total absențe", stats.total_absences),
        ("Din care nemotivate", stats.unmotivated_absences),
        ("Elevi veniți – evenimente ADAUGAT datate", stats.added_dated_students),
        ("Elevi plecați – evenimente TRANSFERAT/RETRAS datate", stats.departed_dated_students),
        ("Promovați", stats.promoted_students),
        ("Corigenți", stats.corigent_students),
        ("Repetenți", stats.repeat_students),
        ("Amânați", stats.deferred_students),
        ("Abandon școlar", None),
    )
    c.setFont(PDF_FONT, 7)
    for label, value in rows:
        c.drawString(x_label, y, label)
        c.line(x_label + 210, y - 2, x_value + 55, y - 2)
        if value is not None:
            c.setFont(PDF_FONT_BOLD, 7)
            c.drawRightString(x_value + 50, y, str(value))
            c.setFont(PDF_FONT, 7)
        y -= step

def _draw_marks_spread_placeholder(
    c: canvas.Canvas,
    wb,
    students: Sequence[StudentIdentity],
    side: str,
    annual_states: Mapping[str, OfficialCatalogAnnualState] | None = None,
) -> None:
    """Geometrie P3/P4; populează numai Note/Data și Absențe în corpul rubricilor."""
    width, height = A4
    left, right = 18, width - 16
    top, bottom = height - 47, 47
    header_h = 108
    gap = 5
    usable_h = top - bottom - header_h - 2 * gap
    block_h = usable_h / 3
    mean_h = 34
    identity_w = 132

    c.setLineWidth(0.65)

    def draw_recording_body(
        student: StudentIdentity | None,
        slots: Sequence[str | None],
        source_keys: Sequence[str | None],
        grid_start: float,
        pair_width: float,
        y_body_bottom: float,
        y_body_top: float,
    ) -> None:
        if student is None:
            return
        subject_data = extract_physical_subject_data(wb, student, slots, source_keys)
        body_h = y_body_top - y_body_bottom
        for j, subject in enumerate(subject_data):
            if subject.source_key is None:
                continue
            gx = grid_start + j * pair_width
            abs_x = gx + 1.0
            note_x = gx + pair_width / 2 + 1.0

            # Notele sunt scrise vertical, în ordinea înregistrării din workbook.
            c.saveState()
            c.translate(note_x, y_body_bottom + 2)
            c.rotate(90)
            c.setFont(PDF_FONT, 3.5)
            cursor = 0.0
            for entry in subject.grades:
                text = format_catalog_grade(entry)
                text_w = pdfmetrics.stringWidth(text, PDF_FONT, 3.5)
                if cursor + text_w > body_h - 4:
                    raise OfficialCatalogError(
                        f"Notele pentru {subject.label!r} nu încap în geometria prototipului."
                    )
                c.drawString(cursor, 0, text)
                cursor += text_w + 2.0
            c.restoreState()

            # Absențele sunt grupate lunar. Zilele motivate sunt încercuite grafic.
            by_month: dict[int, list[AbsenceEntry]] = {}
            for entry in subject.absences:
                by_month.setdefault(entry.date.month, []).append(entry)
            c.saveState()
            c.translate(abs_x, y_body_bottom + 2)
            c.rotate(90)
            cursor = 0.0
            for month in sorted(by_month):
                month_entries = sorted(by_month[month], key=lambda item: item.date.day)
                if cursor:
                    cursor += 2.0
                end_x = draw_catalog_absence_line(c, month_entries, cursor, 0, font_size=3.5)
                if end_x > body_h - 4:
                    raise OfficialCatalogError(
                        f"Absențele pentru {subject.label!r} nu încap în geometria prototipului."
                    )
                cursor = end_x
            c.restoreState()

    if side == "stângă":
        grid_left = left + identity_w
        slots = CATALOG_P3_SLOTS
        pair_w = (right - grid_left) / len(slots)

        c.rect(left, top - header_h, identity_w, header_h)
        c.setFont(PDF_FONT_BOLD, 13)
        c.drawCentredString(left + identity_w / 2, top - 28, "ELEVII")
        c.rect(grid_left, top - header_h, right - grid_left, header_h)
        c.setFont(PDF_FONT_BOLD, 6.8)
        c.drawCentredString((grid_left + right) / 2, top - 9, "DISCIPLINELE/MODULELE***")
        subject_header_bottom = top - header_h + 18
        c.line(grid_left, subject_header_bottom, right, subject_header_bottom)
        for j, slot in enumerate(slots):
            gx = grid_left + j * pair_w
            c.line(gx, top - header_h, gx, top)
            c.line(gx + pair_w / 2, top - header_h, gx + pair_w / 2, subject_header_bottom)
            if slot:
                c.saveState()
                c.translate(gx + pair_w / 2 + 0.8, subject_header_bottom + 4)
                c.rotate(90)
                size = _fit_text(c, slot, header_h - 38, PDF_FONT_BOLD, 4.1, 2.5)
                c.setFont(PDF_FONT_BOLD, size)
                c.drawString(0, 0, slot)
                c.restoreState()
            c.setFont(PDF_FONT, 2.8)
            c.drawCentredString(gx + pair_w * .25, top - header_h + 6, "Absențe")
            c.drawCentredString(gx + pair_w * .75, top - header_h + 6, "Note")
        c.line(right, top - header_h, right, top - 27)
    else:
        slots = CATALOG_P4_SLOTS
        terminal_w = 76
        grid_right = right - terminal_w
        pair_w = (grid_right - left) / len(slots)

        c.rect(left, top - header_h, right - left, header_h)
        c.setFont(PDF_FONT_BOLD, 6.8)
        c.drawCentredString((left + grid_right) / 2, top - 9, "DISCIPLINELE/MODULELE***")
        c.setFont(PDF_FONT_BOLD, 5.0)
        c.drawCentredString(grid_right + terminal_w * .72, top - 10, "ABSENȚE")
        subject_header_bottom = top - header_h + 18
        c.line(left, subject_header_bottom, grid_right, subject_header_bottom)
        for j, slot in enumerate(slots):
            gx = left + j * pair_w
            c.line(gx, top - header_h, gx, top)
            c.line(gx + pair_w / 2, top - header_h, gx + pair_w / 2, subject_header_bottom)
            if slot:
                c.saveState()
                c.translate(gx + pair_w / 2 + 0.8, subject_header_bottom + 4)
                c.rotate(90)
                size = _fit_text(c, slot, header_h - 38, PDF_FONT_BOLD, 4.1, 2.5)
                c.setFont(PDF_FONT_BOLD, size)
                c.drawString(0, 0, slot)
                c.restoreState()
            c.setFont(PDF_FONT, 2.8)
            c.drawCentredString(gx + pair_w * .25, top - header_h + 6, "Absențe")
            c.drawCentredString(gx + pair_w * .75, top - header_h + 6, "Note")
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
            if student is not None:
                annual_state = annual_states.get(student.rm_pg) if annual_states is not None else None
                general_average = (
                    annual_state.general_average
                    if annual_state is not None
                    else extract_existing_general_average(wb, student)
                )
                if annual_state is not None:
                    c.setFont(PDF_FONT_BOLD, 4.1)
                    c.drawRightString(identity_right, y_top - 112, annual_state.end_of_courses_status)
                    c.drawRightString(identity_right, y_top - 125, annual_state.final_status)
                if general_average is not None:
                    c.setFont(PDF_FONT_BOLD, 4.5)
                    c.drawRightString(identity_right, y_top - 140, _norm(general_average))

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
            c.line(right, y_bottom, right, y_top)
            draw_recording_body(
                student,
                CATALOG_P3_SLOTS,
                CATALOG_P3_SOURCE_KEYS,
                grid_left,
                pair_w,
                y_bottom + mean_h,
                y_top,
            )

            # Cele trei rânduri de medii traversează rubricile disciplinelor,
            # fără subdiviziunea verticală Absențe/Note.
            mean_row_h = mean_h / 3
            for k in range(1, 3):
                yy = y_bottom + k * mean_row_h
                c.line(grid_left, yy, right, yy)

            if student is not None:
                p3_data = extract_physical_subject_data(
                    wb, student, CATALOG_P3_SLOTS, CATALOG_P3_SOURCE_KEYS
                )
                c.setFont(PDF_FONT_BOLD, 4.0)
                for j, subject in enumerate(p3_data):
                    annual_state = annual_states.get(student.rm_pg) if annual_states is not None else None
                    if annual_state is not None and subject.source_key is not None:
                        print_state = annual_state.subject_print_state(
                            subject.source_key, subject.average
                        )
                    else:
                        print_state = OfficialCatalogSubjectPrintState(
                            source_key=subject.source_key or "",
                            end_of_courses_average=subject.average,
                            corigency_exam_average=None,
                            annual_average=subject.average,
                        )
                    gx = grid_left + j * pair_w
                    row_values = (
                        (print_state.end_of_courses_average, y_bottom + 2 * mean_row_h + 2),
                        (print_state.corigency_exam_average, y_bottom + mean_row_h + 2),
                        (print_state.annual_average, y_bottom + 2),
                    )
                    for value, yy in row_values:
                        if value is not None:
                            c.drawCentredString(gx + pair_w / 2, yy, _norm(value))

            # Etichetele apar în zona de situație școlară, nu într-o
            # pseudo-coloană de disciplină.
            c.setFont(PDF_FONT, 3.5)
            label_x = left + identity_w - 48
            c.drawRightString(label_x, y_bottom + 2 * mean_row_h + 2, "Media")
            c.drawRightString(label_x, y_bottom + mean_row_h + 2, "Media la ex. de corig.")
            c.drawRightString(label_x, y_bottom + 2, "Media anuală")
        else:
            student = students[idx] if idx < len(students) else None
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
            c.line(grid_right, y_bottom, grid_right, y_top)
            draw_recording_body(
                student,
                CATALOG_P4_SLOTS,
                CATALOG_P4_SOURCE_KEYS,
                left,
                pair_w,
                y_bottom + mean_h,
                y_top,
            )

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

            if student is not None:
                p4_data = extract_physical_subject_data(
                    wb, student, CATALOG_P4_SLOTS, CATALOG_P4_SOURCE_KEYS
                )
                c.setFont(PDF_FONT_BOLD, 4.0)
                for j, subject in enumerate(p4_data):
                    annual_state = annual_states.get(student.rm_pg) if annual_states is not None else None
                    if annual_state is not None and subject.source_key is not None:
                        print_state = annual_state.subject_print_state(
                            subject.source_key, subject.average
                        )
                    else:
                        print_state = OfficialCatalogSubjectPrintState(
                            source_key=subject.source_key or "",
                            end_of_courses_average=subject.average,
                            corigency_exam_average=None,
                            annual_average=subject.average,
                        )
                    gx = left + j * pair_w
                    row_values = (
                        (print_state.end_of_courses_average, y_bottom + 2 * mean_row_h + 2),
                        (print_state.corigency_exam_average, y_bottom + mean_row_h + 2),
                        (print_state.annual_average, y_bottom + 2),
                    )
                    for value, yy in row_values:
                        if value is not None:
                            c.drawCentredString(gx + pair_w / 2, yy, _norm(value))

            if student is not None:
                attendance = extract_existing_attendance_summary(wb, student)
                annual_state = annual_states.get(student.rm_pg) if annual_states is not None else None
                c.setFont(PDF_FONT_BOLD, 4.2)

                # Nota la purtare este valoarea persistentă din coloana 8.
                # Se înscrie în zona de corp Purtare; rândul median barat cu X
                # și celelalte câmpuri manuale ale tipizatului rămân neatinse.
                conduct_value = (
                    annual_state.conduct_annual_average
                    if annual_state is not None
                    else attendance.conduct
                )
                if conduct_value is not None:
                    conduct_body_y = (y_bottom + mean_h + conduct_split_y) / 2
                    c.drawCentredString(
                        (x_conduct + x_total) / 2,
                        conduct_body_y,
                        _norm(conduct_value),
                    )

                if attendance.total is not None:
                    c.drawCentredString(
                        (x_total + x_unmotiv) / 2,
                        y_bottom + 2 * mean_row_h + 2,
                        _norm(attendance.total),
                    )
                if attendance.unmotivated is not None:
                    c.drawCentredString(
                        (x_unmotiv + right) / 2,
                        y_bottom + 2 * mean_row_h + 2,
                        _norm(attendance.unmotivated),
                    )

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
        gest_by_rm = _gest_by_identity(gest_data, students)

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
            _draw_marks_spread_placeholder(c, wb, group, "stângă")
            _draw_prototype_notice(c)
            c.showPage()

            _draw_page_frame(c, right_page, "Situația școlară – corp catalog")
            _draw_marks_spread_placeholder(c, wb, group, "dreaptă")
            _draw_prototype_notice(c)
            c.showPage()

        # P29: date personale – 35 poziții conform planșei oficiale.
        _draw_page_frame(c, 29, "DATE PERSONALE ALE ELEVILOR")
        _draw_students_grid(c, students, gest_by_rm, 29)
        _draw_prototype_notice(c)
        c.showPage()

        # P30: statistica anuală; fără inferențe administrative.
        _draw_page_frame(c, 30, "Situația generală asupra mișcării și frecvenței elevilor și a rezultatelor obținute")
        _draw_prototype_notice(c)
        general_stats = extract_general_statistics(wb, students, gest_by_rm)
        _draw_general_statistics(c, general_stats)
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


def generate_official_catalog_final(
    excel_path: str,
    gest_data: Sequence[Mapping],
    annual_states: Mapping[str, OfficialCatalogAnnualState],
) -> bytes:
    """Generează catalogul pentru tipărire din sursa primară + situații anuale validate.

    Funcția este strict read-only: nu salvează workbook-ul și nu persistă situațiile.
    """
    _register_unicode_fonts()
    _validate_physical_source_mapping()
    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    try:
        students = validate_and_resolve_students(wb, gest_data)
        validate_official_catalog_annual_states(students, annual_states)
        gest_by_rm = _gest_by_identity(gest_data, students)

        out = io.BytesIO()
        c = canvas.Canvas(out, pagesize=A4, pageCompression=1, invariant=1)

        _draw_page_frame(c, 1, "Date de identificare și cadre didactice")
        _draw_admin_page(c)
        c.showPage()

        _draw_page_frame(c, 2, "NORME pentru completarea și utilizarea catalogului clasei")
        c.setFont(PDF_FONT, 8)
        c.drawString(42, A4[1] - 85, "Pagina rezervată reproducerii fidele a normelor din tipizatul oficial.")
        c.showPage()

        for spread_index in range(13):
            start_pos = spread_index * 3
            group = students[start_pos : start_pos + 3]
            left_page = 3 + spread_index * 2
            right_page = left_page + 1

            _draw_page_frame(c, left_page, "Situația școlară – corp catalog")
            _draw_marks_spread_placeholder(c, wb, group, "stângă", annual_states)
            c.showPage()

            _draw_page_frame(c, right_page, "Situația școlară – corp catalog")
            _draw_marks_spread_placeholder(c, wb, group, "dreaptă", annual_states)
            c.showPage()

        _draw_page_frame(c, 29, "DATE PERSONALE ALE ELEVILOR")
        _draw_students_grid(c, students, gest_by_rm, 29)
        c.showPage()

        _draw_page_frame(
            c,
            30,
            "Situația generală asupra mișcării și frecvenței elevilor și a rezultatelor obținute",
        )
        base_stats = extract_general_statistics(wb, students, gest_by_rm)
        final_counts = {"PROMOVAT": 0, "CORIGENT": 0, "REPETENT": 0, "AMANAT": 0}
        for student in students:
            final_counts[annual_states[student.rm_pg].final_status] += 1
        general_stats = GeneralStatistics(
            recorded_students=base_stats.recorded_students,
            active_students=base_stats.active_students,
            transferred_students=base_stats.transferred_students,
            withdrawn_students=base_stats.withdrawn_students,
            added_dated_students=base_stats.added_dated_students,
            departed_dated_students=base_stats.departed_dated_students,
            total_absences=base_stats.total_absences,
            unmotivated_absences=base_stats.unmotivated_absences,
            promoted_students=final_counts["PROMOVAT"],
            corigent_students=final_counts["CORIGENT"],
            repeat_students=final_counts["REPETENT"],
            deferred_students=final_counts["AMANAT"],
        )
        _draw_general_statistics(c, general_stats)
        c.showPage()

        _draw_page_frame(c, 31, "PROCES-VERBAL")
        c.setFont(PDF_FONT, 8)
        c.drawString(42, A4[1] - 85, "Semnăturile și constatările administrative rămân necompletate automat.")
        c.showPage()

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
