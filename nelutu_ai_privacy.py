"""Conservative, independent routing for Neluțu experimental external AI.

This is NOT a personal-data anonymizer. It only allows a narrow set of
predefined generic educational questions. Everything else stays local.
"""
from __future__ import annotations
import re
import unicodedata

SAFE_TOPICS = {
    "matematica": ("matematica", "gandire", "logica", "calcule"),
    "invatamant_tehnic": ("invatamantul tehnic", "meserii", "educatia tehnica"),
    "invatare": ("invatare", "cum invatam", "metode de invatare"),
    "motivatie": ("motivatia pentru invatare", "motivatie scolara"),
    "istorie_educatie": ("istoria educatiei", "spiru haret", "alexandru ioan cuza"),
}

# Restrict to exact approved questions, not keyword extraction from free text.
APPROVED_QUESTIONS = {
    "de ce invatam matematica",
    "la ce foloseste matematica in viata cotidiana",
    "de ce este important invatamantul tehnic",
    "ce rol are educatia tehnica",
    "cum putem invata mai eficient",
    "cum ne pastram motivatia pentru invatare",
    "ce a schimbat spiru haret in scoala",
    "ce rol a avut alexandru ioan cuza in educatie",
}

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[?!. ,;:]+", " ", text)
    return re.sub(r"\\s+", " ", text).strip()

def approved_external_question(text: str) -> bool:
    """Only exact, public, general educational prompts are externally eligible."""
    return normalize(text) in APPROVED_QUESTIONS

def external_messages(question: str, system_prompt: str) -> list[dict[str, str]]:
    """Never forwards chat history, local portal context or student records."""
    if not approved_external_question(question):
        raise ValueError("local_only")
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
