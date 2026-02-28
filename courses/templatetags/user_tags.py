# courses/templatetags/user_tags.py
from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def calculate_level(user):
    """Рассчитывает уровень пользователя на основе XP"""
    try:
        if hasattr(user, 'userprofile'):
            xp = user.userprofile.xp
            # Уровень = XP // 100 + 1
            level = xp // 100 + 1
            return level
        return 1
    except:
        return 1

@register.filter
def get_user_avatar(user):
    """Возвращает первую букву имени пользователя для аватара"""
    if user.username:
        return user.username[0].upper()
    return 'U'

@register.filter
def get_user_xp(user):
    """Возвращает XP пользователя"""
    try:
        if hasattr(user, 'userprofile'):
            return user.userprofile.xp
        return 0
    except:
        return 0

@register.filter
def get_xp_for_next_level(user):
    """Возвращает сколько XP нужно для следующего уровня"""
    try:
        if hasattr(user, 'userprofile'):
            xp = user.userprofile.xp
            current_level = xp // 100 + 1
            xp_needed = current_level * 100
            return xp_needed
        return 100
    except:
        return 100

@register.filter
def get_level_progress(user):
    """Возвращает процент прогресса до следующего уровня"""
    try:
        if hasattr(user, 'userprofile'):
            xp = user.userprofile.xp
            xp_in_current_level = xp % 100
            return (xp_in_current_level / 100) * 100
        return 0
    except:
        return 0