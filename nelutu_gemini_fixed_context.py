"""Fixed, non-personal two-turn Gemini memory experiment.

Not connected to the school applications. Only hardcoded public messages are sent.
"""
from __future__ import annotations

import json
from urllib import request, error

from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT

FIRST_QUESTION = "Ce înseamnă să fii punctual?"
FIRST_ANSWER = "Să ajungi la ora promisă și să respecți timpul celorlalți."
FOLLOW_UP = "Și de ce este important acest lucru?"
MAX_REPLY = 1500


def fixed_context_test(*, api_key: str | None = None,
                       enabled: bool = False, confirmed: bool = False) -> str | None:
    """Requires explicit consent for the entire fixed transcript."""
    if not enabled or not confirmed or not isinstance(api_key, str) or not api_key.strip():
        return None
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": "user", "parts": [{"text": FIRST_QUESTION}]},
            {"role": "model", "parts": [{"text": FIRST_ANSWER}]},
            {"role": "user", "parts": [{"text": FOLLOW_UP}]},
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
        return answer[:MAX_REPLY] or None
    except (error.HTTPError, error.URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError, UnicodeError):
        return None
