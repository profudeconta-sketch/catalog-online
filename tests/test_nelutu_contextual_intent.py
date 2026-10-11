"""Offline regression examples for contextual menu ambiguity."""
from nelutu_contextual_intent import asks_about_portal


def test_general_questions_not_portal():
    examples = (
        "Unde pleaca soarele cand este noapte afara?",
        "Unde se duce Luna cand este ziua afara?",
        "Mai explica-mi odata cum este cu ziua aia in plus?",
        "Ce merit are un om cinstit?",
        "Ce inseamna sociala in psihologie?",
        "Ce inseamna orfan in literatura?",
        "Ce este venitul unei firme?",
        "Ce inseamna mame in poezia asta?",
        "De ce este scoala importanta in societate?",
        "Ce documente istorice s-au descoperit?",
        "Ce este o scutire medicala in general?",
        "Ce inseamna CES in alt context?",
        "Cum se formeaza o bursa de apa?",
    )
    for question in examples:
        assert not asks_about_portal(question), question


def test_explicit_portal_requests_still_local():
    examples = (
        "Cum completez o scutire medicala in portal?",
        "Unde gasesc dosar personal in aplicatie?",
        "Cum solicit o invoire pentru elev?",
        "Cum depun cererea de motivare absente?",
        "Cum incarc documentele pentru bursa sociala?",
        "Unde vad instiintarea de la scoala?",
        "Explica-mi sectiunea Mame minore",
        "Ce buton apas in dosar bursa?",
        "Scoala",
        "Scutiri medicale",
    )
    for question in examples:
        assert asks_about_portal(question), question
