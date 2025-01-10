from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def is_in(value, arg):
    return value in arg


@register.filter
def format_datetime(value):
    """
    Custom filter to format a datetime object as DD/MM/YY - HH:mm.
    """
    if not value:
        return ""
    return value.strftime("%d.%m.%y - %H:%M")
