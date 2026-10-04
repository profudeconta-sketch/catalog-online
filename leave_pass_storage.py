"""Backend Etapa 4E - solicitari si bilete de voie.

Nu modifica datele catalogului. Persistenta este limitata la zona documente_scolare
din repository-ul privat si foloseste control optimist prin SHA.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from zoneinfo import ZoneInfo

from document_storage import (
    DOCUMENT_ROOT, DocumentConflictError, DocumentStorageError,
    normalize_student_key, private_read, private_write,
)
from leave_pass_pdf import generate_leave_pass_pdf

LEAVE_PASS_REGISTRY_PATH = f"{DOCUMENT_ROOT}/registru_bilete_voie.json"
BUCHAREST = ZoneInfo("Europe/Bucharest")
REASONS = {
    "MOTIVE_PERSONALE": "Motive personale",
    "MOTIVE_MEDICALE": "Motive medicale",
}
STATUS_PENDING = "IN_ASTEPTARE"
STATUS_REFUSED = "REFUZATA"
STATUS_EXPIRED = "EXPIRATA"
STATUS_APPROVED = "APROBATA"
REFORMULABLE_STATUSES = {STATUS_PENDING, STATUS_REFUSED, STATUS_EXPIRED}


def _utc_now():
    return dt.datetime.now(dt.timezone.utc)


def _local_now(now_utc=None):
    value = now_utc or _utc_now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(BUCHAREST)


def _parse_departure(request_date, departure_time):
    try:
        day = dt.date.fromisoformat(str(request_date))
        clock = dt.time.fromisoformat(str(departure_time))
    except ValueError as ex:
        raise ValueError("Data sau ora plecării este invalidă.") from ex
    if clock.tzinfo is not None:
        raise ValueError("Ora plecării trebuie transmisă ca oră locală.")
    return dt.datetime.combine(day, clock, tzinfo=BUCHAREST)


def _validate_current_day_future(request_date, departure_time, now_utc=None):
    now_local = _local_now(now_utc)
    if str(request_date) != now_local.date().isoformat():
        raise ValueError("Solicitarea de învoire este permisă exclusiv pentru ziua curentă.")
    departure = _parse_departure(request_date, departure_time)
    if departure <= now_local:
        raise ValueError("Ora solicitată pentru plecare trebuie să fie ulterioară momentului curent.")
    return departure


def load_leave_pass_registry():
    raw, sha = private_read(LEAVE_PASS_REGISTRY_PATH)
    if raw is None:
        return {"schema_version": 1, "requests": []}, None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as ex:
        raise DocumentStorageError("Registrul biletelor de voie este invalid.") from ex
    if data.get("schema_version") != 1 or not isinstance(data.get("requests"), list):
        raise DocumentStorageError("Structura registrului biletelor de voie este invalidă.")
    return data, sha


def save_leave_pass_registry(registry, expected_sha):
    if registry.get("schema_version") != 1 or not isinstance(registry.get("requests"), list):
        raise DocumentStorageError("Registrul biletelor de voie nu poate fi salvat.")
    raw = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    return private_write(
        LEAVE_PASS_REGISTRY_PATH, raw, expected_sha=expected_sha,
        message="Actualizare registru bilete de voie",
    )


def _student_day_matches(registry, student_key, request_date):
    return [
        item for item in registry["requests"]
        if item.get("student_key") == student_key
        and item.get("request_date") == str(request_date)
    ]


def _expire_record_if_needed(record, now_utc=None):
    if record.get("status") != STATUS_PENDING:
        return False
    departure = _parse_departure(record.get("request_date"), record.get("departure_time"))
    if departure <= _local_now(now_utc):
        record["status"] = STATUS_EXPIRED
        record["expired_at_utc"] = (now_utc or _utc_now()).isoformat()
        record["decision_at_utc"] = record["expired_at_utc"]
        return True
    return False


def get_leave_request_for_day(student_rm_pg, request_date=None, refresh_expiry=True):
    student_key = normalize_student_key(student_rm_pg)
    now = _utc_now()
    day = str(request_date or _local_now(now).date().isoformat())
    for _ in range(3):
        registry, sha = load_leave_pass_registry()
        matches = _student_day_matches(registry, student_key, day)
        if len(matches) > 1:
            raise DocumentConflictError("Există mai multe solicitări de învoire pentru același elev și aceeași zi.")
        if not matches:
            return None
        record = matches[0]
        if refresh_expiry and _expire_record_if_needed(record, now):
            try:
                save_leave_pass_registry(registry, sha)
                return dict(record)
            except DocumentConflictError:
                continue
        return dict(record)
    raise DocumentConflictError("Starea solicitării nu a putut fi actualizată în siguranță.")


def submit_or_reformulate_leave_request(*, student_rm_pg, school_year, parent_name,
                                        student_name, departure_time, reason_code,
                                        expected_revision=None):
    parent_name = str(parent_name or "").strip()
    student_name = str(student_name or "").strip()
    if not parent_name or not student_name:
        raise ValueError("Părintele/reprezentantul legal și elevul sunt obligatorii.")
    if reason_code not in REASONS:
        raise ValueError("Motivul învoirii nu este valid.")

    now = _utc_now()
    day = _local_now(now).date().isoformat()
    _validate_current_day_future(day, departure_time, now)
    student_key = normalize_student_key(student_rm_pg)

    for _ in range(3):
        registry, sha = load_leave_pass_registry()
        matches = _student_day_matches(registry, student_key, day)
        if len(matches) > 1:
            raise DocumentConflictError("Există mai multe solicitări pentru același elev și aceeași zi.")

        if matches:
            record = matches[0]
            _expire_record_if_needed(record, now)
            if record.get("status") == STATUS_APPROVED:
                raise DocumentConflictError("Biletul de voie a fost deja aprobat și este definitiv.")
            if record.get("status") not in REFORMULABLE_STATUSES:
                raise DocumentConflictError("Solicitarea nu poate fi reformulată în starea curentă.")
            current_revision = int(record.get("revision", 1))
            if expected_revision is not None and int(expected_revision) != current_revision:
                raise DocumentConflictError("Solicitarea a fost modificată între timp. Reîncărcați forma curentă.")
            record.update({
                "parent_name": parent_name,
                "student_name": student_name,
                "departure_time": str(departure_time),
                "reason_code": reason_code,
                "reason_label": REASONS[reason_code],
                "status": STATUS_PENDING,
                "revision": current_revision + 1,
                "transmitted_at_utc": now.isoformat(),
                "decision_at_utc": None,
                "refused_at_utc": None,
                "expired_at_utc": None,
            })
        else:
            if expected_revision is not None:
                raise DocumentConflictError("Solicitarea așteptată nu mai există.")
            record = {
                "id": uuid.uuid4().hex,
                "schema_version": 1,
                "student_key": student_key,
                "school_year": str(school_year),
                "request_date": day,
                "parent_name": parent_name,
                "student_name": student_name,
                "departure_time": str(departure_time),
                "reason_code": reason_code,
                "reason_label": REASONS[reason_code],
                "status": STATUS_PENDING,
                "revision": 1,
                "transmitted_at_utc": now.isoformat(),
                "decision_at_utc": None,
                "refused_at_utc": None,
                "expired_at_utc": None,
                "approved_at_utc": None,
                "document_path": None,
                "document_sha256": None,
            }
            registry["requests"].append(record)

        try:
            save_leave_pass_registry(registry, sha)
            return dict(record)
        except DocumentConflictError:
            continue
    raise DocumentConflictError("Solicitarea nu a putut fi salvată în siguranță. Reîncercați.")


def refuse_leave_request(*, student_rm_pg, request_id, expected_revision):
    return _decide_nonapproval(
        student_rm_pg=student_rm_pg, request_id=request_id,
        expected_revision=expected_revision, target_status=STATUS_REFUSED,
    )


def _decide_nonapproval(*, student_rm_pg, request_id, expected_revision, target_status):
    student_key = normalize_student_key(student_rm_pg)
    now = _utc_now()
    # Momentul aprobării rămâne identic pe toate retry-urile, astfel încât PDF-ul
    # generat să fie determinist chiar dacă registrul are un conflict concurent.
    approved_at = now.isoformat()
    for _ in range(3):
        registry, sha = load_leave_pass_registry()
        matches = [
            item for item in registry["requests"]
            if item.get("id") == str(request_id) and item.get("student_key") == student_key
        ]
        if len(matches) != 1:
            raise DocumentStorageError("Solicitarea de învoire nu există pentru elevul selectat.")
        record = matches[0]
        if _expire_record_if_needed(record, now):
            try:
                save_leave_pass_registry(registry, sha)
                return dict(record)
            except DocumentConflictError:
                continue
        if record.get("status") != STATUS_PENDING:
            raise DocumentConflictError("Numai o solicitare în așteptare poate fi refuzată.")
        if int(record.get("revision", 1)) != int(expected_revision):
            raise DocumentConflictError("Solicitarea a fost reformulată. Consultați forma actualizată.")
        record["status"] = target_status
        record["refused_at_utc"] = now.isoformat()
        record["decision_at_utc"] = now.isoformat()
        try:
            save_leave_pass_registry(registry, sha)
            return dict(record)
        except DocumentConflictError:
            continue
    raise DocumentConflictError("Refuzul nu a putut fi înregistrat în siguranță.")


def approve_leave_request(*, student_rm_pg, request_id, expected_revision):
    student_key = normalize_student_key(student_rm_pg)
    request_id = str(request_id or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{32}", request_id):
        raise ValueError("Identificatorul solicitării este invalid.")

    now = _utc_now()
    for _ in range(3):
        registry, sha = load_leave_pass_registry()
        matches = [
            item for item in registry["requests"]
            if item.get("id") == request_id and item.get("student_key") == student_key
        ]
        if len(matches) != 1:
            raise DocumentStorageError("Solicitarea de învoire nu există pentru elevul selectat.")
        record = matches[0]

        if record.get("status") == STATUS_APPROVED:
            if int(record.get("revision", 1)) != int(expected_revision):
                raise DocumentConflictError("Versiunea aprobată nu corespunde solicitării consultate.")
            return dict(record)

        if _expire_record_if_needed(record, now):
            try:
                save_leave_pass_registry(registry, sha)
                return dict(record)
            except DocumentConflictError:
                continue

        if record.get("status") != STATUS_PENDING:
            raise DocumentConflictError("Numai o solicitare în așteptare poate fi aprobată.")
        if int(record.get("revision", 1)) != int(expected_revision):
            raise DocumentConflictError("Solicitarea a fost reformulată. Consultați forma actualizată.")
        _validate_current_day_future(record["request_date"], record["departure_time"], now)

        pdf_data = generate_leave_pass_pdf(
            parent_name=record["parent_name"], student_name=record["student_name"],
            request_date=record["request_date"], departure_time=record["departure_time"],
            reason_label=record["reason_label"], transmitted_at_utc=record["transmitted_at_utc"],
            approved_at_utc=approved_at, request_id=request_id,
        )
        pdf_sha = hashlib.sha256(pdf_data).hexdigest()
        path = f"{DOCUMENT_ROOT}/{record['school_year']}/{student_key}/bilet_voie_{request_id}.pdf"

        try:
            private_write(path, pdf_data, expected_sha=None, message="Generare bilet de voie aprobat")
        except DocumentConflictError:
            existing, _ = private_read(path)
            if existing is None or hashlib.sha256(existing).hexdigest() != pdf_sha:
                raise DocumentConflictError(
                    "Există deja un bilet de voie cu un conținut diferit. Aprobarea a fost oprită."
                )

        record.update({
            "status": STATUS_APPROVED,
            "approved_at_utc": approved_at,
            "decision_at_utc": approved_at,
            "document_path": path,
            "document_sha256": pdf_sha,
        })
        try:
            save_leave_pass_registry(registry, sha)
            return dict(record)
        except DocumentConflictError:
            continue

    raise DocumentConflictError("Aprobarea nu a putut fi confirmată în siguranță. Reîncercați.")


def read_approved_leave_pass(student_rm_pg, request_id):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_leave_pass_registry()
    matches = [
        item for item in registry["requests"]
        if item.get("id") == str(request_id)
        and item.get("student_key") == student_key
        and item.get("status") == STATUS_APPROVED
    ]
    if len(matches) != 1:
        raise DocumentStorageError("Biletul de voie aprobat nu a fost găsit.")
    record = matches[0]
    content, _ = private_read(record.get("document_path"))
    if content is None or hashlib.sha256(content).hexdigest() != record.get("document_sha256"):
        raise DocumentStorageError("Integritatea biletului de voie nu a putut fi confirmată.")
    return dict(record), content
