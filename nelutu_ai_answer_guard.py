"""Conservative guard for saving educational answers in Neluțu memory.

Not a complete PII detector. A false negative remains possible; this
experimental memory must not be activated for real parent conversations.
"""
from __future__ import annotations
import re
from nelutu_ai_privacy import normalize

BLOCKED_TERMS = (
    "cnp", "pin", "parola", "numar matricol", "nr matricol",
    "nota elevului", "notele elevului", "absentele elevului",
    "elevul meu", "fiul meu", "fiica mea", "copilul meu",
    "domiciliu", "adresa elevului", "telefonul elevului",
)
EMAIL = re.compile(r"(?<!\w)[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")
LONG_NUMBER = re.compile(r"(?<!\d)\d{9,}(?!\d)")
PHONE = re.compile(r"(?<!\d)(?:\+?40|0)[\s.-]?[237]\d(?:[\s.-]?\d){7}(?!\d)")
IDENTIFIER = re.compile(r"\b(?:cnp|pin|parola|matricol)\s*[:=#-]?\s*\S+", re.I)

def safe_memory_answer(answer: str) -> bool:
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 2200:
        return False
    normalized = normalize(answer)
    if any(term in normalized for term in BLOCKED_TERMS):
        return False
    if EMAIL.search(answer) or LONG_NUMBER.search(answer) or PHONE.search(answer):
        return False
    if IDENTIFIER.search(normalized):
        return False
    return True
