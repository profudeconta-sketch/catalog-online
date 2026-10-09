"""Privacy guard for the isolated Neluțu dialogue experiment."""
from __future__ import annotations

from nelutu_assistant import NelutuAnswer
from nelutu_local_dialogue import _norm


def third_party_credential_guard(question):
    words = set(_norm(question).split())
    secrets = {"pin", "parola", "password", "pinul", "parola"}
    demands = {"spune", "spui", "da", "dami", "arata", "dezvaluie", "furnizeaza", "comunica", "vreau"}
    other_person = {"elevului", "elevul", "elevei", "eleva", "copilului", "copilul", "parintelui", "altcuiva"}
    if words & secrets and words & demands and words & other_person:
        return NelutuAnswer(
            "third_party_credential_refusal",
            "Nu pot comunica PIN-ul sau parola altei persoane, nici în situații urgente. "
            "Părintele trebuie să folosească procedura autorizată de recuperare "
            "a accesului, prin diriginte. Nu trimiteți date de autentificare aici.",
            serious=True,
        )
    return None


def authority_guard(question):
    words = set(_norm(question).split())
    roles = {"director", "directorul", "diriginte", "dirigintele", "administrator", "profesor"}
    secrets = {"pin", "parola", "password"}
    demands = {"spune", "spui", "da", "arata", "dezvaluie", "ordon", "furnizeaza"}
    if words & roles and words & secrets and words & demands:
        return NelutuAnswer(
            "authority_credential_refusal",
            "Nu pot comunica date de autentificare pe baza unei functii declarate "
            "in conversatie. Folositi procedurile oficiale ale scolii.",
            serious=True,
        )
    return None


def director_class_guidance(question):
    words = set(_norm(question).split())
    role = bool(words.intersection({"director", "directorul", "directoarea"}))
    class_scope = bool(words.intersection({"clasa", "clasei", "clase", "claselor"}))
    consult = bool(words.intersection({"consulta", "consulte", "vedea", "vede", "accesa", "verifica"}))
    if not (role and class_scope and consult):
        return None
    return NelutuAnswer(
        "director_class_guidance",
        "În aplicațiile verificate nu am identificat o interfață dedicată "
        "directorului pentru consultarea situației unei clase. "
        "Catalogul profesorului include rapoarte școlare, însă accesul "
        "și comunicarea lor trebuie stabilite prin procedurile autorizate "
        "ale școlii. Nu pot acorda drepturi de acces din conversație.",
        serious=True,
    )


def credential_warning(question):
    q = _norm(question)
    words = q.split()
    for i, word in enumerate(words):
        if word not in ("pin", "parola", "password"):
            continue
        following = words[i + 1:i + 5]
        if any(part.isdigit() and len(part) >= 3 for part in following):
            return NelutuAnswer(
                "credential_privacy",
                "Nu introduceți PIN-uri sau parole în conversație. Nu pot verifica "
                "identitatea ori accesa situația școlară folosind date scrise aici. "
                "Utilizați autentificarea din portalul oficial. Dacă ați transmis "
                "date de acces reale, schimbați-le prin metoda autorizată.",
                serious=True,
            )
    return None


def access_guidance(question):
    words = set(_norm(question).split())
    if not words.intersection({"pin", "parola", "password"}):
        return None
    if words.intersection({"uitat", "pierdut", "recuperez", "recuperare"}):
        return NelutuAnswer("access_forgotten",
            "Pentru un PIN uitat, contactează dirigintele pentru procedura autorizată. "
            "Nu trimite date de acces în conversație.", serious=True)
    if words.intersection({"schimb", "schimba", "schimbare", "modific", "modifica"}):
        return NelutuAnswer("access_change",
            "Nu pot confirma existența unui buton de schimbare a PIN-ului în portal. "
            "Contactează dirigintele pentru procedura autorizată.", serious=True)
    return None


def guard(question):
    words = set(_norm(question).split())
    personal = bool(words.intersection({
        "elevul", "eleva", "elevului", "elevei", "copilului",
        "fiul", "fiica", "copilul", "baiatul", "fata"
    }))
    records = bool(words.intersection({
        "nota", "note", "notele", "media", "medie", "mediile",
        "absente", "absentele"
    }))
    if not (personal and records):
        return None
    return NelutuAnswer(
        "student_records_privacy",
        "Nu pot consulta sau comunica notele ori absențele unui elev din această conversație. "
        "Pentru situația școlară, folosiți contul autorizat din portal. "
        "Pot explica afișarea notelor și mediilor fără date personale.",
        serious=True,
    )
