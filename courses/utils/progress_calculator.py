from django.utils import timezone
from datetime import timedelta
from ..models import Progress, TestResult


def calculate_user_stats(user):
    """Расчет статистики пользователя"""
    # Прогресс по урокам
    total_lessons_completed = Progress.objects.filter(
        user=user, completed=True
    ).count()
    
    # Результаты тестов
    test_results = TestResult.objects.filter(user=user)
    total_tests = test_results.count()
    avg_test_score = test_results.aggregate(
        avg=Avg('percentage')
    )['avg'] or 0
    
    # Общее время обучения
    total_study_time = Progress.objects.filter(
        user=user, completed=True
    ).aggregate(
        total=Sum('time_spent_minutes')
    )['total'] or 0
    
    # Слова
    from ..models import UserWord
    total_words_learned = UserWord.objects.filter(
        user=user, learned=True
    ).count()
    total_words_favorite = UserWord.objects.filter(
        user=user, is_favorite=True
    ).count()
    
    return {
        'total_lessons_completed': total_lessons_completed,
        'total_tests': total_tests,
        'avg_test_score': round(avg_test_score, 1),
        'total_study_hours': round(total_study_time / 60, 1),
        'total_words_learned': total_words_learned,
        'total_words_favorite': total_words_favorite,
    }


def get_streak_info(user):
    """Информация о серии дней обучения"""
    profile = getattr(user, 'userprofile', None)
    if not profile:
        return {'current_streak': 0, 'longest_streak': 0}
    
    return {
        'current_streak': profile.streak_days,
        'longest_streak': profile.streak_days,  # Можно добавить поле в модель
    }


def get_recent_activity(user, limit=5):
    """Получение последней активности"""
    progress = Progress.objects.filter(
        user=user,
        completed=True
    ).select_related('lesson', 'lesson__language').order_by('-completed_at')[:limit]
    
    test_results = TestResult.objects.filter(
        user=user
    ).select_related('test').order_by('-created_at')[:limit]
    
    activities = []
    
    for p in progress:
        activities.append({
            'type': 'lesson',
            'title': p.lesson.title,
            'language': p.lesson.language.name,
            'date': p.completed_at,
            'score': p.score,
        })
    
    for tr in test_results:
        activities.append({
            'type': 'test',
            'title': tr.test.title,
            'date': tr.created_at,
            'score': tr.percentage,
            'passed': tr.passed,
        })
    
    # Сортируем по дате
    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:limit]