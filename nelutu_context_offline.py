"""Deterministic fictional-context exercise; strictly offline."""
from __future__ import annotations

from nelutu_conversation_local import LocalConversation

FICTIONAL_SCRIPT = (
    ("user", "Sâmbătă plantez un trandafir."),
    ("model", "No, trandafirul are nevoie de un loc potrivit."),
    ("user", "Între timp, discutăm despre curcubeu."),
    ("model", "Curcubeul se vede când lumina întâlnește picături de apă."),
)


def answer_from_local_context(conversation: LocalConversation, question: str) -> str:
    """Only answer the exact fictional recall question, with local evidence."""
    if question != "Ce plantă am spus că plantez sâmbătă?":
        return "Întrebarea nu face parte din demonstrația fixă."
    for role, message in reversed(conversation.snapshot()):
        if role == "user" and "plantez un trandafir" in message.lower():
            return "Ai spus că sâmbătă plantezi un trandafir."
    return "Nu am această informație în memoria locală disponibilă."
