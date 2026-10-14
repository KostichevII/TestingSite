from __future__ import annotations
from dataclasses import dataclass, field
from .Question import Question
@dataclass
class Test:
    title: str
    questions: list[Question]
    description: str = ""
    time_limit_sec: int = 0
    pass_score: int = 70
    version: str = "1.0"

    def total_points(self) -> int:
        return sum(q.points for q in self.questions)

    def find_question(self, qid: int) -> Question | None:
        for q in self.questions:
            if q.id == qid:
                return q
        return None