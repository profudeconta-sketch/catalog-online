"""Continuitate locală pentru dialogul lui Neluțu, fără rețea sau date școlare.

Modul experimental independent: apelantul păstrează starea doar în sesiune.
Nu interpretează liber orice text și nu pretinde că este AI generativ.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata

from nelutu_assistant import NelutuAnswer
from nelutu_education_dialogue import TOPICS, educational_reply
from nelutu_pedagogy_library import lookup as library_lookup

def _norm(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

@dataclass(frozen=True)
class DialogueState:
    topic: str = ""
    turns: int = 0

# Urmărim exclusiv tema, nu păstrăm mesajele sau identitatea utilizatorului.
_FOLLOWUPS = {
    "technical": "No, putem porni de la o activitate practică simplă: alegem ceva ce-i place copilului, identificăm un pas pe care îl poate exersa și îi observăm progresul. Ce activitate îl interesează?",
    "purpose": "No, un exemplu bun îi să legăm lecția de o problemă reală: un calcul pentru cumpărături, o explicație despre natură sau o alegere argumentată. Despre ce disciplină vorbim?",
    "motivation": "No, încercăm un pas mic și realizabil, fără comparații cu alți copii: un obiectiv pentru săptămâna aceasta și o discuție calmă despre ce l-a împiedicat. Ce i se pare cel mai greu?",
    "family": "No, ajută să pornim de la o observație concretă și să întrebăm ce sprijin ar fi util, fără să căutăm vinovați. Vreți să formulăm un mesaj respectuos către școală?",
    "future": "No, putem pune pe hârtie trei lucruri: ce îi place, ce deprinderi are și ce ar vrea să încerce. Apoi discutăm opțiunile, fără să hotărâm în locul lui. Cu ce începem?",
}
_FOLLOWUP_MARKERS = (
    "da", "sigur", "continua", "continuam", "spune mi mai mult",
    "explica", "detaliaza", "un exemplu", "da mi un exemplu",
    "cum asa", "de ce", "si apoi", "hai", "te rog",
)
_RESET_MARKERS = ("schimbam subiectul", "alta tema", "alt subiect", "de la inceput")

def reply(question: str, state: DialogueState | None = None) -> tuple[NelutuAnswer | None, DialogueState]:
    """Răspuns general, local; numai tema este păstrată între mesaje."""
    state = state if isinstance(state, DialogueState) else DialogueState()
    q = _norm(question)
    if not q:
        return None, state
    if len(question) > 1200:
        return NelutuAnswer("clarification", "No, mesajul îi cam lung. Îl putem lua pe bucăți, fără nume sau date personale?"), DialogueState()
    if any(marker in q for marker in _RESET_MARKERS):
        return NelutuAnswer("clarification", "Sigur. Despre ce temă nouă ați dori să vorbim?"), DialogueState()
    # Detectarea unei teme noi are prioritate față de continuarea celei vechi.
    fresh = educational_reply(question)
    if fresh is not None:
        topic = fresh.intent.removeprefix("education_")
        return fresh, DialogueState(topic, min(state.turns + 1, 20))
    if state.topic in _FOLLOWUPS and q in _FOLLOWUP_MARKERS:
        return NelutuAnswer("education_followup_" + state.topic, _FOLLOWUPS[state.topic]), DialogueState(state.topic, min(state.turns + 1, 20))
    # Întrebările neînțelese nu primesc răspuns inventat pe baza temei vechi.
    known = library_lookup(question)
    if known is not None:
        return known, DialogueState("", min(state.turns + 1, 20))
    return None, DialogueState("", min(state.turns + 1, 20))

def contract() -> dict:
    return {"uses_network": False, "writes_data": False, "reads_student_records": False,
            "stores_message_history": False, "generative_ai": False}
