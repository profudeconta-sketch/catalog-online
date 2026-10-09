"""Focused, read-only guidance for the parent's medical document workflow."""
from nelutu_assistant import NelutuAnswer
from nelutu_local_dialogue import _norm


def answer(question):
    words = set(_norm(question).split())
    medical = bool(words & {"scutire", "scutirea", "scutiri", "medicala", "medicale"})
    verify = bool(words & {"verific", "verifica", "confirm", "confirmare", "transmis", "trimis", "inregistrat"})
    if not (medical and verify):
        return None
    return NelutuAnswer(
        "parent_guide_medical_verified",
        "No, după autentificarea în Portalul Părinților mergi la "
        "**📁 Documente → 🏥 Scutiri medicale**. Alegi tipul, încarci "
        "fișierul și apeși butonul de transmitere. **Încărcarea singură "
        "nu înseamnă transmitere.** Așteaptă confirmarea portalului "
        "că documentul a fost salvat și înregistrat. Apoi verifică în "
        "**📁 Documente → Documente deja transmise dirigintelui**; "
        "acolo poți regăsi, redeschide sau descărca documentul transmis. "
        "Eu doar te îndrum, nu îl trimit în locul tău. 🤠",
    )
