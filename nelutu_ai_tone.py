"""Conservative conversation-style policy for Neluțu's experimental persona.

This is a local style gate, not a complete safety classifier.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass

def _norm(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower())
                   if not unicodedata.combining(c))

SERIOUS_PATTERNS = (
    r"\b(?:ma|m-a|mau|m-au)\s+(?:lovit|batut|amenintat|agresat)\b",
    r"\b(?:violenta|agresiune|hartuir|bullying|umilire|suicid|sinucidere|abuz)\w*\b",
    r"\b(?:mi-e frica|imi este frica|ma simt in pericol|vreau sa mor)\b",
    r"\b(?:deces|a murit|accident grav|urgenta medicala)\b",
)
STYLE_RULES = {
    "warm": "Vorbește firesc, cald, cu regionalisme autentice și rare.",
    "serious": "Nu face glume. Ascultă cu empatie, nu judeca și propune pași practici.",
}

@dataclass(frozen=True)
class ToneDecision:
    mode: str
    humor_allowed: bool
    instruction: str

def choose_tone(message: str) -> ToneDecision:
    normalized = _norm(message)
    serious = any(re.search(pattern, normalized) for pattern in SERIOUS_PATTERNS)
    mode = "serious" if serious else "warm"
    return ToneDecision(mode, not serious, STYLE_RULES[mode])
