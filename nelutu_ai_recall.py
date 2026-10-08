"""Local retrieval of approved general educational conversation memories.

Never sends memory to a provider, never persists it, and does not train a model.
"""
from __future__ import annotations
from dataclasses import dataclass
from nelutu_ai_privacy import normalize, approved_external_question

STOPWORDS = frozenset("de ce la in din si sau este sunt cu pe un o care cum pentru mai noi".split())

@dataclass(frozen=True)
class RecalledTurn:
    question: str
    answer: str
    relevance: float

def _words(text: str) -> set[str]:
    return {w for w in normalize(text).split() if len(w) >= 3 and w not in STOPWORDS}

def recall_local(memory, query: str, limit: int = 3) -> list[RecalledTurn]:
    """Returns relevant copies of approved question-answer pairs, newest first on ties.

    The query must itself be an approved generic question; no arbitrary personal
    query is used to search memory. Retrieval is only a local UI aid.
    """
    if not approved_external_question(query) or limit <= 0:
        return []
    target = _words(query)
    if not target:
        return []
    turns = memory.recent_local(2 * memory.size())
    matches = []
    for i in range(0, len(turns) - 1, 2):
        q, a = turns[i], turns[i + 1]
        if q.get("role") != "user" or a.get("role") != "assistant":
            continue
        question, answer = q.get("content", ""), a.get("content", "")
        if not approved_external_question(question):
            continue
        words = _words(question)
        if not words:
            continue
        common = len(target & words)
        if common == 0:
            continue
        score = common / len(target | words)
        matches.append((score, i, RecalledTurn(question, answer, score)))
    matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in matches[:min(limit, 5)]]
