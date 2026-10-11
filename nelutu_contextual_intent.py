"""Context-based routing for Neluțu. Never authorizes external transmission.

A bare menu word is ambiguous; shared vocabulary in general questions does
not imply a portal request. Safety/privacy checks remain separate and first.
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
    "dosar", "personal", "scutiri", "medicale", "bursa", "motivare",
    "absente", "parinte", "mame", "social", "document", "scolar",
)
_PORTAL_MARKERS = (
    "portal", "aplicatia", "aplicatie", "catalogul", "catalog",
    "buton", "fila", "sectiune", "meniu", "interfata",
    "contul", "autentificare", "numar matricol", "diriginte",
    "in platforma", "in sistemul nostru", "pe site", "in portal",
    "in aplicatie", "din portal", "din aplicatie",
)
_SCHOOL_TRANSACTIONS = (
    "cerere de motivare", "cerere de invoire", "motivarea absentelor",
    "motivare absente", "scutire medicala pentru elev",
    "dosar de bursa", "bursa scolara", "bursa de merit",
    "bursa sociala", "bilet de voie", "pleaca de la scoala",
    "plece de la scoala", "incarc scutirea", "trimit scutirea",
    "incarc document", "trimit document", "depun cererea",
    "justific absentele", "motivez absente", "invoirea elevului",
)
_GENERAL_CONTEXT = (
    "soare", "luna", "astronomi", "planeta", "univers", "stele",
    "ziua afara", "noapte afara", "ziua in plus", "an bisect",
    "poveste", "poezie", "literatura", "istorie", "filosofie",
    "natura", "societate", "in general", "in medicina",
    "sensul cuvantului", "ce inseamna cuvantul", "etimologia",
    "economi", "financ", "afacer", "profit", "salariu",
    "familie", "mama", "copii", "copilarie", "orfelinat",
    "psiholog", "biolog", "stiinta", "geograf", "universitate",
    "vreme", "clima", "sanatate", "arta", "muzica",
)
_GENERAL_QUESTIONS = (
    "de ce", "ce inseamna", "ce este", "cine este", "cum functioneaza",
    "cum se formeaza", "cum se explica", "unde se duce",
    "unde pleaca", "care este diferenta", "povesteste",
    "explica mi despre", "spune mi despre",
)
_HELP_REQUEST = (
    "cum completez", "cum se completeaza", "cum incarc",
    "unde incarc", "cum trimit", "unde trimit", "cum depun",
    "unde depun", "cum solicit", "cum motivez", "cum justific",
    "cum accesez", "unde gasesc", "ce buton", "cum folosesc",
)


def _has(q, terms):
    return any(re.search(r"\b" + re.escape(term) + r"\b", q) for term in terms)


def classify_context(question):
    """Return 'portal', 'general', 'ambiguous', or 'unknown'."""
    q = _norm(question)
    if not q:
        return "unknown"
    if _has(q, _PORTAL_MARKERS) or _has(q, _SCHOOL_TRANSACTIONS):
        return "portal"
    if _has(q, ("incarc", "trimit", "depun", "completez", "completeaza", "solicit", "aproba", "motiv", "scutir")) and _has(q, ("document", "scutire", "cerere", "absente", "invoire", "bursa", "dosar", "elev")):
        return "portal"
    if _has(q, _GENERAL_CONTEXT):
        return "general"
    if q in _MENU:
        return "ambiguous"
    if _has(q, _HELP_REQUEST) and _has(q, _MENU):
        return "portal" if _has(q, ("cerere", "elev", "diriginte", "portal")) else "ambiguous"
    if _has(q, _GENERAL_QUESTIONS):
        return "general"
    # For ordinary sentences, do not infer a school operation from one word.
    return "unknown"


def asks_about_portal(question):
    return classify_context(question) == "portal"


def is_clearly_general(question):
    return classify_context(question) == "general"


def needs_clarification(question):
    return classify_context(question) == "ambiguous"
