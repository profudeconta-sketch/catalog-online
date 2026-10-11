"""Offline preparation of a bounded, consent-based conversational transcript.

No network calls, no keys, no school data. This is not a PII guarantee:
free-form messages must not be sent to a provider until separate privacy review.
"""
from __future__ import annotations

from nelutu_gemini_optional import is_public_general_chat

MAX_TURNS = 6
MAX_TOTAL_CHARS = 1800


def prepare_public_dialogue(history, new_message, *, consent=False):
    """Return validated Gemini-style contents, or None (fail closed).

    Accept only immutable tuples of (role, text); validate EVERY turn.
    This function never transmits anything and cannot authorize transmission.
    """
    if consent is not True or type(history) is not tuple:
        return None
    if len(history) > MAX_TURNS or len(history) % 2:
        return None
    if not is_public_general_chat(new_message):
        return None
    messages = history + (("user", new_message),)
    total = 0
    result = []
    for index, item in enumerate(messages):
        if type(item) is not tuple or len(item) != 2:
            return None
        role, message = item
        expected = "user" if index % 2 == 0 else "model"
        if role != expected or not is_public_general_chat(message):
            return None
        total += len(message)
        if total > MAX_TOTAL_CHARS:
            return None
        result.append({"role": role, "parts": [{"text": message}]})
    return result
