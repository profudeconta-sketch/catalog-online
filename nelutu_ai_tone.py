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
    r"\b(?:violenta|agresiune|hartui\w*|hartuire|bullying\w*|amenintat\w*|umilire|suicid|sinucidere|abuz|hartuit|amenintar\w*)\b",
    r"\b(?:sunt|am fost|ma simt)\s+(?:hartuit\w*|amenintat\w*|umilit\w*|agresat\w*)\b",
    r"\b(?:mi-e frica|imi este frica|ma simt in pericol|vreau sa mor|nu mai vreau sa traiesc|vreau sa imi fac rau)\b",
    r"\b(?:deces|a murit|accident grav|urgenta medicala)\b",
    r"\b(?:ma sinucid|vreau sa ma sinucid|imi pun capat zilelor|nu mai pot trai|nu mai rezist|imi fac rau)\b",
    r"\b(?:m-a lovit|m-a batut|m-a agresat|m-au lovit|m-au batut|m-au agresat|m-au amenintat)\b",
    r"\b(?:ma gandesc sa ma sinucid|vreau sa[- ]?mi fac rau|in pericol|agresat\w*|amenint\w*)\b",
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
