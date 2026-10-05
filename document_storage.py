"""Infrastructura Etapa 4 pentru documente scolare.

Acest modul nu contine date despre elevi si nu modifica fisierele catalogului.
Toate operatiile de persistenta sunt directionate explicit catre repository-ul
privat si folosesc verificare optimista prin SHA pentru a evita suprascrierile
silentioase.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid

from school_document_receipt_pdf import generate_school_document_receipt_pdf

PRIVATE_REPO = "profudeconta-sketch/catalog-online-date-private"
DOCUMENT_ROOT = "documente_scolare"
ANNUAL_CLOSURE_ROOT = "inchideri_anuale"
PRIVATE_ALLOWED_ROOTS = (DOCUMENT_ROOT, ANNUAL_CLOSURE_ROOT)
REGISTRY_PATH = f"{DOCUMENT_ROOT}/registru_documente.json"
PENDING_ROOT = f"{DOCUMENT_ROOT}/operatii_in_asteptare"
PARENT_EXCUSE_REGISTRY_PATH = f"{DOCUMENT_ROOT}/registru_motivari_parinte.json"
PARENT_EXCUSE_ANNUAL_LIMIT = 40
MAX_DOCUMENT_BYTES = 15 * 1024 * 1024

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": (".pdf",),
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
}

DOCUMENT_CATEGORIES = {
    "DOSAR_PERSONAL": {
        "CARTE_IDENTITATE",
        "DOVADA_ADRESA",
        "CERTIFICAT_NASTERE",
        "DIVERSE",
    },
    "SCUTIRE_MEDICALA": {"SCUTIRE_MEDICALA"},
    "DOSAR_BURSA": {
        "CERERE_BURSA",
        "ACORD_PRELUCRARE_DATE",
        "DECLARATIE_VENITURI_NETE_IMPOZABILE",
        "DOCUMENTE_MEDICALE",
        "CI_PARINTE_TUTORE",
        "CERTIFICATE_NASTERE_FRATI_SURORI",
        "CERTIFICAT_CASATORIE_PARINTI",
        "HOTARARE_SENTINTA_DIVORT",
        "CERTIFICAT_DECES_PARINTE",
        "ALTE_DOCUMENTE_JUSTIFICATIVE",
    },
    "MOTIVARE_PARINTE": {"MOTIVARE_ABSENTE_PARINTE"},
    "SCOALA_CATRE_PARINTE": {"INSTIINTARE", "DOCUMENT_SCOALA"},
    "CONFIRMARE_PRIMIRE": {"CONFIRMARE_ACCES_DOCUMENT"},
}

SCHOLARSHIP_TYPES = {
    "MERIT",
    "SOCIALA_VENIT",
    "SOCIALA_ORFAN",
    "SOCIALA_MEDICALA",
    "SOCIALA_MAME_MINORE",
    "CES",
}


class DocumentStorageError(RuntimeError):
    pass


class DocumentConflictError(DocumentStorageError):
    pass


def _token():
    token = os.environ.get("GITHUB_TOKEN") or ""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass
    if not token:
        raise DocumentStorageError("Tokenul pentru stocarea privata nu este disponibil.")
    return token


def _headers():
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CatalogScolarDocumente",
        "Cache-Control": "no-cache",
    }


def _api_url(path):
    clean = str(path).strip().lstrip("/")
    allowed = any(
        clean == root or clean.startswith(root + "/")
        for root in PRIVATE_ALLOWED_ROOTS
    )
    if not allowed:
        raise DocumentStorageError("Calea nu apartine unei zone private aprobate.")
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in clean.split("/"))
    return f"https://api.github.com/repos/{PRIVATE_REPO}/contents/{quoted}"


def private_read(path):
    req = urllib.request.Request(_api_url(path) + "?ref=main", headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return None, None
        raise DocumentStorageError(f"Citirea documentului privat a esuat: HTTP {ex.code}.") from ex
    except Exception as ex:
        raise DocumentStorageError("Citirea documentului privat a esuat.") from ex

    encoded = payload.get("content")
    sha = payload.get("sha")
    if not encoded or not sha:
        raise DocumentStorageError("Raspuns privat incomplet.")
    return base64.b64decode(encoded), sha


def private_write(path, content, expected_sha=None, message="Actualizare documente scolare"):
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError("Continutul trebuie transmis ca bytes.")

    current, current_sha = private_read(path)
    del current

    if expected_sha is not None and current_sha != expected_sha:
        raise DocumentConflictError(
            "Datele au fost modificate intre timp. Operatia a fost oprita pentru a evita suprascrierea."
        )
    if expected_sha is None and current_sha is not None:
        raise DocumentConflictError("Fisierul exista deja; suprascrierea neconfirmata a fost blocata.")

    payload = {
        "message": message,
        "content": base64.b64encode(bytes(content)).decode("ascii"),
        "branch": "main",
    }
    if current_sha:
        payload["sha"] = current_sha

    req = urllib.request.Request(
        _api_url(path),
        data=json.dumps(payload).encode("utf-8"),
        headers={**_headers(), "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        if ex.code in (409, 422):
            raise DocumentConflictError("Conflict la salvarea documentului; operatia a fost oprita.") from ex
        raise DocumentStorageError(f"Salvarea documentului privat a esuat: HTTP {ex.code}.") from ex
    except Exception as ex:
        raise DocumentStorageError("Salvarea documentului privat a esuat.") from ex

    return result.get("content", {}).get("sha")


def load_registry():
    raw, sha = private_read(REGISTRY_PATH)
    if raw is None:
        return {"schema_version": 1, "documents": []}, None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as ex:
        raise DocumentStorageError("Registrul documentelor este invalid.") from ex
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("documents"), list):
        raise DocumentStorageError("Structura registrului documentelor nu este valida.")
    return data, sha


def save_registry(registry, expected_sha):
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        raise DocumentStorageError("Registrul documentelor nu poate fi salvat: structura invalida.")
    raw = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    return private_write(
        REGISTRY_PATH,
        raw,
        expected_sha=expected_sha,
        message="Actualizare registru documente scolare",
    )


def normalize_student_key(rm_pg):
    value = " ".join(str(rm_pg or "").strip().split())
    if not value:
        raise ValueError("RM/PG lipseste.")
    return hashlib.sha256(value.casefold().encode("utf-8")).hexdigest()[:24]


def validate_upload(filename, mime_type, content):
    name = os.path.basename(str(filename or "").strip())
    mime = str(mime_type or "").strip().lower()
    data = bytes(content or b"")
    if not name or not data:
        raise ValueError("Fisierul este gol.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Fisierul depaseste limita de 15 MB.")
    extension = os.path.splitext(name)[1].lower()
    if mime in {"", "application/octet-stream"}:
        if extension == ".pdf":
            mime = "application/pdf"
        elif extension in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif extension == ".png":
            mime = "image/png"

    extensions = ALLOWED_DOCUMENT_TYPES.get(mime)
    if not extensions or not name.lower().endswith(extensions):
        raise ValueError("Sunt acceptate numai fisiere PDF, JPG/JPEG si PNG.")
    if mime == "application/pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("Fisierul nu are o semnatura PDF valida.")
    if mime == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
        raise ValueError("Fisierul nu are o semnatura JPEG valida.")
    if mime == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Fisierul nu are o semnatura PNG valida.")
    return name, mime, data


def build_document_record(
    *,
    student_rm_pg,
    direction,
    category,
    document_type,
    original_filename,
    mime_type,
    content,
    school_year,
    scholarship_type=None,
    sender_role=None,
    recipient_role=None,
):
    if category not in DOCUMENT_CATEGORIES or document_type not in DOCUMENT_CATEGORIES[category]:
        raise ValueError("Categoria sau tipul documentului nu este valid.")
    if scholarship_type is not None and scholarship_type not in SCHOLARSHIP_TYPES:
        raise ValueError("Tipul bursei nu este valid.")
    if direction not in {"PARINTE_SCOALA", "SCOALA_PARINTE", "SISTEM"}:
        raise ValueError("Directia documentului nu este valida.")

    name, mime, data = validate_upload(original_filename, mime_type, content)
    doc_id = uuid.uuid4().hex
    student_key = normalize_student_key(student_rm_pg)
    extension = os.path.splitext(name)[1].lower()
    stored_path = f"{DOCUMENT_ROOT}/{school_year}/{student_key}/{doc_id}{extension}"
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    record = {
        "id": doc_id,
        "schema_version": 1,
        "student_key": student_key,
        "school_year": str(school_year),
        "direction": direction,
        "category": category,
        "document_type": document_type,
        "scholarship_type": scholarship_type,
        "original_filename": name,
        "stored_path": stored_path,
        "mime_type": mime,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sender_role": sender_role,
        "recipient_role": recipient_role,
        "created_at_utc": now,
        "status": "NECITIT" if direction == "SCOALA_PARINTE" else "TRANSMIS",
        "first_accessed_at_utc": None,
    }
    return record, data


def load_parent_excuse_registry():
    raw, sha = private_read(PARENT_EXCUSE_REGISTRY_PATH)
    if raw is None:
        return {"schema_version": 1, "requests": []}, None
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as ex:
        raise DocumentStorageError("Registrul motivarilor parintelui este invalid.") from ex
    if not isinstance(data, dict) or not isinstance(data.get("requests"), list):
        raise DocumentStorageError("Structura registrului motivarilor parintelui este invalida.")
    return data, sha


def save_parent_excuse_registry(registry, expected_sha):
    if not isinstance(registry, dict) or not isinstance(registry.get("requests"), list):
        raise DocumentStorageError("Registrul motivarilor parintelui nu poate fi salvat.")
    raw = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    return private_write(
        PARENT_EXCUSE_REGISTRY_PATH,
        raw,
        expected_sha=expected_sha,
        message="Actualizare registru motivari parinte",
    )


def parent_excuse_usage(student_rm_pg, school_year):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_parent_excuse_registry()
    used = 0
    for item in registry["requests"]:
        if item.get("student_key") != student_key:
            continue
        if str(item.get("school_year")) != str(school_year):
            continue
        if item.get("status") != "TRANSMIS":
            continue
        try:
            used += int(item.get("hours", 0))
        except (TypeError, ValueError):
            raise DocumentStorageError("Registrul motivarilor contine un numar de ore invalid.")
    if used < 0 or used > PARENT_EXCUSE_ANNUAL_LIMIT:
        raise DocumentStorageError("Contorul anual al motivarilor este inconsistent.")
    return {
        "used_hours": used,
        "remaining_hours": PARENT_EXCUSE_ANNUAL_LIMIT - used,
        "annual_limit": PARENT_EXCUSE_ANNUAL_LIMIT,
    }


def validate_parent_excuse_hours(student_rm_pg, school_year, requested_hours):
    try:
        hours = int(requested_hours)
    except (TypeError, ValueError) as ex:
        raise ValueError("Numarul de ore solicitat nu este valid.") from ex
    if hours < 1:
        raise ValueError("Cererea trebuie sa contina cel putin o ora.")
    usage = parent_excuse_usage(student_rm_pg, school_year)
    if hours > usage["remaining_hours"]:
        raise ValueError(
            f"Limita anuala de {PARENT_EXCUSE_ANNUAL_LIMIT} de ore ar fi depasita. "
            f"Mai sunt disponibile {usage['remaining_hours']} ore."
        )
    return usage



def find_parent_excuse_document(student_rm_pg, school_year, content_sha256):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_registry()
    matches = [
        item for item in registry["documents"]
        if item.get("student_key") == student_key
        and str(item.get("school_year")) == str(school_year)
        and item.get("category") == "MOTIVARE_PARINTE"
        and item.get("document_type") == "MOTIVARE_ABSENTE_PARINTE"
        and item.get("direction") == "PARINTE_SCOALA"
        and item.get("sha256") == str(content_sha256)
    ]
    if len(matches) > 1:
        raise DocumentConflictError("Exista mai multe copii ale aceleiasi cereri.")
    return matches[0] if matches else None

def register_transmitted_parent_excuse(
    *,
    student_rm_pg,
    school_year,
    absence_date,
    hours,
    document_id,
    parent_name,
):
    validate_parent_excuse_hours(student_rm_pg, school_year, hours)
    student_key = normalize_student_key(student_rm_pg)
    request_fingerprint = hashlib.sha256(
        (
            student_key + "|" + str(school_year).strip() + "|" +
            str(absence_date).strip() + "|" + str(int(hours)) + "|" +
            str(parent_name or "").strip().casefold()
        ).encode("utf-8")
    ).hexdigest()
    registry, registry_sha = load_parent_excuse_registry()
    if any(
        item.get("request_fingerprint") == request_fingerprint
        and item.get("status") == "TRANSMIS"
        for item in registry["requests"]
    ):
        raise DocumentConflictError("Această cerere de motivare este deja transmisă.")
    if any(item.get("document_id") == document_id for item in registry["requests"]):
        raise DocumentConflictError("Cererea de motivare este deja înregistrată.")

    record = {
        "id": uuid.uuid4().hex,
        "schema_version": 1,
        "student_key": student_key,
        "request_fingerprint": request_fingerprint,
        "school_year": str(school_year),
        "absence_date": str(absence_date),
        "hours": int(hours),
        "document_id": str(document_id),
        "parent_name": str(parent_name or "").strip(),
        "status": "TRANSMIS",
        "transmitted_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    registry["requests"].append(record)
    save_parent_excuse_registry(registry, registry_sha)
    return record



def get_parent_excuse_for_document(student_rm_pg, document_id):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_parent_excuse_registry()
    matches = [
        item for item in registry["requests"]
        if item.get("student_key") == student_key
        and item.get("document_id") == str(document_id)
    ]
    if len(matches) > 1:
        raise DocumentConflictError("Există mai multe înregistrări pentru aceeași cerere de motivare.")
    return dict(matches[0]) if matches else None

def list_student_documents(student_rm_pg, direction=None):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_registry()
    documents = []
    for item in registry["documents"]:
        if item.get("student_key") != student_key:
            continue
        if direction is not None and item.get("direction") != direction:
            continue
        documents.append(dict(item))
    return sorted(documents, key=lambda item: item.get("created_at_utc", ""), reverse=True)


def read_registered_document(student_rm_pg, document_id):
    student_key = normalize_student_key(student_rm_pg)
    registry, _ = load_registry()
    matches = [
        item for item in registry["documents"]
        if item.get("id") == document_id and item.get("student_key") == student_key
    ]
    if len(matches) != 1:
        raise DocumentStorageError("Documentul nu exista pentru elevul selectat.")

    record = matches[0]
    content, _ = private_read(record.get("stored_path"))
    if content is None:
        raise DocumentStorageError("Fisierul documentului nu a fost gasit in zona privata.")
    if hashlib.sha256(content).hexdigest() != record.get("sha256"):
        raise DocumentStorageError("Integritatea documentului nu a putut fi confirmata.")
    return dict(record), content


def register_first_school_document_access(*, student_rm_pg, student_name, document_id):
    """Înregistrează idempotent prima accesare și generează confirmarea aferentă."""
    student_key = normalize_student_key(student_rm_pg)
    student_name = str(student_name or "").strip()
    source_id = str(document_id or "").strip().lower()
    if not student_name:
        raise DocumentStorageError("Numele elevului lipsește.")
    if not re.fullmatch(r"[0-9a-f]{32}", source_id):
        raise DocumentStorageError("Identificatorul documentului sursă este invalid.")

    confirmation_id = hashlib.sha256(
        ("confirmare-acces|" + source_id).encode("utf-8")
    ).hexdigest()[:32]
    accessed_at = dt.datetime.now(dt.timezone.utc).isoformat()

    for _attempt in range(3):
        registry, registry_sha = load_registry()
        source_matches = [
            item for item in registry["documents"]
            if item.get("id") == source_id and item.get("student_key") == student_key
        ]
        if len(source_matches) != 1:
            raise DocumentStorageError("Documentul transmis de școală nu există pentru elevul autentificat.")

        source = source_matches[0]
        if source.get("direction") != "SCOALA_PARINTE":
            raise DocumentStorageError("Prima accesare poate fi înregistrată numai pentru documente Școală → Părinte.")

        existing = [
            item for item in registry["documents"]
            if item.get("id") == confirmation_id
            or (
                item.get("category") == "CONFIRMARE_PRIMIRE"
                and item.get("source_document_id") == source_id
            )
        ]
        if len(existing) > 1:
            raise DocumentConflictError("Există mai multe confirmări pentru același document.")
        if existing:
            confirmation = existing[0]
            if confirmation.get("student_key") != student_key:
                raise DocumentConflictError("Confirmarea existentă nu aparține elevului autentificat.")
            if confirmation.get("source_document_id") != source_id:
                raise DocumentConflictError("Confirmarea existentă nu corespunde documentului accesat.")
            if source.get("confirmation_document_id") not in {None, confirmation.get("id")}:
                raise DocumentConflictError("Documentul sursă indică o altă confirmare.")
            return {
                "source_document": dict(source),
                "confirmation_document": dict(confirmation),
                "created": False,
            }

        if source.get("first_accessed_at_utc"):
            raise DocumentConflictError(
                "Documentul este marcat ca accesat, dar confirmarea aferentă lipsește. "
                "Operația a fost oprită pentru verificare."
            )

        confirmation_filename = f"Confirmare_primire_{source_id}.pdf"
        confirmation_data = generate_school_document_receipt_pdf(
            student_name=student_name,
            source_document_name=source.get("original_filename") or "Document transmis de școală",
            accessed_at_utc=accessed_at,
            source_document_id=source_id,
        )
        confirmation_name, confirmation_mime, confirmation_data = validate_upload(
            confirmation_filename,
            "application/pdf",
            confirmation_data,
        )
        stored_path = (
            f"{DOCUMENT_ROOT}/{source.get('school_year')}/{student_key}/"
            f"{confirmation_id}.pdf"
        )
        confirmation = {
            "id": confirmation_id,
            "schema_version": 1,
            "student_key": student_key,
            "school_year": str(source.get("school_year") or ""),
            "direction": "SISTEM",
            "category": "CONFIRMARE_PRIMIRE",
            "document_type": "CONFIRMARE_ACCES_DOCUMENT",
            "scholarship_type": None,
            "original_filename": confirmation_name,
            "stored_path": stored_path,
            "mime_type": confirmation_mime,
            "size_bytes": len(confirmation_data),
            "sha256": hashlib.sha256(confirmation_data).hexdigest(),
            "sender_role": "SISTEM",
            "recipient_role": "SCOALA",
            "created_at_utc": accessed_at,
            "status": "GENERAT",
            "first_accessed_at_utc": None,
            "source_document_id": source_id,
        }

        try:
            private_write(
                stored_path,
                confirmation_data,
                expected_sha=None,
                message="Generare confirmare prima accesare document",
            )
        except DocumentConflictError:
            existing_content, _ = private_read(stored_path)
            if existing_content is None:
                raise
            # Dacă o încercare anterioară a scris PDF-ul dar nu a reușit încă
            # actualizarea registrului, îl reutilizăm numai dacă este exact
            # același PDF determinist pentru același timestamp.
            if hashlib.sha256(existing_content).hexdigest() != confirmation["sha256"]:
                raise DocumentConflictError(
                    "Există o confirmare privată neînregistrată cu un conținut diferit. "
                    "Operația a fost oprită pentru verificare."
                )

        source["status"] = "CITIT"
        source["first_accessed_at_utc"] = accessed_at
        source["confirmation_document_id"] = confirmation_id
        registry["documents"].append(confirmation)

        try:
            save_registry(registry, registry_sha)
            return {
                "source_document": dict(source),
                "confirmation_document": dict(confirmation),
                "created": True,
            }
        except DocumentConflictError:
            continue

    registry, _ = load_registry()
    existing = [
        item for item in registry["documents"]
        if item.get("id") == confirmation_id
        and item.get("student_key") == student_key
        and item.get("source_document_id") == source_id
    ]
    if len(existing) == 1:
        source_matches = [
            item for item in registry["documents"]
            if item.get("id") == source_id and item.get("student_key") == student_key
        ]
        if len(source_matches) == 1:
            return {
                "source_document": dict(source_matches[0]),
                "confirmation_document": dict(existing[0]),
                "created": False,
            }
    raise DocumentConflictError(
        "Prima accesare nu a putut fi confirmată în siguranță. Reîncercați."
    )


def _pending_path(document_id):
    value = str(document_id or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{32}", value):
        raise DocumentStorageError("Identificator de document invalid.")
    return f"{PENDING_ROOT}/{value}.json"


def _save_pending_record(record, reason):
    pending = {
        "schema_version": 1,
        "document": record,
        "reason": str(reason)[:500],
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    raw = json.dumps(pending, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    path = _pending_path(record.get("id"))
    _, sha = private_read(path)
    return private_write(
        path,
        raw,
        expected_sha=sha,
        message="Salvare operatie document in asteptare",
    )


def store_new_document(record, content):
    path = record.get("stored_path")
    if not path:
        raise DocumentStorageError("Documentul nu are cale de stocare.")
    digest = hashlib.sha256(bytes(content)).hexdigest()
    if digest != record.get("sha256"):
        raise DocumentStorageError("Integritatea documentului nu corespunde metadatelor.")

    private_write(path, bytes(content), expected_sha=None, message="Adaugare document scolar")

    try:
        registry, registry_sha = load_registry()
        if any(item.get("id") == record.get("id") for item in registry["documents"]):
            raise DocumentConflictError("Documentul exista deja in registru.")
        registry["documents"].append(record)
        save_registry(registry, registry_sha)
    except Exception as ex:
        try:
            _save_pending_record(record, ex)
        except Exception as pending_ex:
            raise DocumentStorageError(
                "Fisierul a fost salvat privat, dar registrul si jurnalul de recuperare "
                "nu au putut fi confirmate. Operatia NU trebuie considerata transmisa."
            ) from pending_ex
        raise DocumentStorageError(
            "Fisierul a fost salvat privat, dar registrul principal nu a fost confirmat. "
            "Operatia a fost marcata pentru recuperare si NU este considerata transmisa."
        ) from ex

    return record["id"]
