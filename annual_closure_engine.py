"""Motor read-only pentru Etapa 5.6 – evaluarea închiderii situației școlare.

Acest modul NU scrie în Excel/JSON și NU modifică date primare.
Rezultatele sunt propuneri de închidere care trebuie validate înainte de persistare.

Bază normativă urmărită:
- ROFUIP, OME nr. 5.726/2024, cu modificările în vigoare.
- Statutul elevului, OM nr. 5.707/2024.

Regulile dependente de planul-cadru (număr anual de ore, momentul finalizării
modulelor) sunt intrări explicite; motorul nu le ghicește.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo
import hashlib
import json


class AnnualClosureError(RuntimeError):
    pass


@dataclass(frozen=True)
class SchoolYearCourseInterval:
    number: int
    start_date: date
    end_date: date


# Structura anului școlar 2026–2027 pentru județul Cluj.
# Aceste intervale calendaristice NU sunt modulele tehnologice M1–M6.
CLJ_2026_2027_COURSE_INTERVALS: tuple[SchoolYearCourseInterval, ...] = (
    SchoolYearCourseInterval(1, date(2026, 9, 7), date(2026, 10, 23)),
    SchoolYearCourseInterval(2, date(2026, 11, 2), date(2026, 12, 22)),
    SchoolYearCourseInterval(3, date(2027, 1, 11), date(2027, 2, 12)),
    SchoolYearCourseInterval(4, date(2027, 2, 22), date(2027, 4, 23)),
    SchoolYearCourseInterval(5, date(2027, 5, 5), date(2027, 6, 18)),
)


@dataclass(frozen=True)
class ConductIntervalGrade:
    interval_number: int
    grade: Decimal
    awarded_on: date


def validate_conduct_interval_grades(
    grades: Sequence[ConductIntervalGrade],
    *,
    as_of: date | None = None,
) -> tuple[Decimal, ...]:
    """Validează cele 5 note primare la purtare; nu le calculează și nu le modifică."""
    cutoff = as_of or date.today()
    by_interval = {}
    for item in grades:
        if item.interval_number in by_interval:
            raise AnnualClosureError(
                f"Există mai multe note la purtare pentru intervalul {item.interval_number}."
            )
        interval = next(
            (x for x in CLJ_2026_2027_COURSE_INTERVALS if x.number == item.interval_number),
            None,
        )
        if interval is None:
            raise AnnualClosureError(
                f"Interval calendaristic invalid pentru purtare: {item.interval_number}."
            )
        grade = _decimal_grade(item.grade)
        if item.awarded_on < interval.end_date:
            raise AnnualClosureError(
                f"Nota la purtare pentru intervalul {item.interval_number} "
                "nu poate fi acordată înainte de ultima zi a intervalului."
            )
        if item.awarded_on > cutoff:
            raise AnnualClosureError("Data notei la purtare este în viitor.")
        by_interval[item.interval_number] = grade

    completed = [
        interval.number
        for interval in CLJ_2026_2027_COURSE_INTERVALS
        if interval.end_date <= cutoff
    ]
    missing = [number for number in completed if number not in by_interval]
    if missing:
        raise AnnualClosureError(
            "Lipsesc notele la purtare pentru intervalele încheiate: "
            + ", ".join(map(str, missing))
            + "."
        )
    return tuple(
        by_interval[number]
        for number in sorted(by_interval)
    )


# Clasa a IX-a TH, 2026–2027.
# TC/CS: 30 săptămâni conform planului-cadru aplicabil.
# Modulele M1–M4: volumele nominale din curriculumul de specialitate publicat
# de Minister pentru domeniul Turism și alimentație.
IX_TH_2026_2027_ANNUAL_HOURS: Mapping[str, int] = {
    "Limba și literatura română": 90,
    "Limba engleză (L1)": 120,
    "Limba franceză (L2)": 30,
    "Matematică": 60,
    "Fizică": 30,
    "Chimie": 30,
    "Biologie": 30,
    "Istorie": 30,
    "Geografie": 30,
    "Logică, argumentare și comunicare": 30,
    "Religie": 30,
    "Arte vizuale și educație plastică": 30,
    "Educație fizică": 30,
    "Informatică / TIC": 30,
    "M1 – Bazele contabilității": 60,
    "M2 – Etică și comunicare": 60,
    "M3 – Structuri de primire turistică": 60,
    "M4 – Procese și calitate în HoReCa": 120,
}

# M5/M6 nu sunt ghicite: planul/curriculumul fixează plafoanele CDEOȘ,
# iar oferta concretă a școlii trebuie furnizată explicit motorului.
IX_TH_2026_2027_CDEOS_MAX_HOURS: Mapping[str, int] = {
    "M5 – CDEOȘ – Stagii de pregătire practică": 150,
    "M6 – Curriculum pentru aprofundare și inserție profesională": 60,
}

# Configurația efectivă aprobată/comunicată pentru clasa IX TH intensiv engleză.
# Se păstrează separat de planul generic: M5=60h, M6=60h; engleza are
# încă 60h/an pentru regimul intensiv, deci 120h/an în total.
IX_TH_2026_2027_CLASS_CDEOS_HOURS: Mapping[str, int] = {
    "M5 – CDEOȘ – Stagii de pregătire practică": 60,
    "M6 – Curriculum pentru aprofundare și inserție profesională": 60,
}


# Coordonatele sunt aceleași cu structura Excel existentă; motorul doar citește.
EXCEL_CG_LAYOUT: tuple[tuple[str, int], ...] = (
    ("Limba și literatura română", 8),
    ("Limba engleză (L1)", 61),
    ("Limba franceză (L2)", 114),
    ("Matematică", 167),
    ("Fizică", 220),
    ("Chimie", 273),
    ("Biologie", 326),
    ("Istorie", 379),
    ("Geografie", 432),
    ("Logică, argumentare și comunicare", 485),
    ("Informatică / TIC", 538),
    ("Educație fizică", 591),
    ("Religie", 644),
    ("Arte vizuale și educație plastică", 697),
)
EXCEL_MODULE_LAYOUT: tuple[tuple[str, int], ...] = (
    ("M1 – Bazele contabilității", 8),
    ("M2 – Etică și comunicare", 61),
    ("M3 – Structuri de primire turistică", 114),
    ("M4 – Procese și calitate în HoReCa", 167),
    ("M5 – CDEOȘ – Stagii de pregătire practică", 220),
    ("M6 – Curriculum pentru aprofundare și inserție profesională", 273),
)
WEEKLY_HOURS_IX_TH_2026_2027: Mapping[str, Decimal] = {
    "Limba și literatura română": Decimal("3"),
    "Limba engleză (L1)": Decimal("4"),
    "Limba franceză (L2)": Decimal("1"),
    "Matematică": Decimal("2"),
    "Fizică": Decimal("1"),
    "Chimie": Decimal("1"),
    "Biologie": Decimal("1"),
    "Istorie": Decimal("1"),
    "Geografie": Decimal("1"),
    "Logică, argumentare și comunicare": Decimal("1"),
    "Religie": Decimal("1"),
    "Arte vizuale și educație plastică": Decimal("1"),
    "Educație fizică": Decimal("1"),
    "Informatică / TIC": Decimal("1"),
}


def subject_inputs_from_workbook(
    wb,
    student_row: int,
    school_cdeos_hours: Mapping[str, int] | None = None,
) -> tuple[SubjectInput, ...]:
    """Construiește intrările motorului exclusiv prin citire din workbook."""
    if "Cultură Generală" not in wb.sheetnames or "Module Tehnologice" not in wb.sheetnames:
        raise AnnualClosureError("Lipsesc foile obligatorii pentru închiderea anuală.")
    result = []
    for sheet_name, layout, is_module in (
        ("Cultură Generală", EXCEL_CG_LAYOUT, False),
        ("Module Tehnologice", EXCEL_MODULE_LAYOUT, True),
    ):
        ws = wb[sheet_name]
        for name, start_col in layout:
            grades = []
            for k in range(10):
                value = ws.cell(row=student_row, column=start_col + k * 2).value
                if value not in (None, ""):
                    grades.append(_decimal_grade(value))
            unmotivated = motivated = 0
            for k in range(30):
                value = ws.cell(row=student_row, column=start_col + 21 + k).value
                if value in (None, ""):
                    continue
                text = str(value).strip()
                if text.endswith(("m", "M")):
                    motivated += 1
                else:
                    unmotivated += 1
            annual_hours = official_annual_hours(name, school_cdeos_hours)
            result.append(SubjectInput(
                name=name,
                grades=tuple(grades),
                unmotivated_absences=unmotivated,
                motivated_absences=motivated,
                annual_hours=annual_hours,
                weekly_hours=None if is_module else WEEKLY_HOURS_IX_TH_2026_2027[name],
                is_module=is_module,
                # Pentru clasa IX TH toate modulele M1–M6 se încheie la sfârșitul anului.
                ends_during_year=False,
            ))
    return tuple(result)


def build_student_subject_inputs(
    wb,
    elev_info,
    row_resolver,
    school_cdeos_hours: Mapping[str, int] | None = None,
) -> tuple[SubjectInput, ...]:
    """Adaptor fail-closed: validează identitatea, apoi citește situația elevului."""
    student_row = row_resolver(wb, elev_info)
    return subject_inputs_from_workbook(
        wb,
        student_row=student_row,
        school_cdeos_hours=school_cdeos_hours,
    )


def official_annual_hours(subject_name: str, school_cdeos_hours: Mapping[str, int] | None = None) -> int:
    if subject_name in IX_TH_2026_2027_ANNUAL_HOURS:
        return IX_TH_2026_2027_ANNUAL_HOURS[subject_name]
    if subject_name in IX_TH_2026_2027_CDEOS_MAX_HOURS:
        if not school_cdeos_hours or subject_name not in school_cdeos_hours:
            raise AnnualClosureError(
                f"{subject_name}: numărul de ore CDEOȘ aprobat pentru clasă trebuie "
                "furnizat explicit; plafonul din plan nu este presupus ca volum efectiv."
            )
        hours = int(school_cdeos_hours[subject_name])
        maximum = IX_TH_2026_2027_CDEOS_MAX_HOURS[subject_name]
        if hours <= 0 or hours > maximum:
            raise AnnualClosureError(
                f"{subject_name}: {hours} ore este în afara intervalului aprobat 1–{maximum}."
            )
        return hours
    raise AnnualClosureError(f"Nu există volum anual oficial configurat pentru {subject_name!r}.")


@dataclass(frozen=True)
class SubjectInput:
    name: str
    grades: tuple[Decimal, ...]
    unmotivated_absences: int
    motivated_absences: int = 0
    annual_hours: int | None = None
    weekly_hours: Decimal | None = None
    is_module: bool = False
    ends_during_year: bool = False


@dataclass(frozen=True)
class SubjectResult:
    name: str
    raw_average: Decimal
    annual_average: int
    unmotivated_absences: int
    motivated_absences: int
    annual_hours: int
    minimum_grade_reference: int
    has_minimum_grade_reference: bool
    reaches_20_percent: bool
    is_module: bool
    ends_during_year: bool


@dataclass(frozen=True)
class AnnualClosurePreview:
    subjects: tuple[SubjectResult, ...]
    ready_for_final_closure: bool
    readiness_blockers: tuple[str, ...]
    total_unmotivated_absences: int
    total_motivated_absences: int
    total_absences: int
    conduct_base_average: Decimal
    conduct_penalty_points: int
    conduct_penalty_total_absences: int
    conduct_penalty_subject_thresholds: int
    conduct_penalty_rule: str
    conduct_annual_average: Decimal
    final_status: str
    general_average: Decimal | None
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class AnnualClosureSnapshot:
    """Structură imuabilă pregătită pentru audit; nu implică persistență."""
    schema_version: int
    rules_version: str
    generated_at: str
    integrity_sha256: str
    school_year: str
    student_key: str
    subjects: tuple[tuple[str, str, int, int, int], ...]
    interval_conduct_grades: tuple[int, ...]
    total_unmotivated_absences: int
    total_motivated_absences: int
    total_absences: int
    conduct_base_average: str
    conduct_penalty_points: int
    conduct_penalty_total_absences: int
    conduct_penalty_subject_thresholds: int
    conduct_penalty_rule: str
    conduct_annual_average: str
    final_status: str
    general_average: str | None


def build_annual_closure_snapshot(
    *,
    student_key: str,
    preview: AnnualClosurePreview,
    interval_conduct_grades: Sequence[Decimal],
) -> AnnualClosureSnapshot:
    """Construiește snapshotul numai dacă preview-ul este eligibil pentru închidere."""
    key = str(student_key).strip()
    if not key:
        raise AnnualClosureError("Snapshotul anual necesită identificatorul stabil al elevului.")
    if not preview.ready_for_final_closure:
        raise AnnualClosureError(
            "Snapshotul anual nu poate fi construit cât timp există blocaje de închidere."
        )
    if len(interval_conduct_grades) != len(CLJ_2026_2027_COURSE_INTERVALS):
        raise AnnualClosureError("Snapshotul necesită toate cele 5 note la purtare.")
    conduct_grades = tuple(
        int(_decimal_grade(value)) for value in interval_conduct_grades
    )
    subjects = tuple(
        (
            item.name,
            str(item.raw_average),
            item.annual_average,
            item.unmotivated_absences,
            item.motivated_absences,
        )
        for item in preview.subjects
    )
    snapshot = AnnualClosureSnapshot(
        schema_version=2,
        rules_version="etapa-5.6-2026-2027-v1",
        generated_at=datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(timespec="seconds"),
        integrity_sha256="",
        school_year="2026-2027",
        student_key=key,
        subjects=subjects,
        interval_conduct_grades=conduct_grades,
        total_unmotivated_absences=preview.total_unmotivated_absences,
        total_motivated_absences=preview.total_motivated_absences,
        total_absences=preview.total_absences,
        conduct_base_average=str(preview.conduct_base_average),
        conduct_penalty_points=preview.conduct_penalty_points,
        conduct_penalty_total_absences=preview.conduct_penalty_total_absences,
        conduct_penalty_subject_thresholds=preview.conduct_penalty_subject_thresholds,
        conduct_penalty_rule=preview.conduct_penalty_rule,
        conduct_annual_average=str(preview.conduct_annual_average),
        final_status=preview.final_status,
        general_average=None if preview.general_average is None else str(preview.general_average),
    )
    return seal_annual_closure_snapshot(snapshot)


def canonical_snapshot_payload(snapshot: AnnualClosureSnapshot) -> bytes:
    """Reprezentare deterministă; hashul însuși este exclus din materialul semnat."""
    payload = asdict(snapshot)
    payload["integrity_sha256"] = ""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def snapshot_sha256(snapshot: AnnualClosureSnapshot) -> str:
    return hashlib.sha256(canonical_snapshot_payload(snapshot)).hexdigest()


def seal_annual_closure_snapshot(snapshot: AnnualClosureSnapshot) -> AnnualClosureSnapshot:
    return replace(snapshot, integrity_sha256=snapshot_sha256(snapshot))


def verify_annual_closure_snapshot(snapshot: AnnualClosureSnapshot) -> bool:
    expected = snapshot.integrity_sha256
    if not expected or len(expected) != 64:
        return False
    return snapshot_sha256(snapshot) == expected


def _decimal_grade(value) -> Decimal:
    try:
        grade = Decimal(str(value))
    except Exception as exc:
        raise AnnualClosureError(f"Notă invalidă: {value!r}") from exc
    if grade < 1 or grade > 10:
        raise AnnualClosureError(f"Nota {grade} este în afara intervalului 1–10.")
    return grade


def round_annual_subject_average(value: Decimal) -> int:
    """Nota întreagă cea mai apropiată; exact .50 se rotunjește în favoarea elevului."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def minimum_grade_reference(subject: SubjectInput) -> int:
    """Reperul ROFUIP art. 107; „de regulă”, nu prag absolut în toate cazurile."""
    if subject.is_module:
        if subject.annual_hours is None or subject.annual_hours <= 0:
            raise AnnualClosureError(f"{subject.name}: lipsesc orele modulului.")
        # de regulă o notă / 25 ore; minimum absolut menționat: 2
        return max(2, int((subject.annual_hours + 24) // 25))
    if subject.weekly_hours is None or subject.weekly_hours <= 0:
        raise AnnualClosureError(f"{subject.name}: lipsesc orele săptămânale.")
    if subject.weekly_hours < 1:
        return 2
    return max(4, int(subject.weekly_hours) + 3)


def calculate_subject(subject: SubjectInput) -> SubjectResult:
    if not subject.grades:
        raise AnnualClosureError(f"{subject.name}: nu există note pentru încheiere.")
    if subject.annual_hours is None or subject.annual_hours <= 0:
        raise AnnualClosureError(
            f"{subject.name}: lipsește numărul anual validat de ore; "
            "nu poate fi verificat pragul legal de 20%."
        )
    grades = tuple(_decimal_grade(v) for v in subject.grades)
    minimum_reference = minimum_grade_reference(subject)
    raw = sum(grades, Decimal("0")) / Decimal(len(grades))
    annual = round_annual_subject_average(raw)
    reaches_20 = Decimal(subject.unmotivated_absences) >= (
        Decimal(subject.annual_hours) * Decimal("0.20")
    )
    return SubjectResult(
        name=subject.name,
        raw_average=raw,
        annual_average=annual,
        unmotivated_absences=subject.unmotivated_absences,
        motivated_absences=subject.motivated_absences,
        annual_hours=subject.annual_hours,
        minimum_grade_reference=minimum_reference,
        has_minimum_grade_reference=len(grades) >= minimum_reference,
        reaches_20_percent=reaches_20,
        is_module=subject.is_module,
        ends_during_year=subject.ends_during_year,
    )


def calculate_conduct(
    interval_conduct_grades: Sequence[Decimal],
    total_unmotivated: int,
    subject_results: Sequence[SubjectResult],
) -> tuple[Decimal, int, int, int, str, Decimal]:
    """ROFUIP art. 108–109 + Statut art. 28: bază anuală, apoi diminuare pentru absențe."""
    if len(interval_conduct_grades) != len(CLJ_2026_2027_COURSE_INTERVALS):
        raise AnnualClosureError(
            "Închiderea anuală necesită câte o notă la purtare pentru toate cele 5 "
            "intervale de cursuri."
        )
    grades = tuple(_decimal_grade(v) for v in interval_conduct_grades)
    raw_base = sum(grades, Decimal("0")) / Decimal(len(grades))
    rounded_base = Decimal(round_annual_subject_average(raw_base))

    total_steps = total_unmotivated // 20
    subject_threshold_steps = sum(1 for s in subject_results if s.reaches_20_percent)

    # Criteriile legale sunt alternative („sau”). Nu însumăm aceeași nefrecventare
    # de două ori; aplicăm numărul de trepte rezultat din criteriul mai sever.
    penalty = max(total_steps, subject_threshold_steps)
    rule = (
        "TOTAL_ANUAL"
        if total_steps > subject_threshold_steps
        else "PRAG_DISCIPLINE_MODULE"
        if subject_threshold_steps > total_steps
        else "EGAL"
    )
    annual = max(Decimal("1"), rounded_base - Decimal(penalty))
    return rounded_base, penalty, total_steps, subject_threshold_steps, rule, annual


def determine_status(
    subject_results: Sequence[SubjectResult],
    conduct_annual_average: Decimal,
) -> str:
    """Determinare preliminară; situațiile AMÂNAT necesită validări suplimentare."""
    if conduct_annual_average < Decimal("6"):
        return "REPETENT"

    failed_end = [
        s for s in subject_results
        if s.annual_average < 5 and not (s.is_module and s.ends_during_year)
    ]
    failed_modules_during = [
        s for s in subject_results
        if s.annual_average < 5 and s.is_module and s.ends_during_year
    ]

    if len(failed_end) > 2:
        return "REPETENT"
    if failed_end or failed_modules_during:
        return "CORIGENT"
    return "PROMOVAT"


def calculate_general_average(
    subject_results: Sequence[SubjectResult],
    conduct_annual_average: Decimal,
    status: str,
) -> Decimal | None:
    if status != "PROMOVAT":
        return None
    values = [Decimal(s.annual_average) for s in subject_results]
    values.append(conduct_annual_average)
    return (sum(values, Decimal("0")) / Decimal(len(values))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def preview_annual_closure(
    subjects: Sequence[SubjectInput],
    motivated_absences: int,
    interval_conduct_grades: Sequence[Decimal],
) -> AnnualClosurePreview:
    results = tuple(calculate_subject(s) for s in subjects)
    total_unmotivated = sum(s.unmotivated_absences for s in results)
    subject_motivated = sum(s.motivated_absences for s in results)
    if motivated_absences != subject_motivated:
        raise AnnualClosureError(
            "Totalul absențelor motivate nu corespunde sumei pe discipline/module."
        )
    total_absences = total_unmotivated + motivated_absences
    base, penalty, penalty_total, penalty_subjects, penalty_rule, conduct = calculate_conduct(
        interval_conduct_grades, total_unmotivated, results
    )
    blockers = []
    for result in results:
        total_subject_absences = result.unmotivated_absences + result.motivated_absences
        if (
            total_subject_absences >= result.annual_hours * 0.50
            and not result.has_minimum_grade_reference
        ):
            blockers.append(
                f"{result.name}: cel puțin 50% absențe și număr insuficient de note – AMÂNAT."
            )
    status = "AMÂNAT" if blockers else determine_status(results, conduct)
    general = calculate_general_average(results, conduct, status)

    readiness = list(blockers)
    for result in results:
        if not result.has_minimum_grade_reference:
            readiness.append(
                f"{result.name}: numărul de note este sub reperul ROFUIP configurat "
                f"({result.minimum_grade_reference}). Art. 117 poate impune declararea AMÂNAT "
                "și în alte situații decât pragul de 50% absențe; cazul trebuie validat "
                "administrativ înainte de închiderea definitivă."
            )
    # Art. 117 include și cauze administrative care nu pot fi deduse numai din catalog
    # (scutire de frecvență, studii/bursă în străinătate, alte cauze neimputabile etc.).
    # Motorul nu inventează aceste stări; ele vor necesita o declarație administrativă
    # explicită înaintea snapshotului definitiv.
    # CORIGENT/REPETENT/AMÂNAT sunt rezultate școlare valide, nu erori tehnice.
    # Doar lipsurile/condițiile neverificate blochează persistența definitivă.
    readiness = tuple(dict.fromkeys(readiness))
    return AnnualClosurePreview(
        subjects=results,
        ready_for_final_closure=not readiness,
        readiness_blockers=readiness,
        total_unmotivated_absences=total_unmotivated,
        total_motivated_absences=motivated_absences,
        total_absences=total_absences,
        conduct_base_average=base,
        conduct_penalty_points=penalty,
        conduct_penalty_total_absences=penalty_total,
        conduct_penalty_subject_thresholds=penalty_subjects,
        conduct_penalty_rule=penalty_rule,
        conduct_annual_average=conduct,
        final_status=status,
        general_average=general,
        blockers=tuple(blockers),
    )


@dataclass(frozen=True)
class AnnualFinalizationSubjectResult:
    """Rezultat ulterior pentru o disciplină; nu modifică snapshotul inițial."""
    subject_name: str
    source_status: str
    result_type: str
    resulting_annual_average: int


@dataclass(frozen=True)
class AnnualFinalizationRecord:
    """Act imuabil care definitivează ulterior o situație anuală neîncheiată."""
    schema_version: int
    rules_version: str
    generated_at: str
    integrity_sha256: str
    school_year: str
    student_key: str
    source_snapshot_sha256: str
    source_status: str
    subject_results: tuple[AnnualFinalizationSubjectResult, ...]
    final_status: str
    final_general_average: str | None
    finalized_on: str


_ALLOWED_FINALIZATION_SOURCE_STATUSES = {"CORIGENT", "AMANAT"}
_ALLOWED_FINALIZATION_RESULT_TYPES = {
    "INCHEIERE_SITUATIE",
    "CORIGENTA",
    "REEXAMINARE",
}
_ALLOWED_FINAL_STATUSES = {"PROMOVAT", "REPETENT"}


def canonical_finalization_payload(record: AnnualFinalizationRecord) -> bytes:
    payload = asdict(record)
    payload["integrity_sha256"] = ""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def finalization_sha256(record: AnnualFinalizationRecord) -> str:
    return hashlib.sha256(canonical_finalization_payload(record)).hexdigest()


def seal_annual_finalization_record(
    record: AnnualFinalizationRecord,
) -> AnnualFinalizationRecord:
    return replace(record, integrity_sha256=finalization_sha256(record))


def verify_annual_finalization_record(record: AnnualFinalizationRecord) -> bool:
    expected = str(record.integrity_sha256 or "")
    return len(expected) == 64 and finalization_sha256(record) == expected


def build_annual_finalization_record(
    *,
    source_snapshot: AnnualClosureSnapshot,
    subject_results: Sequence[AnnualFinalizationSubjectResult],
    final_status: str,
    final_general_average: Decimal | None,
    finalized_on: date,
) -> AnnualFinalizationRecord:
    """Construiește actul ulterior fără a modifica snapshotul sursă.

    Regulile juridice care produc rezultatele examenelor vor fi implementate
    separat. Aici validăm numai identitatea, legătura criptografică și forma
    rezultatului deja stabilit.
    """
    if not verify_annual_closure_snapshot(source_snapshot):
        raise AnnualClosureError("Snapshotul sursă nu trece verificarea SHA-256.")
    if source_snapshot.final_status not in _ALLOWED_FINALIZATION_SOURCE_STATUSES:
        raise AnnualClosureError(
            "Snapshotul sursă nu reprezintă o situație care necesită definitivare ulterioară."
        )
    if final_status not in _ALLOWED_FINAL_STATUSES:
        raise AnnualClosureError("Statutul definitiv solicitat nu este permis.")
    if not subject_results:
        raise AnnualClosureError("Actul de definitivare necesită cel puțin un rezultat ulterior.")

    seen = set()
    normalized = []
    for item in subject_results:
        name = str(item.subject_name).strip()
        if not name:
            raise AnnualClosureError("Disciplina din actul de definitivare nu poate fi goală.")
        if name in seen:
            raise AnnualClosureError(
                f"Disciplina {name!r} apare de mai multe ori în același act de definitivare."
            )
        seen.add(name)
        if item.source_status not in _ALLOWED_FINALIZATION_SOURCE_STATUSES:
            raise AnnualClosureError("Starea sursă a rezultatului ulterior este invalidă.")
        if item.result_type not in _ALLOWED_FINALIZATION_RESULT_TYPES:
            raise AnnualClosureError("Tipul rezultatului ulterior este invalid.")
        if not isinstance(item.resulting_annual_average, int) or isinstance(
            item.resulting_annual_average, bool
        ) or not 1 <= item.resulting_annual_average <= 10:
            raise AnnualClosureError(
                f"{name}: media anuală rezultată trebuie să fie un întreg între 1 și 10."
            )
        normalized.append(
            AnnualFinalizationSubjectResult(
                subject_name=name,
                source_status=item.source_status,
                result_type=item.result_type,
                resulting_annual_average=item.resulting_annual_average,
            )
        )

    if final_status == "PROMOVAT" and final_general_average is None:
        raise AnnualClosureError("Statutul PROMOVAT necesită media generală definitivă.")
    if final_status != "PROMOVAT" and final_general_average is not None:
        raise AnnualClosureError(
            "Media generală definitivă nu se fixează pentru un statut nepromovat."
        )
    general = None
    if final_general_average is not None:
        value = Decimal(str(final_general_average))
        if value < Decimal("1") or value > Decimal("10"):
            raise AnnualClosureError("Media generală definitivă este în afara intervalului 1–10.")
        general = str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    record = AnnualFinalizationRecord(
        schema_version=1,
        rules_version="etapa-5.6-finalizare-2026-2027-v1",
        generated_at=datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(timespec="seconds"),
        integrity_sha256="",
        school_year=source_snapshot.school_year,
        student_key=source_snapshot.student_key,
        source_snapshot_sha256=source_snapshot.integrity_sha256,
        source_status=source_snapshot.final_status,
        subject_results=tuple(normalized),
        final_status=final_status,
        final_general_average=general,
        finalized_on=finalized_on.isoformat(),
    )
    return seal_annual_finalization_record(record)
