"""Offline preparation of a bounded, consent-based conversational transcript.

No network calls, no keys, no school data. This is not a PII guarantee:
free-form messages must not be sent to a provider until separate privacy review.
"""
from __future__ import annotations

from nelutu_gemini_optional import is_public_general_chat

MAX_TURNS = 12
MAX_TOTAL_CHARS = 6000


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


def bounded_public_history(history, next_message=""):
    """Keep recent complete public exchanges; discard oldest, never all on overflow."""
    if type(history) is not tuple or len(history) % 2:
        return ()
    valid = []
    for index in range(0, len(history), 2):
        pair = history[index:index + 2]
        if (len(pair) != 2 or any(type(item) is not tuple or len(item) != 2 for item in pair)
                or pair[0][0] != "user" or pair[1][0] != "model"
                or not all(is_public_general_chat(item[1]) for item in pair)):
            return ()
        valid.extend(pair)
    while valid and (len(valid) > MAX_TURNS or
                     sum(len(message) for _, message in valid) + len(next_message) > MAX_TOTAL_CHARS):
        valid = valid[2:]
    return tuple(valid)


def append_public_exchange(history, question, answer):
    """Store a public turn without exposing assistant text rejected by privacy gate.

    A fixed non-informative model turn preserves the public question's topic.
    Private questions clear external context rather than crossing the boundary.
    """
    if not is_public_general_chat(question):
        return ()
    safe_answer = answer if is_public_general_chat(answer) else (
        "Am raspuns la intrebarea anterioara."
    )
    return bounded_public_history(
        bounded_public_history(history, question) +
        (("user", question), ("model", safe_answer))
    )


# Local-only archive is independent of the bounded outbound Gemini window.
# It contains only text accepted by the existing public privacy filter.
MAX_LOCAL_TURNS = 200


def append_local_public_archive(archive, question, answer):
    """Retain up to 100 safe public exchanges locally; no network or storage writes."""
    if not is_public_general_chat(question):
        return ()
    if type(archive) is not tuple or len(archive) % 2:
        archive = ()
    safe = answer if is_public_general_chat(answer) else "Am raspuns la intrebarea anterioara."
    return (archive + (("user", question), ("model", safe)))[-MAX_LOCAL_TURNS:]
