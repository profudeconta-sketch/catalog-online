"""Privacy guard for the isolated Neluțu dialogue experiment."""
from __future__ import annotations

from nelutu_assistant import NelutuAnswer
from nelutu_local_dialogue import _norm


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
