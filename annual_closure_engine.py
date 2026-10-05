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

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence


class AnnualClosureError(RuntimeError):
    pass


# Clasa a IX-a TH, 2026–2027.
# TC/CS: 30 săptămâni conform planului-cadru aplicabil.
# Modulele M1–M4: volumele nominale din curriculumul de specialitate publicat
# de Minister pentru domeniul Turism și alimentație.
IX_TH_2026_2027_ANNUAL_HOURS: Mapping[str, int] = {
    "Limba și literatura română": 90,
    "Limba engleză (L1)": 60,
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
    "M6 – Curriculum pentru aprofundare și inserție profesională": 30,
}


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
    annual_hours: int | None
    is_module: bool = False
    ends_during_year: bool = False


@dataclass(frozen=True)
class SubjectResult:
    name: str
    raw_average: Decimal
    annual_average: int
    unmotivated_absences: int
    annual_hours: int
    reaches_20_percent: bool
    is_module: bool
    ends_during_year: bool


@dataclass(frozen=True)
class AnnualClosurePreview:
    subjects: tuple[SubjectResult, ...]
    total_unmotivated_absences: int
    total_motivated_absences: int
    total_absences: int
    conduct_base_average: Decimal
    conduct_penalty_points: int
    conduct_annual_average: Decimal
    final_status: str
    general_average: Decimal | None
    blockers: tuple[str, ...]


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


def calculate_subject(subject: SubjectInput) -> SubjectResult:
    if not subject.grades:
        raise AnnualClosureError(f"{subject.name}: nu există note pentru încheiere.")
    if subject.annual_hours is None or subject.annual_hours <= 0:
        raise AnnualClosureError(
            f"{subject.name}: lipsește numărul anual validat de ore; "
            "nu poate fi verificat pragul legal de 20%."
        )
    grades = tuple(_decimal_grade(v) for v in subject.grades)
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
        annual_hours=subject.annual_hours,
        reaches_20_percent=reaches_20,
        is_module=subject.is_module,
        ends_during_year=subject.ends_during_year,
    )


def calculate_conduct(
    interval_conduct_grades: Sequence[Decimal],
    total_unmotivated: int,
    subject_results: Sequence[SubjectResult],
) -> tuple[Decimal, int, Decimal]:
    """Media de bază la purtare, apoi diminuarea legală pentru nefrecventare."""
    if not interval_conduct_grades:
        raise AnnualClosureError(
            "Lipsesc notele la purtare acordate pentru intervalele de cursuri."
        )
    grades = tuple(_decimal_grade(v) for v in interval_conduct_grades)
    raw_base = sum(grades, Decimal("0")) / Decimal(len(grades))
    # ROFUIP art. 109: și la purtare se încheie o singură medie anuală,
    # rotunjită la întregul cel mai apropiat; .50 în favoarea elevului.
    rounded_base = Decimal(round_annual_subject_average(raw_base))

    total_steps = total_unmotivated // 20
    subject_threshold_steps = sum(1 for s in subject_results if s.reaches_20_percent)

    # „sau” = criterii alternative pentru diminuare; folosim sancțiunea mai severă,
    # fără a dubla aceleași absențe prin însumarea celor două criterii.
    penalty = max(total_steps, subject_threshold_steps)
    annual = max(Decimal("1"), rounded_base - Decimal(penalty))
    return rounded_base, penalty, annual


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
    total_absences = total_unmotivated + motivated_absences
    base, penalty, conduct = calculate_conduct(
        interval_conduct_grades, total_unmotivated, results
    )
    status = determine_status(results, conduct)
    general = calculate_general_average(results, conduct, status)
    return AnnualClosurePreview(
        subjects=results,
        total_unmotivated_absences=total_unmotivated,
        total_motivated_absences=motivated_absences,
        total_absences=total_absences,
        conduct_base_average=base,
        conduct_penalty_points=penalty,
        conduct_annual_average=conduct,
        final_status=status,
        general_average=general,
        blockers=(),
    )
