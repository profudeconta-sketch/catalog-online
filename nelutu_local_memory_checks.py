"""Offline checks for the existing bounded, isolated conversation buffer."""
from nelutu_conversation_local import LocalConversation

def check_memory():
    a, b = LocalConversation(), LocalConversation()
    for role, message in (
        ("user", "Salut, Neluțu!"),
        ("model", "No, bine ai venit!"),
        ("user", "Vorbim despre o carte."),
        ("model", "Desigur, despre carte."),
        ("user", "Mai ții minte subiectul?"),
    ):
        assert a.append(role, message)
    assert len(a.snapshot()) == 4
    assert b.snapshot() == ()
    a.clear()
    assert a.snapshot() == ()
    return True
