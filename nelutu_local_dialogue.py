"""Continuitate locală pentru dialogul lui Neluțu, fără rețea sau date școlare.

Modul experimental independent: apelantul păstrează starea doar în sesiune.
Nu interpretează liber orice text și nu pretinde că este AI generativ.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata

from nelutu_assistant import NelutuAnswer
from nelutu_education_dialogue import educational_reply
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
_SECOND_FOLLOWUPS = {
    "technical": "Așe, un pas concret ar fi să încercăm o activitate scurtă de atelier și să observăm ce i-a plăcut. Nu putem alege meseria în locul copilului.",
    "purpose": "De pildă, la cumpărături folosim matematica pentru rest și buget, iar la o știre folosim gândirea critică pentru a verifica informația.",
    "motivation": "Putem stabili un obiectiv mic, verificabil, și să apreciem efortul. Dacă dificultatea persistă, o discuție cu profesorul poate clarifica sprijinul potrivit.",
    "family": "Un mesaj util spune ce am observat, întreabă cum vede școala situația și propune un pas comun, fără acuzații.",
    "future": "Putem compara două opțiuni după interese, deprinderi și oportunități de învățare, fără promisiuni despre rezultatul final.",
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
    if not isinstance(question, str):
        return None, DialogueState()
    q = _norm(question)
    if not q:
        return None, state
    # Mesajele sensibile nu sunt tratate drept conversație educațională obișnuită.
    sensitive = ("ma loveste", "m a lovit", "ma bate", "violenta", "abuz",
                 "ma sinucid", "vreau sa mor", "imi fac rau", "ma ameninta",
                 "hartuit", "bullying", "agresat", "agresiune")
    sensitive += ("ma hartuiesc", "ma hartuieste", "ma lovesc", "m au lovit",
                  "vreau sa ma omor", "nu mai vreau sa traiesc", "ma ranesc",
                  "imi este frica acasa", "sunt batut", "sunt batuta")
    if any(re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", q) for term in sensitive):
        return NelutuAnswer("sensitive_redirect",
            "Îmi pare rău că treceți printr-o situație dificilă. Dacă există pericol imediat, "
            "apelați 112. Pentru sprijin în școală, discutați cu dirigintele sau consilierul școlar. "
            "Nu este nevoie să-mi transmiteți nume ori alte date personale.", serious=True), DialogueState()
    if len(question) > 1200:
        return NelutuAnswer("clarification", "No, mesajul îi cam lung. Îl putem lua pe bucăți, fără nume sau date personale?"), DialogueState()
    if any(q == marker or q.startswith(marker + " ") for marker in _RESET_MARKERS):
        return NelutuAnswer("clarification", "Sigur. Despre ce temă nouă ați dori să vorbim?"), DialogueState()
    # Conversație socială simplă, fără a inventa evenimente sau date personale.
    # Potrivire pe expresii întregi: întrebările fără sens rămân la fallback.
    social = {
        "ce mai faci": "No, bine-s, mulțam de întrebare! 🤠 Stau aici, cu vorba pregătită și cu mintea trează, să dau o mână de ajutor. Da' tu ce mai faci?",
        "cum esti": "No, bine-s, mulțam! 🤠 Pregătit să povestim ori să descurcăm vreo întrebare. Tu cum ești?",
        "cum o duci": "No, o duc bine, cât poate un Neluțu digital! 🤠 Cu ce te pot ajuta?",
        "salut": "No, servus! 🤠 Bine-ai venit! Cu ce te pot ajuta?",
        "servus": "Servus, servus! 🤠 No, ce mai povestim?",
        "buna ziua": "Bună ziua și bine-ați venit! 🤠 Cu ce vă pot ajuta?",
        "buna seara": "Bună seara! 🤠 No, spuneți, cu ce vă pot ajuta?",
        "multumesc": "Cu drag! 🤠 No, să fie cu folos!",
        "mersi": "Cu mare drag! 🤠",
    }
    social_q = re.sub(r"^(?:(?:no|apai|pai|ma|hei)\\s+)+", "", q)
    social_q = re.sub(r"\\s+(?:nelutu|nelutule|astazi|azi)$", "", social_q)
    if social_q in social:
        return NelutuAnswer("smalltalk", social[social_q]), DialogueState()
    # Detectarea unei teme noi are prioritate față de continuarea celei vechi.
    fresh = educational_reply(question)
    if fresh is not None:
        topic = fresh.intent.removeprefix("education_")
        return fresh, DialogueState(topic, 1 if topic != state.topic else min(state.turns + 1, 20))
    # Răspuns la disciplina cerută în cadrul temei educației, fără istoric de mesaje.
    # Nu extindem această regulă la întrebări necunoscute despre elevi.
    # Exemple sigure pentru discipline menționate ca răspuns la întrebarea lui Neluțu.
    # Se potrivesc doar răspunsurile scurte despre disciplină, nu întrebările despre elevi.
    if state.topic == "purpose" and state.turns >= 1:
        subject_examples = {
            "matematica": "La matematică, un preț de 100 de lei redus cu 20% ajunge la 80 de lei. Așe verificăm o ofertă.",
            "romana": "La limba română, exersăm să citim atent un contract și să scriem un mesaj clar și respectuos.",
            "limba romana": "La limba română, exersăm să citim atent un contract și să scriem un mesaj clar și respectuos.",
            "istorie": "La istorie, comparăm sursele și învățăm să verificăm afirmațiile înainte să le credem.",
            "fizica": "La fizică, înțelegem de ce centura de siguranță contează când un vehicul frânează brusc.",
            "engleza": "La engleză, putem înțelege instrucțiuni, conversații și informații utile într-o călătorie.",
            "chimie": "La chimie, învățăm de ce nu amestecăm produse de curățenie fără să citim etichetele."
        }
        subject = re.sub(r"^(?:la |despre )", "", q)
        subject = re.sub(r"(?: mai explica(?: mi)?| explica(?: mi)?| da mi un exemplu| mai detaliaza)$", "", subject)
        # Recunoastem si fraze complete despre disciplina, nu doar numele izolat.
        requested_example = any(marker in q for marker in (
            "exemplu", "explica", "detalia", "arata", "cum folos", "la ce ajuta"
        ))
        mentioned = next((
            name for name in sorted(subject_examples, key=len, reverse=True)
            if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", q)
        ), None)
        if mentioned is not None and requested_example:
            subject = mentioned
        if subject in subject_examples:
            return NelutuAnswer("education_followup_purpose",
                "No, uite un exemplu concret. 🤠 " + subject_examples[subject] +
                " Vrei să explorăm și o altă situație practică?"), DialogueState("purpose", min(state.turns + 1, 20))
    if state.topic in _FOLLOWUPS and (q in _FOLLOWUP_MARKERS or q.startswith("poti sa detaliezi") or q.startswith("mai explica") or q.startswith("da mi un exemplu ")):
        if state.turns >= 3:
            return NelutuAnswer("clarification", "No, ca să nu repet aceeași poveste, spuneți-mi ce aspect anume doriți să aprofundăm."), DialogueState(state.topic, state.turns)
        message = _FOLLOWUPS[state.topic] if state.turns <= 1 else _SECOND_FOLLOWUPS[state.topic]
        return NelutuAnswer("education_followup_" + state.topic, message), DialogueState(state.topic, min(state.turns + 1, 20))
    # Întrebările neînțelese nu primesc răspuns inventat pe baza temei vechi.
    known = library_lookup(question)
    if known is not None:
        return known, DialogueState("", min(state.turns + 1, 20))
    return None, DialogueState("", min(state.turns + 1, 20))

def contract() -> dict:
    return {"uses_network": False, "writes_data": False, "reads_student_records": False,
            "stores_message_history": False, "generative_ai": False}
