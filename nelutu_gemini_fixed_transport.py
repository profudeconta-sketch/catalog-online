"""Shared transport for fixed fictional Gemini demonstrations only.

No free-form messages, no school data and no automatic retries.
"""
from __future__ import annotations

import json
from urllib import error, request

from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT


def is_approved_fixed_exchange(exchange) -> bool:
    """Allow only the four exact public transcripts already displayed in the demo."""
    from nelutu_gemini_fixed_context import FIRST_QUESTION, FIRST_ANSWER, FOLLOW_UP
    from nelutu_gemini_fixed_multiturn import FIXED_EXCHANGE
    from nelutu_gemini_fixed_paraphrase import PARAPHRASE_EXCHANGE
    from nelutu_gemini_fixed_topic_return import TOPIC_RETURN_EXCHANGE

    approved = (
        (("user", FIRST_QUESTION), ("model", FIRST_ANSWER), ("user", FOLLOW_UP)),
        FIXED_EXCHANGE,
        PARAPHRASE_EXCHANGE,
        TOPIC_RETURN_EXCHANGE,
    )
    return type(exchange) is tuple and any(exchange == item for item in approved)


def send_fixed_exchange(exchange, *, api_key: str | None, enabled: bool,
                        confirmed: bool, temperature: float,
                        opener=None) -> str | None:
    """One approved request; sanitized failure; fixed transcript only."""
    if not enabled or not confirmed or not isinstance(api_key, str) or not api_key.strip():
        return None
    if not is_approved_fixed_exchange(exchange):
        return None
    if opener is None:
        opener = request.urlopen
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": role, "parts": [{"text": message}]}
            for role, message in exchange
        ],
        "generationConfig": {"maxOutputTokens": 240, "temperature": temperature},
    }).encode("utf-8")
    req = request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    try:
        with opener(req, timeout=TIMEOUT) as response:
            result = json.load(response)
        parts = result["candidates"][0]["content"]["parts"]
        answer = "".join(part.get("text", "") for part in parts).strip()
        return answer[:1500] or None
    except (error.HTTPError, error.URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError, UnicodeError, AttributeError):
        return None
