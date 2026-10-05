"""Registru privat create-once pentru situația școlară definitivă.

Nu modifică Excelul, gestiunea elevilor sau snapshoturile de la încheierea
cursurilor. Pentru această etapă pot deveni definitive direct numai situațiile
PROMOVAT și REPETENT. CORIGENT și AMANAT necesită un act ulterior auditabil.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from annual_closure_engine import AnnualClosureSnapshot, verify_annual_closure_snapshot

FINAL_STATUS_PRIVATE_REGISTRY_PATH = "inchideri_anuale/registru_situatie_definitiva_2026_2027.json"
SCHOOL_YEAR = "2026-2027"
SCHEMA_VERSION = 1
DIRECT_FINAL_STATUSES = frozenset({"PROMOVAT", "REPETENT"})


class FinalStatusStorageError(RuntimeError):
    pass


class FinalStatusPersistenceUncertainError(FinalStatusStorageError):
    pass


def _empty_registry() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "school_year": SCHOOL_YEAR, "students": {}}


def _canonical(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _entry_from_snapshot(snapshot: AnnualClosureSnapshot) -> dict[str, Any]:
    if not verify_annual_closure_snapshot(snapshot):
        raise FinalStatusStorageError("Snapshotul de închidere nu trece verificarea SHA-256.")
    status = str(snapshot.final_status).strip().upper()
    if status not in DIRECT_FINAL_STATUSES:
        raise FinalStatusStorageError(
            f"Situația {status or 'NECUNOSCUTĂ'} nu poate deveni definitivă direct. "
            "Este necesar un act ulterior auditabil."
        )
    payload = {
        "student_key": str(snapshot.student_key).strip(),
        "source_closure_sha256": str(snapshot.integrity_sha256),
        "final_status": status,
        "general_average": snapshot.general_average,
    }
    payload["integrity_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def _validate_registry(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise FinalStatusStorageError("Format invalid pentru registrul situațiilor definitive.")
    if data.get("schema_version") != SCHEMA_VERSION or data.get("school_year") != SCHOOL_YEAR:
        raise FinalStatusStorageError("Registrul situațiilor definitive are versiune/an școlar invalid.")
    students = data.get("students")
    if not isinstance(students, dict):
        raise FinalStatusStorageError("Registrul situațiilor definitive nu conține elevi valizi.")
    for key, entry in students.items():
        if not isinstance(entry, dict) or str(entry.get("student_key", "")).strip() != str(key).strip():
            raise FinalStatusStorageError(f"Înregistrare definitivă invalidă pentru {key!r}.")
        check = {k: entry.get(k) for k in ("student_key", "source_closure_sha256", "final_status", "general_average")}
        expected = hashlib.sha256(_canonical(check)).hexdigest()
        if entry.get("integrity_sha256") != expected:
            raise FinalStatusStorageError(f"SHA-256 invalid pentru situația definitivă a elevului {key!r}.")
        if str(entry.get("final_status", "")).upper() not in DIRECT_FINAL_STATUSES:
            raise FinalStatusStorageError(f"Statut definitiv direct nepermis pentru elevul {key!r}.")


def load_private_final_status_registry() -> tuple[dict[str, Any], str | None]:
    try:
        from document_storage import private_read
        raw, sha = private_read(FINAL_STATUS_PRIVATE_REGISTRY_PATH)
    except Exception as exc:
        raise FinalStatusStorageError("Registrul privat al situațiilor definitive nu poate fi citit.") from exc
    if raw is None:
        return _empty_registry(), None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FinalStatusStorageError("Registrul privat al situațiilor definitive este corupt.") from exc
    _validate_registry(data)
    return data, sha


def persist_private_final_status_batch_once(
    snapshots: Mapping[str, AnnualClosureSnapshot],
    expected_student_keys: set[str],
) -> dict[str, Any]:
    """Publică situația definitivă a clasei într-o singură scriere privată.

    Fail-closed: setul elevilor trebuie să coincidă exact, toate snapshoturile
    trebuie să fie valide și direct definitive, iar orice conflict blochează lotul.
    """
    expected = {str(k).strip() for k in expected_student_keys}
    actual = {str(k).strip() for k in snapshots}
    if not expected or actual != expected:
        raise FinalStatusStorageError("Setul snapshoturilor nu corespunde exact clasei.")

    entries: dict[str, dict[str, Any]] = {}
    for key in sorted(expected):
        snapshot = snapshots[key]
        if str(snapshot.student_key).strip() != key:
            raise FinalStatusStorageError(f"Cheia snapshotului nu corespunde elevului {key!r}.")
        entries[key] = _entry_from_snapshot(snapshot)

    registry, registry_sha = load_private_final_status_registry()
    existing = registry["students"]
    conflicts = [key for key, entry in entries.items() if key in existing and existing[key] != entry]
    if conflicts:
        raise FinalStatusStorageError(
            "Situația definitivă este blocată: există înregistrări diferite pentru " + ", ".join(conflicts)
        )
    additions = {key: entry for key, entry in entries.items() if key not in existing}
    if not additions:
        return registry

    updated = {**registry, "students": {**existing, **additions}}
    _validate_registry(updated)
    raw = json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    try:
        from document_storage import private_write
        private_write(
            FINAL_STATUS_PRIVATE_REGISTRY_PATH,
            raw,
            expected_sha=registry_sha,
            message="Înregistrare situație școlară definitivă 2026-2027",
        )
    except Exception as exc:
        raise FinalStatusStorageError("Situația definitivă nu a putut fi publicată în registrul privat.") from exc

    try:
        final, _ = load_private_final_status_registry()
    except Exception as exc:
        raise FinalStatusPersistenceUncertainError(
            "Publicarea poate fi deja efectuată, dar confirmarea nu a putut fi citită. "
            "Nu repetați automat operația."
        ) from exc
    if final != updated:
        raise FinalStatusStorageError("Verificarea registrului definitiv după publicare a eșuat.")
    return final
