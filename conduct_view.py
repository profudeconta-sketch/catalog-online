"""Afișare read-only, comună pentru fișa elevului și portalul părinților.

Registrul privat al notelor la purtare este singura sursă a notelor pe intervale.
Acest modul nu scrie și nu modifică înregistrările elevilor.
"""
from __future__ import annotations

import base64
import datetime
import json
import urllib.request

from annual_closure_engine import CLJ_2026_2027_COURSE_INTERVALS


class ConductViewError(RuntimeError):
    """Afișarea este blocată dacă datele nu pot fi confirmate."""


CONDUCT_ANNUAL_NOTICE = (
    "Notele la purtare acordate pentru fiecare dintre cele 5 intervale de cursuri "
    "evaluează comportamentul elevului. Media anuală la purtare se încheie numai "
    "la sfârșitul anului școlar, din media aritmetică a celor 5 note, rotunjită "
    "la cel mai apropiat întreg (0,50 în favoarea elevului). "
    "Potrivit art. 109 alin. (1) din ROFUIP și art. 28 alin. (2) din Statutul elevului, "
    "media anuală la purtare se diminuează cu un punct la fiecare 20 de absențe "
    "nemotivate acumulate în anul școlar sau la atingerea pragului de 20% absențe "
    "nemotivate din orele anuale ale unei discipline/unui modul. "
    "Diminuarea se stabilește la încheierea anului, fără modificarea retroactivă "
    "a notelor acordate pe intervale. Media generală școlară este distinctă de media "
    "anuală la purtare."
)


def validate_conduct_registry_for_view(data):
    """Validare fail-closed, inclusiv împotriva notelor duplicate."""
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("school_year") != "2026-2027"
        or not isinstance(data.get("grades"), list)
    ):
        raise ConductViewError("Structura registrului la purtare nu este validă.")
    intervals = {item.number: item for item in CLJ_2026_2027_COURSE_INTERVALS}
    seen = set()
    for record in data["grades"]:
        if not isinstance(record, dict):
            raise ConductViewError("Înregistrare la purtare invalidă.")
        key = record.get("student_key")
        number = record.get("interval_number")
        grade = record.get("grade")
        if (
            not isinstance(key, str) or not key.strip()
            or type(number) is not int or number not in intervals
            or type(grade) is not int or not 1 <= grade <= 10
        ):
            raise ConductViewError("Notă sau identificator invalid în registrul la purtare.")
        unique = (key.strip(), number)
        if unique in seen:
            raise ConductViewError("Înregistrări duplicate în registrul la purtare.")
        seen.add(unique)
        try:
            awarded = datetime.date.fromisoformat(record["awarded_on"])
        except (TypeError, ValueError, KeyError):
            raise ConductViewError("Data unei note la purtare este invalidă.") from None
        if awarded < intervals[number].end_date:
            raise ConductViewError("O notă la purtare este datată înainte de interval.")
    return data


def conduct_interval_rows(registry, student_key):
    """Exclusiv cele 5 intervale pentru elevul autentificat/selectat."""
    validated = validate_conduct_registry_for_view(registry)
    key = str(student_key or "").strip()
    if not key:
        raise ConductViewError("Identitatea elevului nu poate fi stabilită.")
    owned = {
        item["interval_number"]: item
        for item in validated["grades"]
        if item["student_key"].strip() == key
    }
    return [
        {
            "Interval de cursuri": f"Intervalul {interval.number}",
            "Perioada": (
                f"{interval.start_date.strftime('%d.%m.%Y')} – "
                f"{interval.end_date.strftime('%d.%m.%Y')}"
            ),
            "Nota la purtare": str(owned[interval.number]["grade"]) if interval.number in owned else "Neacordată",
            "Data acordării": owned[interval.number]["awarded_on"] if interval.number in owned else "—",
        }
        for interval in CLJ_2026_2027_COURSE_INTERVALS
    ]


def fetch_private_conduct_registry(token):
    """Citește registrul actual din repo-ul privat; nu utilizează fișiere locale posibil vechi."""
    if not isinstance(token, str) or not token.strip():
        raise ConductViewError("Sincronizarea registrului la purtare nu este configurată.")
    url = (
        "https://api.github.com/repos/profudeconta-sketch/"
        "catalog-online-date-private/contents/registru_purtare_2026_2027.json?ref=main"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StreamlitApp",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 200:
                raise ConductViewError("Sursa privată nu a confirmat registrul la purtare.")
            payload = json.loads(response.read().decode("utf-8"))
        encoded = payload.get("content")
        if not isinstance(encoded, str) or not encoded:
            raise ConductViewError("Registrul privat este gol.")
        data = json.loads(base64.b64decode(encoded, validate=True).decode("utf-8"))
        return validate_conduct_registry_for_view(data)
    except ConductViewError:
        raise
    except Exception:
        raise ConductViewError("Registrul privat la purtare nu este disponibil sau valid.") from None
