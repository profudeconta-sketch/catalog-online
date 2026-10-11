"""Opt-in experimental free-form Gemini transport; not wired to public Streamlit.

Only fictional/public content after explicit consent, offline budget approval and
operator enablement. The validator is heuristic, NOT a privacy guarantee.
"""
from __future__ import annotations

import json
from urllib import error, request

from nelutu_free_dialogue_preparation import prepare_public_dialogue
from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT


def generate_public_dialogue(history, message, *, api_key=None,
                             enabled=False, confirmed=False,
                             budget_reserved=False, opener=None):
    """One request, no retries; return None on any failed gate or error."""
    if enabled is not True or confirmed is not True or budget_reserved is not True:
        return None
    if not isinstance(api_key, str) or not api_key.strip():
        return None
    contents = prepare_public_dialogue(history, message, consent=True)
    if contents is None:
        return None
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.65},
    }).encode("utf-8")
    req = request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    try:
        if opener is None:
            opener = request.urlopen
        with opener(req, timeout=TIMEOUT) as response:
            result = json.load(response)
        parts = result["candidates"][0]["content"]["parts"]
        answer = "".join(part.get("text", "") for part in parts).strip()
        return answer[:1500] or None
    except (error.HTTPError, error.URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError, UnicodeError, AttributeError):
        return None
