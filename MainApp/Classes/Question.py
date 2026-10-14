from dataclasses import dataclass, field
from typing import Literal
from MainApp.Classes.Option import Option

QuestionType = Literal["single", "multiple", "text"]

#@dataclass
class Question:
    id: int
    type: QuestionType
    text: str
    points: int = 1
    options: list[Option] = field(default_factory=list)
    correct: list[str] = field(default_factory=list)

    def __init__(self, id, type, text, points, options, correct):
        self.id = id
        self.type = type
        self.text = text
        self.points = points
        self.options = options
        self.correct = correct
