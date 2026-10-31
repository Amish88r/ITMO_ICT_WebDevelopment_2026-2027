from django import template

register = template.Library()


@register.filter
def grade_color(sub):
    """Цвет ячейки в журнале по проценту от максимума."""
    if sub is None:
        return 'secondary'
    if sub.grade is None:
        return 'info'
    pct = sub.grade / sub.homework.max_score
    return 'success' if pct >= 0.85 else 'primary' if pct >= 0.7 else 'warning' if pct >= 0.5 else 'danger'
