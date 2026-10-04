from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST


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