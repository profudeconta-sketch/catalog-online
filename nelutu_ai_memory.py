"""Opt-in memory prototype for Neluțu, isolated from the school catalog.

In-memory per-session history only. No database, network, global user profile,
student information or automatic training. Long-term memory needs separate
privacy review and explicit user consent before implementation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from nelutu_ai_privacy import approved_external_question
from nelutu_ai_answer_guard import safe_memory_answer

MAX_TURNS = 30

@dataclass
class NelutuMemory:
    """Owned by ONE Streamlit session; never share between accounts."""
    turns: list[dict[str, str]] = field(default_factory=list)

    def add(self, question: str, answer: str) -> bool:
        if not approved_external_question(question):
            return False
        if not safe_memory_answer(answer):
            return False
        self.turns.append({"role": "user", "content": question})
        self.turns.append({"role": "assistant", "content": answer})
        self.turns = self.turns[-2 * MAX_TURNS:]
        return True

    def clear(self) -> None:
        self.turns.clear()

    def recent_local(self, count: int = 8) -> list[dict[str, str]]:
        """Local display only; never pass to an external AI provider."""
        if count <= 0:
            return []
        return [dict(item) for item in self.turns[-min(count, 2 * MAX_TURNS):]]

    def size(self) -> int:
        return len(self.turns) // 2
