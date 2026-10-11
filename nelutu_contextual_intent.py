"""Contextual intent gate for Neluțu. Classification never authorizes data export.

An isolated menu label is ambiguous: keep the established local help.
A general question mentioning a shared word must not trigger portal instructions.
"""
import re
import unicodedata


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value).lower())
    return " ".join(re.findall(r"[a-z0-9]+", "".join(
        ch for ch in value if not unicodedata.combining(ch)
    )))


_MENU = (
    "scoala", "invoire", "documente", "dosar personal", "scutiri medicale",
    "dosar bursa", "motivare absente parinte", "merit", "sociala orfan",
    "orfan", "sociala venit", "sociala", "venit", "sociala medicala",
    "medicala", "mame minore", "minore", "mame", "ces",
)
_PORTAL_MARKERS = (
    "portal", "aplicatie", "aplicatia", "catalog", "buton", "fila",
    "sectiune", "sectiunea", "meniu", "interfata", "contul",
    "autentificare", "numar matricol", "diriginte", "in platforma",
    "in sistem", "pe site", "in portal", "in aplicatie",
)
_PROCEDURAL = (
    "cum completez", "cum se completeaza", "cum incarc", "unde incarc",
    "cum trimit", "unde trimit", "cum depun", "unde depun",
    "cum solicit", "cum cer", "cum motivez", "cum justific absente",
    "cum vad", "unde vad", "cum accesez", "unde gasesc",
    "ce buton", "ce trebuie sa apas", "cum folosesc",
)
_SCHOOL_OBJECTS = (
    "scutire", "scutiri", "motivare absente", "absente", "invoire",
    "bilet de voie", "bursa", "burse", "dosar", "document",
    "instiintare", "notificare", "elev", "parinte", "scoala",
    "catalog", "portal", "cerere", "adeverinta",
)
_GENERAL_CONTEXT = (
    "soare", "luna", "astronomi", "planeta", "univers", "stele",
    "ziua afara", "noapte afara", "ziua in plus", "an bisect",
    "poveste", "poezie", "literatura", "istorie", "filosofie",
    "in natura", "in societate", "in general", "in medicina",
    "sensul cuvantului", "ce inseamna cuvantul", "etimologia",
)


def asks_about_portal(question):
    """Conservative local intent: require contextual evidence, not a word hit."""
    q = _norm(question)
    if not q:
        return False
    if q in _MENU:
        return True
    if any(marker in q for marker in _GENERAL_CONTEXT) and not any(
        marker in q for marker in _PORTAL_MARKERS
    ):
        return False
    if any(re.search(r"\b" + re.escape(x) + r"\b", q) for x in _PORTAL_MARKERS):
        return True
    if any(verb in q for verb in _PROCEDURAL) and any(
        re.search(r"\b" + re.escape(obj) + r"\b", q) for obj in _SCHOOL_OBJECTS
    ):
        return True
    # Explicit school transactions, not a mere mention of a shared term.
    return any(x in q for x in (
        "pleaca de la scoala", "plece de la scoala",
        "cerere de motivare", "cerere de invoire",
        "motivarea absentelor", "motivare absente",
        "scutire medicala pentru elev", "dosar de bursa",
        "bursa scolara", "bursa de merit", "bursa sociala",
        "confirmare de primire de la scoala",
    ))
