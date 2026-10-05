"""Persistență fail-closed pentru snapshoturile anuale Etapa 5.6.

Registrul este separat de datele primare. O închidere existentă nu se suprascrie.
Publicarea în repository-ul privat rămâne responsabilitatea aplicației, după
verificarea locală a registrului.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from annual_closure_engine import (
    AnnualClosureSnapshot,
    verify_annual_closure_snapshot,
)

ANNUAL_CLOSURE_REGISTRY_FILE = "registru_inchidere_anuala_2026_2027.json"
SCHOOL_YEAR = "2026-2027"
REGISTRY_SCHEMA_VERSION = 1


class AnnualClosureStorageError(RuntimeError):
    pass


def empty_annual_closure_registry() -> dict[str, Any]:
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "school_year": SCHOOL_YEAR,
        "snapshots": {},
    }


def load_annual_closure_registry(path: str | Path = ANNUAL_CLOSURE_REGISTRY_FILE) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return empty_annual_closure_registry()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AnnualClosureStorageError("Registrul anual nu poate fi citit în siguranță.") from exc
    if not isinstance(data, dict):
        raise AnnualClosureStorageError("Format invalid pentru registrul anual.")
    if data.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise AnnualClosureStorageError("Versiune necunoscută a registrului anual.")
    if data.get("school_year") != SCHOOL_YEAR:
        raise AnnualClosureStorageError("Registrul anual aparține altui an școlar.")
    if not isinstance(data.get("snapshots"), dict):
        raise AnnualClosureStorageError("Registrul anual nu conține o colecție validă de snapshoturi.")
    return data


def _snapshot_dict(snapshot: AnnualClosureSnapshot) -> dict[str, Any]:
    if not verify_annual_closure_snapshot(snapshot):
        raise AnnualClosureStorageError("Snapshotul anual nu trece verificarea SHA-256.")
    return asdict(snapshot)


def register_annual_closure_once(
    snapshot: AnnualClosureSnapshot,
    path: str | Path = ANNUAL_CLOSURE_REGISTRY_FILE,
) -> dict[str, Any]:
    """Create-once: nu permite înlocuirea implicită a unei închideri existente."""
    key = str(snapshot.student_key).strip()
    if not key:
        raise AnnualClosureStorageError("Lipsește identificatorul stabil al elevului.")
    payload = _snapshot_dict(snapshot)
    registry = load_annual_closure_registry(path)
    snapshots = registry["snapshots"]
    if key in snapshots:
        existing = snapshots[key]
        if existing == payload:
            return registry  # retry idempotent; nu rescriem.
        raise AnnualClosureStorageError(
            "Elevul are deja o închidere anuală persistentă. "
            "Corectarea necesită un flux separat și auditabil."
        )

    updated = {
        **registry,
        "snapshots": {**snapshots, key: payload},
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_suffix(target.suffix + ".bak")

    fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(updated, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        check = json.loads(Path(temp_name).read_text(encoding="utf-8"))
        stored = check.get("snapshots", {}).get(key)
        if stored != payload:
            raise AnnualClosureStorageError("Verificarea registrului temporar a eșuat.")
        try:
            stored_snapshot = AnnualClosureSnapshot(**stored)
        except Exception as exc:
            raise AnnualClosureStorageError("Snapshotul temporar nu poate fi reconstruit.") from exc
        if not verify_annual_closure_snapshot(stored_snapshot):
            raise AnnualClosureStorageError("SHA-256 al snapshotului temporar este invalid.")
        if target.exists():
            shutil.copy2(target, backup)
        os.replace(temp_name, target)
    except Exception:
        try:
            Path(temp_name).unlink(missing_ok=True)
        except Exception:
            pass
        raise

    final = load_annual_closure_registry(target)
    final_payload = final["snapshots"].get(key)
    if final_payload != payload:
        raise AnnualClosureStorageError("Verificarea după scriere a registrului anual a eșuat.")
    try:
        final_snapshot = AnnualClosureSnapshot(**final_payload)
    except Exception as exc:
        raise AnnualClosureStorageError("Snapshotul final nu poate fi reconstruit.") from exc
    if not verify_annual_closure_snapshot(final_snapshot):
        raise AnnualClosureStorageError("SHA-256 al snapshotului final este invalid.")
    return final
