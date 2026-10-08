"""Local answer reuse is opt-in and never writes to school data."""
from __future__ import annotations
from dataclasses import dataclass
from nelutu_ai_memory import NelutuMemory
from nelutu_ai_recall import recall_local
from nelutu_ai_privacy import approved_external_question

@dataclass(frozen=True)
class MemorySuggestion:
    answer: str
    source: str

def suggest_previous_answer(memory: NelutuMemory, question: str) -> MemorySuggestion | None:
    """Show an exact previous answer as a memory, never as verified knowledge."""
    if not approved_external_question(question):
        return None
    matches = recall_local(memory, question, limit=1)
    if not matches or matches[0].relevance != 1.0:
        return None
    return MemorySuggestion(answer=matches[0].answer, source="previous_session_answer")

def remember_approved_exchange(memory: NelutuMemory, question: str, answer: str) -> bool:
    """Store only allowlisted educational exchanges in the current session."""
    return memory.add(question, answer)
