from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получение значения из словаря по ключу"""
    return dictionary.get(key)

@register.filter
def truncate_chars(value, max_length):
    """Обрезка текста до указанной длины"""
    if len(value) <= max_length:
        return value
    return value[:max_length] + '...'

@register.simple_tag
def define(val=None):
    return val