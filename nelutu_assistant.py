"""Neluțu — asistent local, gratuit și read-only pentru Portalul Părinților.

Nu importă module de stocare, nu scrie fișiere și nu apelează servicii AI externe.
Răspunsurile sunt determinate local dintr-o bază de cunoștințe controlată.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class NelutuAnswer:
    intent: str
    text: str
    source_label: str | None = None
    source_url: str | None = None
    serious: bool = False


LEGAL_SOURCES = {
    "lege_198": (
        "Legea învățământului preuniversitar nr. 198/2023, forma consolidată",
        "https://legislatie.just.ro/Public/DetaliiDocument/277920",
    ),
    "rofuip": (
        "ROFUIP — Ordinul nr. 5.726/2024, forma consolidată",
        "https://legislatie.just.ro/Public/DetaliiDocument/311706",
    ),
    "statut": (
        "Statutul elevului — Ordinul nr. 5.707/2024",
        "https://www.edu.ro/sites/default/files/_fi%C8%99iere/Legislatie/2024/OM_5707_2024_Statut_elev.pdf",
    ),
}

QUICK_TOPICS = (
    "Cum folosesc portalul?",
    "Note și medii",
    "Absențe și motivări",
    "Învoire",
    "Documente",
    "Burse",
    "Înștiințări de la școală",
    "Drepturi și obligații",
)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _has_any(q: str, words: Iterable[str]) -> bool:
    return any(_norm(word) in q for word in words)


def _source(key: str):
    label, url = LEGAL_SOURCES[key]
    return label, url


def answer(question: str) -> NelutuAnswer:
    q = _norm(question)
    if not q:
        return NelutuAnswer(
            "empty",
            "No, amu m-ai prins cu traista goală. 😄 Scrie-mi ce vrei să afli și Neluțu își pune rotițele la treabă.",
        )

    # Situații sensibile: claritate înaintea glumei.
    if _has_any(q, ("violenta", "lovit", "batut", "bullying", "hartuit", "abuz", "amenintat", "sinucidere", "autovatam", "drog", "agresiune")):
        return NelutuAnswer(
            "safety",
            "Îmi pare rău că e vorba despre o situație serioasă. Aici las glumele deoparte. "
            "Dacă există pericol imediat, cere ajutorul serviciilor de urgență. Pentru o situație școlară, "
            "anunță cât mai repede dirigintele și conducerea școlii; cazurile de violență trebuie tratate prin "
            "procedurile școlii și, când este necesar, împreună cu instituțiile competente. Eu pot explica portalul "
            "și regulile generale, dar nu pot investiga cazul și nu pot înlocui un specialist.",
            serious=True,
        )

    if _has_any(q, ("cum folosesc portalul", "portal", "meniu", "unde gasesc", "cum functioneaza")):
        return NelutuAnswer(
            "portal",
            "Ie mă! Portalul îi mai cuminte decât pare. 😄 După autentificare ai trei zone mari: "
            "Școală — pentru comunicările primite, Învoire — pentru cereri de plecare, și Documente — pentru ce trimiți dirigintelui. "
            "Mai jos vezi situația școlară: medii, note și absențe. Spune-mi ce vrei să faci și te duc până la buton; "
            "nu-l apăs eu, că n-am degete, numa' pretenții. 😂",
        )

    if _has_any(q, ("pin", "autentific", "logare", "matricol", "nu pot intra")):
        return NelutuAnswer(
            "login",
            "No binie mă, la poarta digitală ne trebuie numărul matricol și PIN-ul corect. 😄 "
            "Dacă nu te poți autentifica, verifică exact caracterele introduse. Dacă tot nu merge, contactează dirigintele; "
            "Neluțu nu vede, nu schimbă și nu recuperează PIN-uri. Și-i mai sănătos așa — dacă le-aș ști pe toate, m-aș speria și eu de mine. 😂",
        )

    if _has_any(q, ("nota", "note", "medie", "medii", "clasament", "situatia scolara")):
        return NelutuAnswer(
            "grades",
            "Aha, no, aici intrăm în ograda notelor. 😄 În portal poți vedea notele și mediile afișate pentru discipline/module, "
            "plus indicatorii situației școlare. Neluțu îți explică ce vezi, dar nu poate pune, șterge sau modifica nicio notă. "
            "Pentru o neconcordanță concretă, vorbește cu profesorul/dirigintele — eu îs bun la explicații, nu la rescris catalogul. 😂",
        )

    if _has_any(q, ("absenta", "absente", "motivare", "motivez", "scutire")):
        label, url = _source("rofuip")
        return NelutuAnswer(
            "absences",
            "No, amu cu absențele să fim preciși, că ele n-au simțul umorului. 😄 "
            "ROFUIP prevede că motivarea se face pe baza actelor justificative. Pentru cererea scrisă a părintelui există limita "
            "de 40 de ore de curs într-un an școlar, fără a depăși 20% din orele unei discipline; cererea este adresată dirigintelui "
            "și trebuie avizată în prealabil de director. Actele justificative se prezintă în termenul prevăzut de regulament. "
            "În portal, formularul te ajută să transmiți documentul; decizia de motivare aparține persoanelor competente din școală. "
            "Api eu pot număra orele, da' director încă nu m-or făcut. 😂",
            label, url,
        )

    if _has_any(q, ("invoire", "plecare", "plece", "iesire", "parasirea scolii")):
        return NelutuAnswer(
            "leave",
            "Ie mă. 😄 În fila „Învoire” poți completa cererea disponibilă pentru elev. După trimitere, urmărești în portal starea ei. "
            "Neluțu nu aprobă și nu refuză învoiri — eu îs portar doar la vorbe. 😂 Dacă situația este urgentă sau neclară, contactează dirigintele.",
        )

    if _has_any(q, ("document", "incarc", "pdf", "dosar", "medical", "adeverinta")):
        return NelutuAnswer(
            "documents",
            "No binie mă, la „Documente” îi mica noastră poștă fără timbre. 😄 Alegi categoria potrivită, atașezi documentul cerut și folosești "
            "butonul de transmitere. O simplă previzualizare nu înseamnă trimitere. Când portalul confirmă transmiterea, documentul este înregistrat "
            "în fluxul către diriginte. Neluțu nu poate încărca ori trimite în locul tău — că după aia mă trezesc și secretar, și poștaș. 😂",
        )

    if _has_any(q, ("bursa", "burse", "merit", "sociala", "ces", "orfan", "venit")):
        return NelutuAnswer(
            "scholarship",
            "Aha, no, la burse alegem întâi categoria potrivită din „Dosar bursă”, apoi încărcăm documentul corespunzător. 😄 "
            "Eu pot explica unde se află fiecare opțiune, dar nu stabilesc eligibilitatea și nu aprob bursa. Pentru un caz concret sau acte lipsă, "
            "secretariatul/dirigintele îți poate confirma cerințele. N-aș vrea să promit bani cu buzunarele mele digitale goale. 😂",
        )

    if _has_any(q, ("instiintare", "notificare", "comunicare", "citit", "confirmare", "confirmat")):
        return NelutuAnswer(
            "school_notice",
            "No, aici mecanismul îi făcut să nu joace alba-neagra cu „citit/necitit”. 😄 O comunicare de la școală devine accesată în sistem "
            "când documentul este deschis din contul autentificat al părintelui; simplul mesaj WhatsApp nu ține locul acelei confirmări interne. "
            "WhatsApp îi clopoțelul de la poartă, portalul îi registrul. 😂",
        )

    if _has_any(q, ("whatsapp", "wapp", "mesaj")):
        return NelutuAnswer(
            "whatsapp",
            "Ie mă. 😄 Butonul WhatsApp doar pregătește mesajul; trimiterea o faci tu manual în WhatsApp. "
            "Confirmările oficiale ale portalului rămân în sistemul autentificat. Cu alte cuvinte: eu îți pun plicul în mână, da' nu fug cu el până la destinatar. 😂",
        )

    if _has_any(q, ("drept", "obligatie", "lege", "legal", "regulament", "statut")):
        label, url = _source("lege_198")
        return NelutuAnswer(
            "legal_general",
            "No, amu intrăm pe teren juridic și Neluțu își îndreaptă clopul. 😄 Legea învățământului preuniversitar nr. 198/2023 stabilește, între altele, "
            "participarea și responsabilitatea părinților, interesul superior al elevului, respectul, nediscriminarea și comunicarea în comunitatea școlară. "
            "Pot explica o regulă generală și îți arăt sursa, dar pentru interpretarea unui caz concret sau o contestație trebuie discutat cu dirigintele, "
            "directorul ori un specialist competent. Eu am clop, nu robă pe USB. 😂 Spune-mi exact tema: absențe, sancțiuni, documente, drepturi sau altceva.",
            label, url,
        )

    if _has_any(q, ("salut", "buna", "servus", "ceau", "cine esti", "nelutu")):
        return NelutuAnswer(
            "hello",
            "Ie mă, servus! Eu-s Neluțu. 😄 Mocan digital de pe Valea Arieșului: explic portalul, descurc regulile și mai scap câte-o glumă printre butoane. "
            "Nu mă supăr, nu judec și nu modific nimic în catalog. Întreabă-mă orice despre portal sau viața școlară — dacă nu știu, îți spun, "
            "că-i mai ieftin decât să inventez. 😂",
        )

    return NelutuAnswer(
        "fallback",
        "No, amu m-ai băgat oleacă-n ceață. 😄 Nu vreau să scot un răspuns din clop doar ca să par deștept. "
        "Încearcă să-mi spui întrebarea cu alte cuvinte sau alege una dintre temele rapide: portal, note, absențe, învoire, documente, burse, "
        "înștiințări ori drepturi. Dacă-i un caz concret pe care nu-l pot lămuri sigur, te trimit la diriginte/director/specialist — "
        "mai bine un Neluțu prudent decât unul care vorbește ca moara fără apă. 😂",
    )


def read_only_contract() -> dict:
    """Contract inspectabil/testabil: motorul nu are capabilități de mutație."""
    return {
        "writes_primary_data": False,
        "writes_files": False,
        "calls_paid_ai": False,
        "calls_external_ai": False,
        "can_change_grades": False,
        "can_send_documents": False,
        "can_approve_requests": False,
    }
