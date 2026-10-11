"""Read-only retrieval of the existing complete system tutorial.

No network, credentials, student data or writes. Answers are grounded in
relevant sections of the actual tutorial, not a portal-only FAQ.
"""
from __future__ import annotations

import re
import unicodedata
from nelutu_parent_guide import TUTORIAL_TEXT

MAX_EXCERPT_CHARS = 3000
MAX_SECTIONS = 3


def _tokens(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]+", normalized) if len(w) > 2}


def _sections():
    # Preserve exact tutorial paragraphs as the source of truth.
    return [
        (heading.strip(), body.strip())
        for heading, body in re.findall(
            r"(?m)^## ([^\n]+)\n(.*?)(?=^## |^# |\Z)",
            TUTORIAL_TEXT, re.DOTALL | re.MULTILINE,
        )
        if body.strip()
    ]


def tutorial_context(question: str) -> str:
    """Select relevant complete-system guide sections; return empty if uncertain."""
    if not isinstance(question, str) or not question.strip() or len(question) > 600:
        return ""
    query = _tokens(question)
    if not query:
        return ""
    ranked = []
    for index, (heading, body) in enumerate(_sections()):
        title_terms = _tokens(heading)
        body_terms = _tokens(body)
        score = 4 * len(query & title_terms) + len(query & body_terms)
        if score >= 2:
            ranked.append((-score, index, heading, body))
    ranked.sort()
    result = []
    used = 0
    for _, _, heading, body in ranked[:MAX_SECTIONS]:
        section = f"## {heading}\n{body}"
        if len(section) > MAX_EXCERPT_CHARS:
            section = section[:MAX_EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"
        if used + len(section) > MAX_EXCERPT_CHARS:
            break
        result.append(section)
        used += len(section)
    return "\n\n".join(result)


def tutorial_topics():
    """Expose headings for inspection and offline tests."""
    return tuple(heading for heading, _ in _sections())
