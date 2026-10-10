"""Optional Gemini conversational backend. No student data, no writes, opt-in only.

This module is deliberately NOT wired into the active portal. A separate review
must validate consent, routing, secrets and Streamlit resource limits first.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from urllib import request, error

MODEL = "gemini-2.5-flash-lite"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
MAX_CHARS = 600
TIMEOUT = 8

SYSTEM = (
    "Ești Neluțu-al-nost, asistent virtual ardelenesc, prietenos și cu umor discret. "
    "Conversează natural în română, inclusiv cu întrebări reformulate și fără diacritice. "
    "Ține cont de replicile anterioare, fără să pretinzi că ești om. "
    "Răspunde concis, logic, cu exemple cotidiene și idei practice. "
    "Nu inventa fapte sau surse; recunoaște incertitudinea. "
    "Nu solicita informații personale. Nu oferi conținut violent, abuziv sau injurios. "
    "Nu pretinde că poți modifica catalogul, aproba cereri sau genera documente."
)

# Fail-closed: do not forward school, identity, health or administrative data.
_BLOCKED = (
    "elev", "eleva", "copilul meu", "fiul meu", "fiica mea", "parinte",
    "catalog", "nota", "notele", "medie", "absent", "invoir",
    "scutir", "bursa", "document", "dosar", "dirigint", "profesor",
    "scoala", "clasa", "matricol", "pin", "parola", "contul",
    "telefon", "adresa", "email", "cnp", "serie", "buletin",
    "diagnostic", "medical", "autism", "ces", "boala", "tratament",
    "suicid", "sinucid", "omor", "lovit", "violenta", "abuz",
)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?:\+?40|0)[\s.-]?(?:\d[\s.-]?){9}\b")
_LONG_DIGITS = re.compile(r"\b\d{6,}\b")


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def is_public_general_chat(message: str) -> bool:
    """Conservative boundary, not a guarantee of personal-data detection."""
    if not isinstance(message, str) or not 1 <= len(message.strip()) <= MAX_CHARS:
        return False
    norm = _normalize(message)
    if any(term in norm for term in _BLOCKED):
        return False
    if _EMAIL.search(message) or _PHONE.search(message) or _LONG_DIGITS.search(message):
        return False
    return True


def generate(message: str, history: tuple[tuple[str, str], ...] = (), *,
             api_key: str | None = None, enabled: bool = False,
             public_text_confirmed: bool = False) -> str | None:
    """Return None on blocked, unavailable or failed service; never raise to UI.

    History is forbidden for external requests at this stage. Neither secrets
    nor request contents are logged.
    """
    # Explicit per-request consent is required even for apparently public text.
    # The caller must show the actual outbound message before confirmation.
    if not enabled or not public_text_confirmed or not is_public_general_chat(message):
        return None
    key = api_key or os.environ.get("NELUTU_GEMINI_API_KEY")
    if not isinstance(key, str) or not key.strip():
        return None
    # Until history has a separate explicit consent UI, forbid sending it.
    if history:
        return None
    contents = [{"role": "user", "parts": [{"text": message}]}]
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 240, "temperature": 0.6},
    }).encode("utf-8")
    req = request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT) as response:
            result = json.load(response)
        parts = result["candidates"][0]["content"]["parts"]
        answer = "".join(part.get("text", "") for part in parts).strip()
        return answer[:1500] or None
    except (error.HTTPError, error.URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError, UnicodeError):
        return None
