"""Adaptor experimental pentru integrare ulterioară; nu modifică portalul activ."""
from __future__ import annotations
import re
from nelutu_parent_guide import answer_parent
from nelutu_parent_flows import answer as parent_flow_guidance
from nelutu_local_dialogue import DialogueState, reply as local_reply, _norm
from nelutu_education_dialogue import educational_reply
from nelutu_subject_importance import subject_reply
from nelutu_privacy_guard import guard as privacy_guard, credential_warning, access_guidance, authority_guard, director_class_guidance, third_party_credential_guard

def _school_topic(question):
    """Explicit school subjects; keep privacy and safety routing first."""
    q = _norm(question)
    words = set(q.split())
    from nelutu_assistant import NelutuAnswer
    if "40" in words and ({"absente", "absenta", "ore"} & words):
        return NelutuAnswer("absences_40", "No, regula celor 40 de ore se referă la limita anuală de absențe care pot fi motivate la cererea scrisă a părintelui sau a elevului major, în condițiile ROFUIP și fără depășirea a 20% din orele unei discipline. Nu este o permisiune de a lipsi și nici o motivare automată. Pentru aplicarea concretă se verifică cererea și regulile școlii.")
    if "contabil" in q and ("baz" in q or "contabilitatii" in words):
        return NelutuAnswer("education_accounting", "No, la Bazele contabilității învățăm despre bunuri, datorii, capitaluri, venituri și cheltuieli, documente justificative și înregistrarea operațiunilor unei firme. Pe scurt, cum urmărim corect activitatea economică.")
    if ("turist" in q or "hotel" in words) and ({"structuri", "primire", "facem", "invatam"} & words):
        return NelutuAnswer("education_tourism", "No, la Structuri de primire turistică învățăm despre hoteluri, pensiuni, clasificare, servicii, rezervări și primirea oaspeților. Ospitalitatea bună se învață, nu-i numai un zâmbet la recepție!")
    # Educația fizică (sportul) nu este disciplina Fizică.\n    if ({"educatie", "educatia"} & words and {"fizica", "fizice"} & words) or "sport" in words:\n        return None  # Biblioteca disciplinelor oferă explicația despre mișcare și sănătate.\n    if "fizica" in words or "fizicii" in words:
        return NelutuAnswer("education_physics", "No, fizica explică mișcarea, forțele, energia, căldura și electricitatea. De aceea pricepem cum frânează un vehicul, de ce ne protejează centura și cum funcționează aparatele.")
    if "chimie" in words or "chimia" in words or "chimiei" in words:
        return NelutuAnswer("education_chemistry", "No, chimia ne ajută să înțelegem substanțele și transformările lor: gătitul, curățenia, apa, medicamentele și protejarea mediului. Învățăm și cum să folosim produsele în siguranță.")
    school_word = bool({"scoala", "scolii", "scoal", "invatatura", "carte"} & words or "copilu" in words)
    school_purpose = bool({"rost", "buna", "bun", "atata", "folos", "trebuie", "trebe", "dc", "dece", "pt", "pentru"} & words or "la cei buna" in q)
    if school_word and school_purpose:
        return NelutuAnswer("education_purpose", "No, școala nu-i numai pentru note. Ne învață să gândim, să punem întrebări, să lucrăm cu alții și să deprindem o meserie. Nu folosim fiecare formulă zilnic, dar felul în care învățăm să rezolvăm probleme ne rămâne!")
    return None

def answer_parent_dialogue(question, context=None, state=None):
    """Prioritizează întotdeauna routerul portalului; continuitatea este limitată."""
    state = state if isinstance(state, DialogueState) else DialogueState()
    # Filtrul de risc al dialogului nou se execută înainte de rutarea portalului.
    # Niciun răspuns neserios al routerului vechi nu poate masca o alertă detectată.
    safety, _ = local_reply(question, DialogueState())
    if safety is not None and safety.serious:
        return safety, DialogueState()
    # Limita de lungime nu poate fi ocolită de un intent al portalului.
    if isinstance(question, str) and len(question) > 1200:
        return safety, DialogueState()
    privacy = credential_warning(question) or authority_guard(question) or third_party_credential_guard(question) or privacy_guard(question) or access_guidance(question) or director_class_guidance(question)
    if privacy is not None:
        return privacy, DialogueState()
    # Saluturile simple nu trebuie interceptate de routerul generic al portalului.
    social, social_state = local_reply(question, state)
    if social is not None and social.intent == "smalltalk":
        return social, social_state
    # Întrebările explicite despre plafonul de 40 de ore primesc întâi
    # explicația regulii, nu instrucțiunile generale pentru formular.
    normalized = _norm(question)
    if '40' in normalized.split() and any(term in normalized.split() for term in ('absente', 'absenta', 'ore')):
        rule = _school_topic(question)
        if rule is not None and rule.intent == 'absences_40':
            return rule, DialogueState()
    flow = parent_flow_guidance(question)
    if flow is not None and (flow.intent != 'parent_flow_school' or not _school_topic(question)) :
        return flow, DialogueState()
    school = _school_topic(question)
    if school is not None:
        return school, DialogueState()
    # Continuarile educationale deja stabilite au prioritate fata de fallback-ul
    # vechi; fluxurile portalului si filtrele de confidentialitate raman primele.
    if state.topic == "purpose":
        local_followup, next_state = local_reply(question, state)
        if local_followup is not None and local_followup.intent.startswith("education_followup_"):
            return local_followup, next_state
    if state.topic == "social_wait" and social is not None and social.intent == "smalltalk_followup":
        return social, social_state
    subject = subject_reply(question)
    if subject is not None:
        return subject, DialogueState()
    base = answer_parent(question, context)
    # Privacy-sensitive requests require a dedicated pre-routing guard.

    # Întrebările educaționale explicite pot fi mascate de clasificarea
    # prea largă «portal_component». Nu schimbăm însă ghidurile portalului.
    if base.intent == "portal_component":
        educational = educational_reply(question)
        portal_terms = ("portal", "aplicatie", "buton", "document", "nota", "note",
                        "absente", "invoire", "scutire", "mesaj", "notificare",
                        "catalog", "trimite", "incarc", "cont", "parola")
        normalized = _norm(question)
        if educational is not None and not any(
            re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", normalized)
            for t in portal_terms
        ):
            return educational, DialogueState(educational.intent.removeprefix("education_"), 1)
    # Orice răspuns de siguranță, portal, legal sau bazat pe date rămâne autoritar.
    if base.serious or base.intent not in ("fallback", "clarification"):
        # Un subiect educațional explicit poate actualiza tema, fără a înlocui
        # răspunsul deja stabilit de routerul principal.
        if base.intent.startswith("education_"):
            return base, DialogueState(base.intent.removeprefix("education_"), 1)
        return base, DialogueState()
    local, next_state = local_reply(question, state)
    if local is not None:
        return local, next_state
    if base.intent in ('fallback', 'clarification'):
        from nelutu_assistant import NelutuAnswer
        return NelutuAnswer('clarification', 'No io n-am priceput nimic din ce vrei să mă întrebi. Reformulează, te rog, că nu vreau să vorbesc prostii! 🤠'), DialogueState()
    return base, DialogueState()
