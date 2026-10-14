import base64
import json

from .Crypto import decrypt_value, derive_key
from MainApp.Classes.Option import Option
from MainApp.Classes.Question import Question
from MainApp.Classes.Test import Test


class TestLoadError(ValueError):
    """Любая проблема при чтении или расшифровке файла теста."""


def load_test(raw: str | bytes) -> Test:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise TestLoadError(f"Некорректный JSON: {e}")

    try:
        salt = base64.b64decode(data["crypto"]["salt"])
    except (KeyError, ValueError) as e:
        raise TestLoadError(f"Отсутствует или повреждён блок crypto: {e}")

    key = derive_key(salt)
    questions: list[Question] = []

    for i, q in enumerate(data.get("questions", [])):
        qid = q.get("id", i + 1)
        qtype = q.get("type")
        if qtype not in ("single", "multiple", "text"):
            raise TestLoadError(f"Вопрос {qid}: неизвестный тип {qtype!r}")

        # Правильный ответ: сначала пробуем расшифровать, потом fallback на plain
        correct: list[str] = []
        if "correct_enc" in q:
            try:
                correct = decrypt_value(q["correct_enc"], key)
            except Exception as e:
                raise TestLoadError(
                    f"Вопрос {qid}: не удалось расшифровать ответ ({e})"
                )
        elif "correct" in q:
            correct = list(q["correct"])

        options = [
            Option(id=o["id"], text=o["text"])
            for o in q.get("options", [])
        ]

        questions.append(Question(
            id=qid,
            type=qtype,
            text=q["text"],
            points=q.get("points", 1),
            options=options,
            correct=correct,
        ))

    if not questions:
        raise TestLoadError("В файле нет вопросов")

    return Test(
        title=data.get("title", "Без названия"),
        description=data.get("description", ""),
        time_limit_sec=data.get("time_limit_sec", 0),
        pass_score=data.get("pass_score", 70),
        version=data.get("version", "1.0"),
        questions=questions,
    )