"""Isolated, fixed five-replica context test; never accepts free-form messages."""
from __future__ import annotations

import json
from urllib import error, request

from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT

# Public fictional exchange, displayed in full before each outbound request.
FIXED_EXCHANGE = (
    ("user", "Aș vrea să-mi organizez mai bine diminețile."),
    ("model", "Poți pregăti seara trei lucruri importante pentru ziua următoare."),
    ("user", "Dă-mi un exemplu concret."),
    ("model", "Pregătește hainele, pune cheile la locul lor și notează prima sarcină."),
    ("user", "Și dacă uit al doilea lucru, cum îmi pot aminti?"),
)


def fixed_multiturn_test(*, api_key: str | None = None,
                         enabled: bool = False, confirmed: bool = False) -> str | None:
    """Sends only FIXED_EXCHANGE after explicit consent, no real session data."""
    if not enabled or not confirmed or not isinstance(api_key, str) or not api_key.strip():
        return None
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": role, "parts": [{"text": message}]}
            for role, message in FIXED_EXCHANGE
        ],
        "generationConfig": {"maxOutputTokens": 240, "temperature": 0.6},
    }).encode("utf-8")
    req = request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
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
