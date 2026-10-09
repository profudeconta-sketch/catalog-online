"""Privacy guard for the isolated Neluțu dialogue experiment."""
from __future__ import annotations

from nelutu_assistant import NelutuAnswer
from nelutu_local_dialogue import _norm


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
