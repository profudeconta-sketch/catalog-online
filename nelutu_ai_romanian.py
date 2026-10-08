"""Conservative Romanian surface corrections for the isolated AI prototype.

Only narrowly scoped, high-confidence phrases are changed. This is not a
general grammar checker and must not alter genuine regional expressions.
"""
from __future__ import annotations
import re

_RULES = (
    (r"\bpasând prin economie\b", "trecând prin economie"),
    (r"\bcu cuvinte tale\b", "cu propriile tale cuvinte"),
    (r"\bnu ezita să cere ajutorul\b", "nu ezita să ceri ajutor"),
    (r"\bsă devină autonome în domenii concrete\b", "să devină autonomi în domenii concrete"),
    (r"\bca un seminț de curiozitate\b", "ca o sămânță de curiozitate"),
    (r"\bștiriile\b", "informațiile"),
    (r"\bÎnvăță activ\b", "Învață activ"),
    (r"\bRepetați cu timp\b", "Repetă la intervale regulate"),
)

def polish_romanian(answer: str) -> str:
    """Apply only reviewed phrase-level corrections; preserve all other text."""
    if not isinstance(answer, str):
        raise TypeError("answer must be text")
    result = answer
    for pattern, replacement in _RULES:
        result = re.sub(pattern, replacement, result)
    return result
