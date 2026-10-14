from django import template

register = template.Library()


@register.filter
def question_field(form, question_id):
    """form['q_<id>'] — безопасный доступ к полю динамической формы."""
    return form[f"q_{question_id}"]