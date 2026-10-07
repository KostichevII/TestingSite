def theme(request):
    theme = request.COOKIES.get("theme", "light")
    if theme not in ("light", "dark", "auto"):
        theme = "light"
    return {"theme": theme}