import base64
from dataclasses import dataclass

from django import forms

from MainApp.Classes import Question, Test


class UploadForm(forms.Form):
    file = forms.FileField(
        label="Файл теста (.json)",
        widget=forms.ClearableFileInput(
            attrs={"accept": ".json,application/json"}
        ),
    )


@dataclass
class GradeDetail:
    question: Question
    given: list[str]
    is_correct: bool
    earned: int
    max: int


@dataclass
class GradeResult:
    score: int
    max_score: int
    percent: float
    passed: bool
    details: list[GradeDetail]


class SolveForm(forms.Form):
    """Динамическая форма прохождения теста.

    Поля строятся в __init__ по объекту Test. Исходный зашифрованный
    JSON передаётся через скрытое поле blob (base64) — так мы не
    зависим от сессий и БД.
    """

    def __init__(self, test: Test, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test = test
        self._build_fields()

    # ---------- построение полей ----------

    def _build_fields(self) -> None:
        for q in self.test.questions:
            name = f"q_{q.id}"
            if q.type == "single":
                self.fields[name] = forms.ChoiceField(
                    choices=[(o.id, o.text) for o in q.options],
                    widget=forms.RadioSelect,
                    required=True,
                    label=q.text,
                )
            elif q.type == "multiple":
                self.fields[name] = forms.MultipleChoiceField(
                    choices=[(o.id, o.text) for o in q.options],
                    widget=forms.CheckboxSelectMultiple,
                    required=True,
                    label=q.text,
                )
            else:  # text
                self.fields[name] = forms.CharField(
                    required=True,
                    label=q.text,
                    widget=forms.TextInput(attrs={"placeholder": "Ваш ответ"}),
                )

    # ---------- проверка ----------

    def grade(self) -> GradeResult:
        if not self.is_valid():
            raise ValueError("Форма содержит ошибки — сначала исправьте их")

        score = 0
        details: list[GradeDetail] = []

        for q in self.test.questions:
            raw = self.cleaned_data.get(f"q_{q.id}")

            if q.type == "text":
                given = [raw.strip().lower()] if raw else []
                allowed = {c.strip().lower() for c in q.correct}
                is_correct = bool(given) and given[0] in allowed
            else:
                given = list(raw) if isinstance(raw, (list, tuple)) else ([raw] if raw else [])
                is_correct = set(given) == set(q.correct)

            earned = q.points if is_correct else 0
            score += earned
            details.append(GradeDetail(
                question=q, given=given, is_correct=is_correct,
                earned=earned, max=q.points,
            ))

        max_score = self.test.total_points()
        percent = (score / max_score * 100) if max_score else 0.0
        return GradeResult(
            score=score, max_score=max_score,
            percent=round(percent, 2),
            passed=percent >= self.test.pass_score,
            details=details,
        )
