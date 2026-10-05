"""Stocare separată pentru notele la purtare pe intervale, anul 2026–2027."""
from __future__ import annotations

import datetime
import json
import os
import shutil
from zoneinfo import ZoneInfo

from annual_closure_engine import CLJ_2026_2027_COURSE_INTERVALS

REGISTRY_FILE = "registru_purtare_2026_2027.json"


class ConductStorageError(RuntimeError):
    pass


def _empty_registry():
    return {"schema_version": 1, "school_year": "2026-2027", "grades": []}


def load_conduct_registry(path: str = REGISTRY_FILE):
    if not os.path.exists(path):
        return _empty_registry()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        raise ConductStorageError("Registrul notelor la purtare nu poate fi citit.") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("school_year") != "2026-2027"
        or not isinstance(data.get("grades"), list)
    ):
        raise ConductStorageError("Structura registrului notelor la purtare este invalidă.")
    return data


def save_conduct_grade(
    *,
    student_key: str,
    interval_number: int,
    grade: int,
    awarded_on: str,
    path: str = REGISTRY_FILE,
):
    key = str(student_key).strip()
    if not key:
        raise ConductStorageError("Identificatorul elevului lipsește.")
    if not isinstance(grade, int) or isinstance(grade, bool) or not 1 <= grade <= 10:
        raise ConductStorageError("Nota la purtare trebuie să fie un număr întreg între 1 și 10.")

    interval = next(
        (item for item in CLJ_2026_2027_COURSE_INTERVALS if item.number == interval_number),
        None,
    )
    if interval is None:
        raise ConductStorageError("Intervalul de cursuri este invalid.")
    try:
        awarded_date = datetime.date.fromisoformat(awarded_on)
    except Exception as exc:
        raise ConductStorageError("Data acordării notei este invalidă.") from exc
    today_ro = datetime.datetime.now(ZoneInfo("Europe/Bucharest")).date()
    if awarded_date < interval.end_date:
        raise ConductStorageError("Nota nu poate fi acordată înainte de încheierea intervalului.")
    if awarded_date > today_ro:
        raise ConductStorageError("Nota nu poate avea o dată viitoare.")

    data = load_conduct_registry(path)
    if any(
        str(item.get("student_key", "")).strip() == key
        and int(item.get("interval_number", -1)) == interval_number
        for item in data["grades"]
    ):
        raise ConductStorageError(
            "Există deja o notă la purtare pentru acest elev și acest interval. "
            "Registrul nu permite suprascrierea tăcută."
        )

    record = {
        "student_key": key,
        "interval_number": interval_number,
        "grade": grade,
        "awarded_on": awarded_date.isoformat(),
        "recorded_at": datetime.datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(timespec="seconds"),
    }
    updated = dict(data)
    updated["grades"] = list(data["grades"]) + [record]

    temp_path = path + ".tmp"
    backup_path = path + ".bak"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(updated, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        with open(temp_path, "r", encoding="utf-8") as handle:
            if json.load(handle) != updated:
                raise ConductStorageError("Verificarea registrului temporar a eșuat.")
        if os.path.exists(path):
            shutil.copy2(path, backup_path)
        os.replace(temp_path, path)
    except Exception as exc:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        if isinstance(exc, ConductStorageError):
            raise
        raise ConductStorageError("Nota la purtare nu a putut fi salvată.") from exc
    return record


def conduct_grades_for_student(student_key: str, path: str = REGISTRY_FILE):
    """Returnează cele 5 note în ordinea intervalelor; fail-closed dacă setul e incomplet."""
    key = str(student_key).strip()
    data = load_conduct_registry(path)
    rows = [
        item for item in data["grades"]
        if str(item.get("student_key", "")).strip() == key
    ]
    by_interval = {}
    for item in rows:
        number = int(item.get("interval_number", -1))
        if number in by_interval:
            raise ConductStorageError(
                f"Există înregistrări duplicate pentru intervalul {number}."
            )
        by_interval[number] = item
    expected = {item.number for item in CLJ_2026_2027_COURSE_INTERVALS}
    if set(by_interval) != expected:
        missing = sorted(expected.difference(by_interval))
        extra = sorted(set(by_interval).difference(expected))
        details = []
        if missing:
            details.append("lipsesc intervalele " + ", ".join(map(str, missing)))
        if extra:
            details.append("intervale invalide " + ", ".join(map(str, extra)))
        raise ConductStorageError(
            "Situația la purtare nu este completă pentru închiderea anuală: "
            + "; ".join(details)
            + "."
        )
    return tuple(
        int(by_interval[number]["grade"])
        for number in sorted(expected)
    )
