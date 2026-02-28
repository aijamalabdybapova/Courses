from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import LoginView  
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect

from .models import (
    Language, Course, Lesson, Word, Progress, Test,
    Question, Answer, TestResult, UserProfile, UserWord
)
from .forms import (
    RegisterForm, 
    UserUpdateForm,      
    ProfileUpdateForm,   
    WordForm, 
    SearchForm,
    CustomAuthenticationForm, 
    CustomPasswordResetForm,
)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход'
        return context
    
def home(request):
    """Главная страница для всех пользователей"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей показываем главную страницу с возможностью перехода в dashboard
        # Собираем базовую статистику
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Статистика для главной страницы
        total_lessons_completed = Progress.objects.filter(
            user=request.user, completed=True
        ).count()
        
        test_results = TestResult.objects.filter(user=request.user)
        total_tests = test_results.count()
        
        # Рассчитываем средний процент по тестам
        if test_results.exists():
            avg_percentage = test_results.aggregate(
                avg_percent=Avg('percentage')
            )['avg_percent'] or 0
            avg_test_score = round(avg_percentage, 1)
        else:
            avg_test_score = 0
        
        # Получаем последние активности
        recent_activities = Progress.objects.filter(
            user=request.user,
            completed=True
        ).select_related('lesson', 'lesson__course__language').order_by('-completed_at')[:3]
        
        # Получаем языки с прогрессом
        languages_with_progress = []
        languages = Language.objects.all()[:3]  # Берем первые 3 языка
        
        for language in languages:
            total_lessons = 0
            completed_lessons = 0
            
            for course in language.courses.all():
                total_lessons += course.lessons.count()
                completed_in_course = Progress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    completed=True
                ).count()
                completed_lessons += completed_in_course
            
            if total_lessons > 0:
                progress_percentage = int((completed_lessons / total_lessons) * 100)
            else:
                progress_percentage = 0
            
            languages_with_progress.append({
                'language': language,
                'progress_percentage': progress_percentage,
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons
            })
        
        # ВАЖНО: рендерим правильный шаблон!
        return render(request, 'courses/home_authenticated.html', {
            'profile': profile,
            'stats': {
                'total_lessons_completed': total_lessons_completed,
                'total_tests': total_tests,
                'avg_test_score': avg_test_score,
                'streak_days': profile.streak_days,
                'xp': profile.xp,
                'level': profile.xp // 100 + 1,
            },
            'recent_activities': recent_activities,
            'languages_with_progress': languages_with_progress,
            'total_languages': Language.objects.count(),
            'total_courses': Course.objects.count(),
        })
    
    # Для гостей показываем стандартную главную
    total_users = User.objects.count()
    total_languages = Language.objects.count()
    
    # Считаем общее количество уроков
    total_lessons = 0
    total_words = 0
    for language in Language.objects.all():
        for course in language.courses.all():
            total_lessons += course.lessons.count()
            total_words += course.total_words
    
    return render(request, 'courses/home.html', {
        'total_users': total_users,
        'total_languages': total_languages,
        'total_lessons': total_lessons,
        'total_words': total_words,
    })

def language_list(request):
    """Список языков с прогрессом пользователя"""
    languages = Language.objects.all()
    
    # Для каждого языка считаем прогресс пользователя
    for language in languages:
        # Общее количество уроков в языке
        total_lessons = 0
        completed_lessons = 0
        
        if request.user.is_authenticated:
            # Для каждого курса в языке считаем пройденные уроки
            for course in language.courses.all():
                total_lessons += course.lessons.count()
                # Считаем пройденные уроки в этом курсе
                completed_in_course = Progress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    completed=True
                ).count()
                completed_lessons += completed_in_course
        else:
            # Для неавторизованных просто считаем общее количество уроков
            for course in language.courses.all():
                total_lessons += course.lessons.count()
        
        # Расчет процента прогресса
        if total_lessons > 0:
            progress_percentage = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percentage = 0
        
        # Добавляем поля к объекту языка
        language.total_lessons_count = total_lessons
        language.completed_lessons_count = completed_lessons
        language.progress_percentage = progress_percentage
        
        # Считаем общее количество слов в языке
        language.total_words_count = language.total_words
    
    return render(request, 'courses/language_list.html', {
        'languages': languages
    })


def language_detail(request, language_id):
    """Детальная страница языка с курсами"""
    language = get_object_or_404(Language, id=language_id)
    courses = language.courses.filter(is_active=True).order_by('order')
    
    # Статистика по курсам
    for course in courses:
        course.completed_lessons = 0
        course.total_lessons = course.lessons.count()
        course.words_count = course.total_words
        
        if request.user.is_authenticated:
            course.user_progress = Progress.objects.filter(
                user=request.user,
                lesson__course=course,
                completed=True
            ).count()
            course.progress_percentage = int((course.user_progress / course.total_lessons * 100)) if course.total_lessons > 0 else 0
        else:
            course.user_progress = 0
            course.progress_percentage = 0
    
    return render(request, 'courses/language_detail.html', {
        'language': language,
        'courses': courses,
    })

def course_detail(request, course_id):
    """Детальная страница курса"""
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all().order_by('order')
    
    # Получаем прогресс пользователя
    completed_lesson_ids = []
    if request.user.is_authenticated:
        completed_lesson_ids = Progress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            completed=True
        ).values_list('lesson_id', flat=True)
    
    # Подготавливаем данные для уроков
    lesson_data = []
    for lesson in lessons:
        lesson_data.append({
            'lesson': lesson,
            'completed': lesson.id in completed_lesson_ids,
            'words_count': lesson.words.count(),
        })
    
    # Проверяем, доступен ли курс
    course_available = True
    if request.user.is_authenticated and course.order > 1:
        # Проверяем, завершен ли предыдущий курс
        prev_course = Course.objects.filter(
            language=course.language,
            order=course.order - 1
        ).first()
        if prev_course:
            completed_in_prev = Progress.objects.filter(
                user=request.user,
                lesson__course=prev_course,
                completed=True
            ).count()
            total_in_prev = prev_course.lessons.count()
            course_available = completed_in_prev == total_in_prev
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lesson_data,
        'course_available': course_available,
        'total_words': course.total_words,
    })

def test_email(request):
    """Тестовая отправка email"""
    try:
        send_mail(
            'Тестовое письмо от LangLearn',
            'Это тестовое письмо для проверки настроек email.',
            settings.DEFAULT_FROM_EMAIL,
            ['your-test-email@gmail.com'],  # Замените на ваш email
            fail_silently=False,
            html_message='<h1>Тестовое письмо</h1><p>Если вы видите это, email работает!</p>'
        )
        return HttpResponse('Email отправлен успешно!')
    except Exception as e:
        return HttpResponse(f'Ошибка отправки email: {str(e)}')
    
def password_reset_done_custom(request):
    messages.success(request, 'Письмо для восстановления пароля отправлено на ваш email!')
    return render(request, 'registration/password_reset_done.html')
    


@login_required
def lesson_detail(request, lesson_id):
    """Детальная страница урока"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    words = lesson.words.all()
    course = lesson.course
    
    # Проверяем прогресс
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    # Проверяем, доступен ли урок
    lesson_available = True
    if lesson.order > 1:
        prev_lesson = lesson.prev_lesson
        if prev_lesson:
            prev_progress = Progress.objects.filter(
                user=request.user,
                lesson=prev_lesson,
                completed=True
            ).exists()
            lesson_available = prev_progress
    
    # Проверяем, есть ли тест для этого урока
    test = Test.objects.filter(lesson=lesson).first()
    
    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson,
        'course': course,
        'words': words,
        'progress': progress,
        'lesson_available': lesson_available,
        'test': test,
    })


@login_required
def complete_lesson(request, lesson_id):
    """Отметить урок как пройденный"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
        
        # Обновляем профиль
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += 10
        profile.total_study_time_minutes += 15
        profile.save()
        
        messages.success(request, f'Урок "{lesson.title}" пройден!')
    
    return redirect('lesson_detail', lesson_id=lesson.id)


@login_required
def test_detail(request, test_id):
    """Страница теста с обработкой ответов"""
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all().prefetch_related('answers')
    
    # Вычисляем данные для шаблона
    questions_count = questions.count()
    max_xp = questions_count * 5  # 5 XP за каждый вопрос
    
    if request.method == 'POST':
        score = 0
        total = questions_count
        
        # Проверяем каждый вопрос
        for question in questions:
                selected_answer_id = request.POST.get(f'question_{question.id}')
                if selected_answer_id:
                    try:
                        selected_answer = Answer.objects.get(id=selected_answer_id, question=question)
                        if selected_answer.is_correct:
                            score += 1
                    except Answer.DoesNotExist:
                        pass
        
        # Рассчитываем процент
        percentage = (score / total * 100) if total > 0 else 0
        
        # Создаем результат теста
        result = TestResult.objects.create(
            user=request.user,
            test=test,
            score=score,
            total=total,
            percentage=percentage,
            passed=percentage >= 70
        )
        
        # Добавляем опыт
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += score * 5  # 5 XP за каждый правильный ответ
        profile.save()
        
        # Редирект на страницу результата с result_id
        return redirect('test_result_detail', test_id=test_id, result_id=result.id)
    
    # GET запрос - показываем тест
    return render(request, 'courses/test_detail.html', {
        'test': test,
        'questions': questions,
        'questions_count': questions_count,
        'max_xp': max_xp,
    })

@login_required
def test_result(request, test_id, result_id=None):
    """Страница результата теста"""
    test = get_object_or_404(Test, id=test_id)
    
    # Если передан result_id, показываем конкретный результат
    if result_id:
        result = get_object_or_404(TestResult, id=result_id, user=request.user, test=test)
    else:
        # Иначе показываем последний результат пользователя для этого теста
        result = TestResult.objects.filter(
            user=request.user,
            test=test
        ).order_by('-created_at').first()
        
        if not result:
            messages.error(request, 'Вы еще не проходили этот тест')
            return redirect('test_detail', test_id=test_id)
    
    # Вычисляем дополнительные данные
    earned_xp = result.score * 5
    wrong_answers = result.total - result.score
    
    return render(request, 'courses/test_result.html', {
        'test': test,
        'result': result,
        'earned_xp': earned_xp,
        'wrong_answers': wrong_answers,
        'percentage': result.percentage,
    })

@login_required
def profile(request):
    """Профиль пользователя с возможностью редактирования"""
    profile_obj, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)
    
    # Получаем статистику
    progress = Progress.objects.filter(user=request.user, completed=True).select_related('lesson')
    results = TestResult.objects.filter(user=request.user).select_related('test')
    
    # Статистика тестов
    test_results = TestResult.objects.filter(user=request.user)
    total_tests = test_results.count()
    
    if test_results.exists():
        avg_percentage = test_results.aggregate(
            avg_percent=Avg('percentage')
        )['avg_percent'] or 0
        avg_test_score = round(avg_percentage, 1)
    else:
        avg_test_score = 0
    
    # Прогресс по языкам для профиля
    languages_progress = []
    languages = Language.objects.all()
    
    for language in languages:
        total_lessons = 0
        for course in language.courses.all():
            total_lessons += course.lessons.count()
        
        completed = Progress.objects.filter(
            user=request.user,
            lesson__course__language=language,
            completed=True
        ).count()
        
        if total_lessons > 0:
            languages_progress.append({
                'language': language,
                'completed': completed,
                'total': total_lessons,
                'percentage': int((completed / total_lessons) * 100)
            })
    
    # Расчет уровня на основе XP
    level = profile_obj.xp // 100 + 1
    xp_for_next_level = level * 100
    xp_progress = profile_obj.xp % 100
    
    # Ежедневная цель для профиля
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_study = Progress.objects.filter(
        user=request.user,
        completed_at__gte=today_start
    ).count() * 15
    
    return render(request, 'courses/profile.html', {
        'profile': profile_obj,
        'user_form': user_form,
        'profile_form': profile_form,
        'progress': progress,
        'results': results,
        'level': level,
        'xp_for_next_level': xp_for_next_level,
        'xp_progress': xp_progress,
        'languages_progress': languages_progress,
        'today_study': today_study,
        'stats': {
            'total_lessons_completed': Progress.objects.filter(
                user=request.user, completed=True
            ).count(),
            'total_tests': total_tests,
            'avg_test_score': avg_test_score,
            'streak_days': profile_obj.streak_days,
            'total_words_learned': UserWord.objects.filter(
                user=request.user, learned=True
            ).count(),
            'total_words_favorite': UserWord.objects.filter(
                user=request.user, is_favorite=True
            ).count(),
        },
    })


@login_required
def change_password(request):
    """Изменение пароля"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'courses/change_password.html', {'form': form})


@login_required
def dictionary(request):
    """Словарь пользователя с фильтрацией по языкам"""
    form = SearchForm(request.GET or None)
    
    # Базовый запрос
    words = UserWord.objects.filter(user=request.user).select_related(
        'word', 
        'word__lesson', 
        'word__lesson__course', 
        'word__lesson__course__language'
    )
    
    # Получаем все языки для фильтра
    languages = Language.objects.all()
    
    # Текущий выбранный язык (из GET параметра или из сессии)
    current_language_id = request.GET.get('language')
    if not current_language_id and 'current_dict_language' in request.session:
        current_language_id = request.session.get('current_dict_language')
    
    # Применяем фильтр по языку
    if current_language_id:
        words = words.filter(word__lesson__course__language_id=current_language_id)
        request.session['current_dict_language'] = current_language_id
    else:
        # Если язык не выбран, показываем все слова
        pass
    
    # Поиск по тексту
    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            words = words.filter(
                Q(word__word__icontains=query) |
                Q(word__translation__icontains=query)
            )
    
    # Сортировка
    words = words.order_by('-last_viewed')
    
    # Пагинация
    paginator = Paginator(words, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика по языкам для боковой панели
    language_stats = []
    for language in languages:
        count = UserWord.objects.filter(
            user=request.user,
            word__lesson__course__language=language
        ).count()
        
        learned_count = UserWord.objects.filter(
            user=request.user,
            word__lesson__course__language=language,
            learned=True
        ).count()
        
        favorite_count = UserWord.objects.filter(
            user=request.user,
            word__lesson__course__language=language,
            is_favorite=True
        ).count()
        
        language_stats.append({
            'language': language,
            'total': count,
            'learned': learned_count,
            'favorite': favorite_count,
            'selected': str(language.id) == str(current_language_id)
        })
    
    # Общая статистика
    total_words = words.count()
    total_learned = words.filter(learned=True).count()
    total_favorite = words.filter(is_favorite=True).count()
    
    return render(request, 'courses/dictionary.html', {
        'page_obj': page_obj,
        'form': form,
        'total_words': total_words,
        'total_learned': total_learned,
        'total_favorite': total_favorite,
        'language_stats': language_stats,
        'current_language_id': int(current_language_id) if current_language_id else None,
    })


@login_required
def toggle_favorite_word(request, word_id):
    """Добавить/удалить слово в избранное"""
    word = get_object_or_404(Word, id=word_id)
    user_word, created = UserWord.objects.get_or_create(
        user=request.user,
        word=word
    )
    
    user_word.is_favorite = not user_word.is_favorite
    user_word.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': user_word.is_favorite
        })
    
    messages.success(request, f'Слово "{word.word}" {"добавлено в" if user_word.is_favorite else "удалено из"} избранное')
    return redirect('dictionary')


@login_required
def mark_word_learned(request, word_id):
    """Отметить слово как изученное"""
    word = get_object_or_404(Word, id=word_id)
    user_word, created = UserWord.objects.get_or_create(
        user=request.user,
        word=word
    )
    
    user_word.learned = not user_word.learned
    if user_word.learned:
        user_word.learned_at = timezone.now()
    else:
        user_word.learned_at = None
    user_word.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'learned': user_word.learned
        })
    
    messages.success(request, f'Слово "{word.word}" {"отмечено как изученное" if user_word.learned else "удалено из изученных"}')
    return redirect('dictionary')


@login_required
def dashboard(request):
    """Панель управления с прогрессом"""
    # Получаем профиль пользователя
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Статистика уроков
    total_lessons_completed = Progress.objects.filter(
        user=request.user, completed=True
    ).count()
    
    # Статистика слов
    total_words_learned = UserWord.objects.filter(
        user=request.user, learned=True
    ).count()
    
    total_words_favorite = UserWord.objects.filter(
        user=request.user, is_favorite=True
    ).count()
    
    # Статистика тестов
    test_results = TestResult.objects.filter(user=request.user)
    total_tests = test_results.count()
    
    # ПРАВИЛЬНЫЙ расчет среднего процента по тестам
    if test_results.exists():
        avg_percentage = test_results.aggregate(
            avg_percent=Avg('percentage')
        )['avg_percent'] or 0
        avg_test_score = round(avg_percentage, 1)
    else:
        avg_test_score = 0
    
    # Прогресс по языкам
    languages_progress = []
    languages = Language.objects.all()
    
    for language in languages:
        # Считаем общее количество уроков во всех курсах языка
        total_lessons = 0
        for course in language.courses.all():
            total_lessons += course.lessons.count()
        
        # Считаем пройденные уроки во всех курсах языка
        completed = Progress.objects.filter(
            user=request.user,
            lesson__course__language=language,
            completed=True
        ).count()
        
        if total_lessons > 0:
            percentage = int((completed / total_lessons) * 100)
            languages_progress.append({
                'language': language,
                'completed': completed,
                'total': total_lessons,
                'percentage': percentage
            })
    
    # Ежедневная цель - ИСПРАВЛЕННЫЙ РАСЧЕТ
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_study = Progress.objects.filter(
        user=request.user,
        completed_at__gte=today_start
    ).count() * 15  # Примерно 15 минут на урок
    
    # Важно: правильно рассчитываем процент с проверкой деления на ноль
    daily_goal = profile.daily_goal_minutes
    
    if daily_goal > 0:
        # Рассчитываем процент и ограничиваем максимум 100
        goal_percentage_raw = (today_study / daily_goal) * 100
        goal_percentage = min(goal_percentage_raw, 100)
    else:
        goal_percentage = 0
    
    # Округляем до одного знака после запятой для точности
    goal_percentage = round(goal_percentage, 1)
    
    # Отладочная информация (можно убрать в продакшене)
    print(f"[DEBUG] Daily Goal Calculation:")
    print(f"  today_study: {today_study} minutes")
    print(f"  daily_goal: {daily_goal} minutes")
    print(f"  goal_percentage_raw: {goal_percentage_raw if daily_goal > 0 else 0}%")
    print(f"  goal_percentage: {goal_percentage}%")
    
    # Последняя активность
    recent_progress = Progress.objects.filter(
        user=request.user,
        completed=True
    ).select_related('lesson', 'lesson__course__language').order_by('-completed_at')[:5]
    
    recent_tests = TestResult.objects.filter(
        user=request.user
    ).select_related('test').order_by('-created_at')[:5]
    
    recent_activity = []
    
    for p in recent_progress:
        recent_activity.append({
            'type': 'lesson',
            'title': p.lesson.title,
            'date': p.completed_at,
            'icon': '📚'
        })
    
    for t in recent_tests:
        recent_activity.append({
            'type': 'test',
            'title': t.test.title,
            'date': t.created_at,
            'icon': '📝',
            'score': f"{t.score}/{t.total} ({t.percentage:.1f}%)"
        })
    
    # Сортируем по дате
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:5]
    
    return render(request, 'courses/dashboard.html', {
        'stats': {
            'total_lessons_completed': total_lessons_completed,
            'total_tests': total_tests,
            'avg_test_score': avg_test_score,
            'total_words_learned': total_words_learned,
            'total_words_favorite': total_words_favorite,
            'streak_days': profile.streak_days,
            'xp': profile.xp,
            'level': profile.xp // 100 + 1,
        },
        'languages_progress': languages_progress,
        'today_study': today_study,
        'goal_percentage': goal_percentage,  # Уже правильно рассчитано и ограничено
        'recent_activity': recent_activity,
        'profile': profile,
    })

def register(request):
    """Регистрация"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Создаем профиль
            UserProfile.objects.create(user=user)
            
            # Авторизуем пользователя
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def api_user_stats(request):
    """API для получения статистики пользователя"""
    try:
        total_lessons_completed = Progress.objects.filter(
            user=request.user, completed=True
        ).count()
        
        total_words_learned = UserWord.objects.filter(
            user=request.user, learned=True
        ).count()
        
        total_words_favorite = UserWord.objects.filter(
            user=request.user, is_favorite=True
        ).count()
        
        test_results = TestResult.objects.filter(user=request.user)
        
        # ПРАВИЛЬНЫЙ расчет среднего процента по тестам
        if test_results.exists():
            avg_percentage = test_results.aggregate(
                avg_percent=Avg('percentage')
            )['avg_percent'] or 0
            avg_test_score = round(avg_percentage, 1)
        else:
            avg_test_score = 0
        
        return JsonResponse({
            'success': True,
            'total_lessons_completed': total_lessons_completed,
            'total_words_learned': total_words_learned,
            'total_words_favorite': total_words_favorite,
            'avg_test_score': avg_test_score,  # Средний процент
            'test_results_count': test_results.count(),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def api_recent_progress(request):
    """API для получения последнего прогресса"""
    try:
        recent = Progress.objects.filter(
            user=request.user,
            completed=True
        ).select_related('lesson', 'lesson__course__language').order_by('-completed_at')[:5]
        
        data = []
        for p in recent:
            data.append({
                'lesson': p.lesson.title,
                'language': p.lesson.course.language.name if p.lesson.course.language else 'Неизвестно',
                'date': p.completed_at.strftime('%d.%m.%Y') if p.completed_at else '',
            })
        
        return JsonResponse({
            'success': True,
            'progress': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@login_required
def clear_dictionary_filter(request):
    """Очистка фильтра по языку в словаре"""
    if 'current_dict_language' in request.session:
        del request.session['current_dict_language']
    return redirect('dictionary')
    

@login_required
def clear_dictionary_filter(request):
    """Очистка фильтра по языку в словаре"""
    if 'current_dict_language' in request.session:
        del request.session['current_dict_language']
    return redirect('dictionary')
