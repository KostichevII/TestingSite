import uuid
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone

from django.shortcuts import redirect, render
from MainApp.Processors.JSONloader import TestLoadError, load_test
from .forms import SolveForm, UploadForm

@require_POST
def set_theme(request):
    theme = request.POST.get("theme", "light")
    if theme not in ("light", "dark", "auto"):
        theme = "light"

    # Куда вернуть пользователя: скрытое поле next или Referer
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("main")

    response = HttpResponseRedirect(next_url)
    response.set_cookie(
        "theme",
        theme,
        max_age=60 * 60 * 24 * 365,  # 1 год
        samesite="Lax",
        secure=request.is_secure(),  # True на HTTPS, False локально
        httponly=True,               # JS не читает cookie — доступна только серверу
    )
    return response

CACHE_PREFIX = "quiz:"
CACHE_TTL = 60 * 60  # 1 час


def _cache_key(token: str) -> str:
    return f"{CACHE_PREFIX}{token}"


def _clear_quiz(request, token: str) -> None:
    """Убираем тест из кеша и токен из сессии."""
    cache.delete(_cache_key(token))
    request.session.pop("quiz_token", None)
    request.session.pop("quiz_started_at", None)


def quiz_upload(request):
    """Шаг 1: загрузка файла → редирект на /solve/<token>/."""
    form = UploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        raw = form.cleaned_data["file"].read().decode("utf-8")
        try:
            test = load_test(raw)
        except TestLoadError as e:
            return render(request, "TestLoad.html", {
                "form": form, "error": str(e),
            })

        token = uuid.uuid4().hex
        cache.set(_cache_key(token), {"test": test}, CACHE_TTL)
        request.session["quiz_token"] = token
        request.session["quiz_started_at"] = timezone.now().isoformat()

        return redirect("quiz_solve", token=token)

    return render(request, "TestLoad.html", {"form": form})


def quiz_solve(request, token: str):
    """Шаг 2-3: прохождение теста и проверка ответов."""
    # 1. Токен должен совпадать с сессией — иначе чужой URL бесполезен
    if request.session.get("quiz_token") != token:
        return redirect("quiz_upload")

    # 2. Берём тест из кеша
    payload = cache.get(_cache_key(token))
    if payload is None:
        # Кеш истёк или его вычистили
        request.session.pop("quiz_token", None)
        return render(request, "TestError.html", {
            "error": "Время прохождения истекло. Загрузите тест заново.",
        })

    test = payload["test"]

    if request.method == "POST":
        form = SolveForm(test, request.POST)
        if form.is_valid():
            result = form.grade()
            # Результат отдаём один раз, после — чистим
            started_at = request.session.get("quiz_started_at")
            _clear_quiz(request, token)

            return render(request, "TestSolvingRes.html", {
                "test": test,
                "result": result,
                "started_at": started_at,
            })

        # Ошибки валидации — показываем форму снова
        return render(request, "TestSolving.html", {
            "test": test, "form": form, "token": token,
        })

    # GET — рендерим пустую форму
    form = SolveForm(test)
    return render(request, "TestSolving.html", {
        "test": test, "form": form, "token": token,
    })


EDIT_CACHE_PREFIX = "edit:"
EDIT_CACHE_TTL = 60 * 60   # 1 час


def _edit_cache_key(token: str) -> str:
    return f"{EDIT_CACHE_PREFIX}{token}"


def _clear_edit(request, token: str | None = None) -> None:
    """Чистим токен из сессии и (если известен) из кеша."""
    token = token or request.session.get("edit_token")
    if token:
        cache.delete(_edit_cache_key(token))
    request.session.pop("edit_token", None)

def quiz_edit_upload(request):
    """Принимает файл, кладёт расшифрованный Test в кеш и редиректит."""
    error = None

    if request.method == "POST":
        uploaded = request.FILES.get("file")
        if not uploaded:
            error = "Выберите файл теста."
        else:
            try:
                raw = uploaded.read().decode("utf-8")
                test = load_test(raw)
            except TestLoadError as e:
                error = str(e)
            except UnicodeDecodeError:
                error = "Файл должен быть в кодировке UTF-8."
            else:
                # чистим предыдущий незавершённый сеанс редактирования
                _clear_edit(request)

                token = uuid.uuid4().hex
                cache.set(_edit_cache_key(token), {"test": test}, EDIT_CACHE_TTL)
                request.session["edit_token"] = token
                request.session["edit_started_at"] = timezone.now().isoformat()

                return redirect("quiz_edit", token=token)

    return render(request, "TestEditUpload.html", {"error": error})


def quiz_edit(request, token: str):
    """Рендерит форму создания с initial_data из кеша."""
    # 1. Защита: токен в URL должен совпадать с сессией
    if request.session.get("edit_token") != token:
        return redirect("quiz_edit_upload")

    # 2. Достаём Test из кеша
    payload = cache.get(_edit_cache_key(token))
    if payload is None:
        request.session.pop("edit_token", None)
        return render(request, "TestEditError.html", {
            "error": "Сеанс редактирования истёк. Загрузите файл заново.",
        })

    test = payload["test"]

    # 3. Продлеваем TTL — пока пользователь работает, кеш живёт
    cache.touch(_edit_cache_key(token), EDIT_CACHE_TTL)

    # 4. Приводим доменную модель к тому, что понимает JS
    initial_data = {
        "title": test.title,
        "description": test.description,
        "time_limit_sec": test.time_limit_sec,
        "pass_score": test.pass_score,
        "questions": [
            {
                "id": q.id,
                "type": q.type,
                "text": q.text,
                "points": q.points,
                "options": [{"id": o.id, "text": o.text} for o in q.options],
                "correct": q.correct,
            }
            for q in test.questions
        ],
    }

    return render(request, "TestGeneration.html", {
        "initial_data": initial_data,
        "edit_token": token,
    })

@require_POST
def quiz_edit_exit(request):
    _clear_edit(request)
    return redirect("quiz_edit_upload")