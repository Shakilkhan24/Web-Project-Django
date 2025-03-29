from django import template

register = template.Library()

@register.filter
def filter_by_status(tasks, status):
    """Filter tasks by their status."""
    return [task for task in tasks if task.status == status]
