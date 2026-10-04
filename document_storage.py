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

PRIVATE_REPO = "profudeconta-sketch/catalog-online-date-private"
DOCUMENT_ROOT = "documente_scolare"
REGISTRY_PATH = f"{DOCUMENT_ROOT}/registru_documente.json"
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
    if not clean.startswith(DOCUMENT_ROOT + "/") and clean != DOCUMENT_ROOT:
        raise DocumentStorageError("Calea documentului nu apartine zonei private aprobate.")
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


def store_new_document(record, content):
    path = record.get("stored_path")
    if not path:
        raise DocumentStorageError("Documentul nu are cale de stocare.")
    digest = hashlib.sha256(bytes(content)).hexdigest()
    if digest != record.get("sha256"):
        raise DocumentStorageError("Integritatea documentului nu corespunde metadatelor.")

    private_write(path, bytes(content), expected_sha=None, message="Adaugare document scolar")

    registry, registry_sha = load_registry()
    if any(item.get("id") == record.get("id") for item in registry["documents"]):
        raise DocumentConflictError("Documentul exista deja in registru.")

    registry["documents"].append(record)
    try:
        save_registry(registry, registry_sha)
    except Exception:
        # Fisierul ramane in zona privata, dar nu este pierdut. Reconcilierea
        # registrului poate fi facuta ulterior pe baza caii si hash-ului.
        raise

    return record["id"]
