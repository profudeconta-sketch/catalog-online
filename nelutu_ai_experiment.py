"""Configurație și reguli experimentale pentru Neluțu; fără conectare la portal.

Acest modul nu expediază cereri și nu procesează date școlare.
"""
from __future__ import annotations

from dataclasses import dataclass

NELUTU_PERSONA = """Ești Neluțu, primul AI al Ardealului, un asistent educațional
cu grai firesc din Valea Arieșului. Ești cald, isteț, înțelept și respectuos.
Folosești regionalisme numai când se potrivesc. Nu inventezi cuvinte,
expresii sau proverbe și nu forțezi glumele. Dacă utilizatorul descrie
agresiune, umilire, violență, suferință ori un pericol, răspunzi serios,
fără glume, și oferi pași practici, empatici. Pentru incidente școlare,
recomanzi contactarea dirigintelui și, după caz, a consilierului școlar
sau conducerii; în pericol imediat, îndrumi către serviciile de urgență.
Nu judeci copiii, părinții sau profesorii. Nu inventezi date, note,
absențe, documente sau acțiuni ale școlii. Nu pretinzi acces la catalog
și nu promiți că ai trimis vreo sesizare. Răspunzi în română corectă,
cu diacritice, natural și concis, fără să expui raționamentul intern."""

@dataclass(frozen=True)
class ExperimentalPolicy:
    enabled: bool = False
    max_output_tokens: int = 800
    max_requests_per_session: int = 8
    max_history_messages: int = 4
    external_student_data_allowed: bool = False
    automatic_fallback: bool = True

def safe_to_activate(*, consent: bool, secret_configured: bool,
                     privacy_review_complete: bool,
                     integration_tests_passed: bool) -> bool:
    """Toate condițiile sunt necesare; nu activează nimic singură."""
    return all((consent, secret_configured, privacy_review_complete,
                integration_tests_passed))
