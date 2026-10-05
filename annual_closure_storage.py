"""Persistență fail-closed pentru snapshoturile de închidere a cursurilor, Etapa 5.6.

Registrul este separat de datele primare. O închidere existentă nu se suprascrie.
Publicarea în repository-ul privat rămâne responsabilitatea aplicației, după
verificarea locală a registrului.
"""
from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from annual_closure_engine import (
    AnnualClosureSnapshot,
    verify_annual_closure_snapshot,
)

ANNUAL_CLOSURE_REGISTRY_FILE = "registru_inchidere_anuala_2026_2027.json"
SCHOOL_YEAR = "2026-2027"
REGISTRY_SCHEMA_VERSION = 1


class AnnualClosureStorageError(RuntimeError):
    pass


class AnnualClosurePersistenceUncertainError(AnnualClosureStorageError):
    """Scrierea poate fi deja efectuată; este interzis retry-ul automat."""
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


def _fsync_directory(directory: Path) -> None:
    """Persistă metadatele rename-ului pe sisteme POSIX; fail-closed dacă fsync e disponibil."""
    if os.name != "posix":
        return
    fd = os.open(str(directory), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def _exclusive_registry_lock(target: Path) -> Iterator[None]:
    """Lock fail-closed: un al doilea writer trebuie să reîncerce, nu să suprascrie."""
    lock = target.with_suffix(target.suffix + ".lock")
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise AnnualClosureStorageError(
            "Registrul anual este deja în curs de actualizare. Reîncercați operația."
        ) from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"pid={os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        try:
            lock.unlink(missing_ok=True)
            _fsync_directory(target.parent)
        except Exception:
            # Eliberarea lockului nu trebuie să mascheze o eroare anterioară.
            pass


def _write_verified_json_temp(
    data: dict[str, Any],
    *,
    directory: Path,
    prefix: str,
) -> str:
    fd, temp_name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=str(directory))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        return temp_name
    except Exception:
        try:
            Path(temp_name).unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _atomic_backup(target: Path, backup: Path) -> None:
    """Copiază versiunea anterioară în backup fără a lăsa un .bak parțial."""
    previous = json.loads(target.read_text(encoding="utf-8"))
    temp_name = _write_verified_json_temp(
        previous,
        directory=target.parent,
        prefix=backup.name + ".",
    )
    try:
        if json.loads(Path(temp_name).read_text(encoding="utf-8")) != previous:
            raise AnnualClosureStorageError("Verificarea backupului temporar a eșuat.")
        os.replace(temp_name, backup)
        _fsync_directory(target.parent)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def register_annual_closure_once(
    snapshot: AnnualClosureSnapshot,
    path: str | Path = ANNUAL_CLOSURE_REGISTRY_FILE,
) -> dict[str, Any]:
    """Create-once: nu permite înlocuirea implicită a unei închideri existente."""
    key = str(snapshot.student_key).strip()
    if not key:
        raise AnnualClosureStorageError("Lipsește identificatorul stabil al elevului.")
    payload = _snapshot_dict(snapshot)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with _exclusive_registry_lock(target):
        # Citirea are loc DUPĂ obținerea lockului: elimină lost-update între writeri.
        registry = load_annual_closure_registry(target)
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
        backup = target.with_suffix(target.suffix + ".bak")
        temp_name = _write_verified_json_temp(
            updated,
            directory=target.parent,
            prefix=target.name + ".",
        )
        try:
            check = json.loads(Path(temp_name).read_text(encoding="utf-8"))
            stored = check.get("snapshots", {}).get(key)
            if stored != payload:
                raise AnnualClosureStorageError("Verificarea registrului temporar a eșuat.")
            try:
                stored_snapshot = AnnualClosureSnapshot(**stored)
            except Exception as exc:
                raise AnnualClosureStorageError(
                    "Snapshotul temporar nu poate fi reconstruit."
                ) from exc
            if not verify_annual_closure_snapshot(stored_snapshot):
                raise AnnualClosureStorageError("SHA-256 al snapshotului temporar este invalid.")

            if target.exists():
                _atomic_backup(target, backup)
            os.replace(temp_name, target)
            _fsync_directory(target.parent)
        except Exception:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except Exception:
                pass
            raise

        final = load_annual_closure_registry(target)
        final_payload = final["snapshots"].get(key)
        if final_payload != payload:
            raise AnnualClosureStorageError(
                "Verificarea după scriere a registrului anual a eșuat."
            )
        try:
            final_snapshot = AnnualClosureSnapshot(**final_payload)
        except Exception as exc:
            raise AnnualClosureStorageError(
                "Snapshotul final nu poate fi reconstruit."
            ) from exc
        if not verify_annual_closure_snapshot(final_snapshot):
            raise AnnualClosureStorageError("SHA-256 al snapshotului final este invalid.")
        return final


# Destinația privată este separată atât de catalogul primar, cât și de documentele școlare.
ANNUAL_CLOSURE_PRIVATE_ROOT = "inchideri_anuale"
ANNUAL_CLOSURE_PRIVATE_REGISTRY_PATH = (
    f"{ANNUAL_CLOSURE_PRIVATE_ROOT}/registru_inchidere_anuala_2026_2027.json"
)


def serialize_annual_closure_registry(registry: dict[str, Any]) -> bytes:
    """Serializează determinist registrul validat, fără a-l publica."""
    if not isinstance(registry, dict):
        raise AnnualClosureStorageError("Registrul anual privat este invalid.")
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise AnnualClosureStorageError("Versiune invalidă pentru registrul anual privat.")
    if registry.get("school_year") != SCHOOL_YEAR:
        raise AnnualClosureStorageError("An școlar invalid pentru registrul anual privat.")
    if not isinstance(registry.get("snapshots"), dict):
        raise AnnualClosureStorageError("Colecția de snapshoturi private este invalidă.")

    for key, payload in registry["snapshots"].items():
        if not str(key).strip() or not isinstance(payload, dict):
            raise AnnualClosureStorageError("Înregistrare anuală privată invalidă.")
        try:
            snapshot = AnnualClosureSnapshot(**payload)
        except Exception as exc:
            raise AnnualClosureStorageError(
                "Un snapshot din registrul privat nu poate fi reconstruit."
            ) from exc
        if str(snapshot.student_key).strip() != str(key).strip():
            raise AnnualClosureStorageError(
                "Cheia elevului nu corespunde snapshotului din registrul privat."
            )
        if not verify_annual_closure_snapshot(snapshot):
            raise AnnualClosureStorageError(
                "Un snapshot din registrul privat nu trece verificarea SHA-256."
            )

    return (
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def load_private_annual_closure_registry() -> tuple[dict[str, Any], str | None]:
    """Citește exclusiv registrul anual din repository-ul privat existent."""
    try:
        from document_storage import private_read
        raw, sha = private_read(ANNUAL_CLOSURE_PRIVATE_REGISTRY_PATH)
    except Exception as exc:
        raise AnnualClosureStorageError(
            "Registrul privat al închiderilor anuale nu poate fi citit."
        ) from exc
    if raw is None:
        return empty_annual_closure_registry(), None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise AnnualClosureStorageError(
            "Registrul privat al închiderilor anuale este corupt."
        ) from exc
    # Validarea completă include verificarea SHA-256 a fiecărui snapshot.
    serialize_annual_closure_registry(data)
    return data, sha


def publish_private_annual_closure_registry(
    registry: dict[str, Any],
    *,
    expected_sha: str | None,
) -> str | None:
    """Publică numai în zona privată dedicată, cu protecția SHA deja folosită de proiect."""
    raw = serialize_annual_closure_registry(registry)
    try:
        from document_storage import private_write
        return private_write(
            ANNUAL_CLOSURE_PRIVATE_REGISTRY_PATH,
            raw,
            expected_sha=expected_sha,
            message="Actualizare registru privat închideri anuale 2026-2027",
        )
    except Exception as exc:
        raise AnnualClosureStorageError(
            "Registrul privat al închiderilor anuale nu a putut fi publicat."
        ) from exc


def persist_private_annual_closure_once(
    snapshot: AnnualClosureSnapshot,
) -> dict[str, Any]:
    """Persistă o singură dată snapshotul de la încheierea cursurilor, fără suprascriere.

    Operația este intenționat independentă de interfața catalogului și de datele
    primare. Conflictul de versiune al registrului privat este tratat fail-closed.
    """
    key = str(snapshot.student_key).strip()
    if not key:
        raise AnnualClosureStorageError("Lipsește identificatorul stabil al elevului.")
    payload = _snapshot_dict(snapshot)

    registry, registry_sha = load_private_annual_closure_registry()
    snapshots = registry["snapshots"]

    if key in snapshots:
        if snapshots[key] == payload:
            # Retry idempotent: nu publicăm și nu modificăm repository-ul privat.
            return registry
        raise AnnualClosureStorageError(
            "Elevul are deja un snapshot de închidere a situației școlare în registrul privat. "
            "Corectarea necesită un flux separat și auditabil."
        )

    updated = {
        **registry,
        "snapshots": {**snapshots, key: payload},
    }

    # Validăm integral noua stare înainte de orice tentativă de publicare.
    serialize_annual_closure_registry(updated)

    # private_write verifică SHA-ul citit mai sus. Dacă alt writer a modificat
    # registrul între timp, publicarea este refuzată, nu se face merge implicit.
    publish_private_annual_closure_registry(
        updated,
        expected_sha=registry_sha,
    )

    # După PUT, orice eșec de citire este ambiguu: scrierea poate exista deja.
    # Nu transformăm această stare într-un retry automat al operației de scriere.
    try:
        final, _final_sha = load_private_annual_closure_registry()
    except Exception as exc:
        raise AnnualClosurePersistenceUncertainError(
            "Publicarea poate fi deja efectuată, dar confirmarea nu a putut fi citită. "
            "Nu repetați automat închiderea; verificați registrul privat înainte de orice nouă operație."
        ) from exc
    if final != updated:
        raise AnnualClosureStorageError(
            "Verificarea registrului privat după publicare a eșuat."
        )
    if final["snapshots"].get(key) != payload:
        raise AnnualClosureStorageError(
            "Snapshotul anual publicat nu corespunde datelor validate."
        )
    return final



def persist_private_annual_closure_batch_once(
    snapshots: list[AnnualClosureSnapshot] | tuple[AnnualClosureSnapshot, ...],
) -> dict[str, Any]:
    """Publică atomic logic snapshoturile unei clase într-o singură scriere privată.

    Toate snapshoturile sunt validate și toate conflictele sunt detectate înainte
    de publicare. Snapshoturile identice deja existente sunt tratate idempotent.
    """
    if not snapshots:
        raise AnnualClosureStorageError("Lista snapshoturilor clasei este goală.")

    payloads: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        key = str(snapshot.student_key).strip()
        if not key:
            raise AnnualClosureStorageError("Un snapshot nu are identificator stabil de elev.")
        if key in payloads:
            raise AnnualClosureStorageError(
                f"Elevul {key!r} apare de mai multe ori în lotul de închidere."
            )
        payloads[key] = _snapshot_dict(snapshot)

    registry, registry_sha = load_private_annual_closure_registry()
    existing = registry["snapshots"]

    conflicts = [
        key for key, payload in payloads.items()
        if key in existing and existing[key] != payload
    ]
    if conflicts:
        raise AnnualClosureStorageError(
            "Închiderea clasei este blocată: există snapshoturi diferite deja "
            "înregistrate pentru: " + ", ".join(sorted(conflicts))
        )

    additions = {
        key: payload for key, payload in payloads.items()
        if key not in existing
    }
    if not additions:
        return registry

    updated = {
        **registry,
        "snapshots": {**existing, **additions},
    }

    # Validare integrală înainte de unica publicare.
    serialize_annual_closure_registry(updated)
    publish_private_annual_closure_registry(updated, expected_sha=registry_sha)

    try:
        final, _final_sha = load_private_annual_closure_registry()
    except Exception as exc:
        raise AnnualClosurePersistenceUncertainError(
            "Publicarea lotului clasei poate fi deja efectuată, dar confirmarea "
            "nu a putut fi citită. Nu repetați automat operația; verificați "
            "registrul privat înainte de o nouă încercare."
        ) from exc
    if final != updated:
        raise AnnualClosureStorageError(
            "Verificarea registrului privat după publicarea clasei a eșuat."
        )
    return final


def reconcile_private_annual_closure(
    snapshot: AnnualClosureSnapshot,
) -> str:
    """Verificare read-only după o publicare cu rezultat incert.

    Returnează:
      - CONFIRMED: snapshotul există și este identic;
      - ABSENT: elevul nu apare în registrul privat;
      - CONFLICT: elevul apare, dar cu alt snapshot valid.

    Funcția nu scrie și nu modifică registrul privat.
    """
    key = str(snapshot.student_key).strip()
    if not key:
        raise AnnualClosureStorageError("Lipsește identificatorul stabil al elevului.")
    payload = _snapshot_dict(snapshot)

    registry, _registry_sha = load_private_annual_closure_registry()
    existing = registry["snapshots"].get(key)
    if existing is None:
        return "ABSENT"
    if existing == payload:
        return "CONFIRMED"
    return "CONFLICT"
