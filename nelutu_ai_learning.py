"""A memory is not a verified fact: controlled local learning ledger.

No automatic self-training, network calls, student records or shared global memory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from nelutu_ai_privacy import approved_external_question
from nelutu_ai_answer_guard import safe_memory_answer

@dataclass(frozen=True)
class Lesson:
    question: str
    answer: str
    status: str
    reviewed_by: str

@dataclass
class LearningNotebook:
    lessons: dict[str, Lesson] = field(default_factory=dict)

    def propose(self, question: str, answer: str) -> bool:
        if not approved_external_question(question) or not safe_memory_answer(answer):
            return False
        self.lessons[question] = Lesson(question, answer, "pending", "")
        return True

    def approve(self, question: str, *, reviewer: str) -> bool:
        if not isinstance(reviewer, str) or not reviewer.strip():
            return False
        lesson = self.lessons.get(question)
        if lesson is None or lesson.status != "pending":
            return False
        self.lessons[question] = Lesson(lesson.question, lesson.answer, "approved", reviewer.strip())
        return True

    def recall_verified(self, question: str) -> str | None:
        lesson = self.lessons.get(question)
        return lesson.answer if lesson is not None and lesson.status == "approved" else None

    def retract(self, question: str) -> None:
        self.lessons.pop(question, None)
