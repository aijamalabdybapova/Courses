from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models

from .models import (
    Language, Course, Lesson, Word, Test, Question, Answer,
    User, UserProfile, Progress, TestResult, UserWord,
    ModeratorStudent, ModeratorNote  # Добавьте ModeratorNote если нужно
)
from .forms import (
    LanguageForm, CourseForm, LessonForm, WordForm,
    TestForm, QuestionForm, AnswerForm
)

# Декоратор для проверки прав администратора
def admin_required(view_func):
    """Декоратор для проверки, что пользователь является администратором (не модератором)"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_authenticated and (hasattr(u, 'userprofile') and u.userprofile.is_admin) or u.is_superuser,
        login_url='home',
        redirect_field_name='next'
    )(view_func)
    return decorated_view_func

# ========== ДАШБОРД ==========
@admin_required
def admin_dashboard(request):
    """Главная панель администратора"""
    # Основные метрики
    total_users = User.objects.count()
    total_languages = Language.objects.count()
    total_courses = Course.objects.count()
    total_lessons = Lesson.objects.count()
    total_words = Word.objects.count()
    total_tests = Test.objects.count()
    
    # Активность за сегодня
    today = timezone.now().date()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    completed_lessons_today = Progress.objects.filter(
        completed=True,
        completed_at__date=today
    ).count()
    
    # Активность за неделю
    week_ago = timezone.now() - timedelta(days=7)
    active_users_week = Progress.objects.filter(
        completed_at__gte=week_ago
    ).values('user').distinct().count()
    
    # Последние действия
    recent_progress = Progress.objects.filter(
        completed=True
    ).select_related('user', 'lesson__course__language').order_by('-completed_at')[:10]
    
    recent_registrations = User.objects.order_by('-date_joined')[:5]
    
    # Статистика по тестам
    avg_test_score = TestResult.objects.aggregate(
        avg=Avg('percentage')
    )['avg'] or 0
    
    # Популярные курсы
    popular_courses = Course.objects.annotate(
        student_count=Count('lessons__progress', distinct=True),
        completed_count=Count('lessons__progress', filter=models.Q(lessons__progress__completed=True))
    ).order_by('-student_count')[:5]
    
    # График активности по дням (последние 7 дней)
    activity_chart_data = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        count = Progress.objects.filter(
            completed=True,
            completed_at__date=day
        ).count()
        activity_chart_data.append({
            'date': day.strftime('%d.%m'),
            'count': count
        })
    
    # Передаем данные для сайдбара
    context = {
        'total_users': total_users,
        'total_languages': total_languages,
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_words': total_words,
        'total_tests': total_tests,
        'new_users_today': new_users_today,
        'completed_lessons_today': completed_lessons_today,
        'active_users_week': active_users_week,
        'avg_test_score': round(avg_test_score, 1),
        'recent_progress': recent_progress,
        'recent_registrations': recent_registrations,
        'popular_courses': popular_courses,
        'activity_chart_data': activity_chart_data,
    }
    context['moderators'] = User.objects.filter(userprofile__role='moderator')
    context['students'] = User.objects.filter(userprofile__role='student')
    return render(request, 'courses/admin/dashboard.html', context)


# ========== УПРАВЛЕНИЕ ЯЗЫКАМИ ==========
@admin_required
def admin_languages(request):
    """Список языков"""
    languages = Language.objects.all().order_by('name')
    
    # Передаем данные для сайдбара
    context = {
        'languages': languages,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/languages/list.html', context)


@admin_required
def admin_language_create(request):
    """Создание языка"""
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Язык успешно создан!')
            return redirect('admin_languages')
    else:
        form = LanguageForm()
    
    context = {
        'form': form,
        'title': 'Создание языка',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/languages/form.html', context)


@admin_required
def admin_language_edit(request, pk):
    """Редактирование языка"""
    language = get_object_or_404(Language, pk=pk)
    
    if request.method == 'POST':
        form = LanguageForm(request.POST, instance=language)
        if form.is_valid():
            form.save()
            messages.success(request, 'Язык успешно обновлен!')
            return redirect('admin_languages')
    else:
        form = LanguageForm(instance=language)
    
    context = {
        'form': form,
        'title': f'Редактирование: {language.name}',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/languages/form.html', context)


@admin_required
def admin_language_delete(request, pk):
    """Удаление языка"""
    language = get_object_or_404(Language, pk=pk)
    
    # Проверяем, есть ли связанные курсы
    if language.courses.exists():
        messages.error(request, 'Нельзя удалить язык, к которому привязаны курсы!')
        return redirect('admin_languages')
    
    if request.method == 'POST':
        language.delete()
        messages.success(request, 'Язык успешно удален!')
        return redirect('admin_languages')
    
    context = {
        'language': language,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/languages/delete.html', context)


# ========== УПРАВЛЕНИЕ КУРСАМИ ==========
@admin_required
def admin_courses(request):
    """Список курсов"""
    courses = Course.objects.select_related('language').all().order_by('language', 'order')
    
    # Фильтрация по языку
    language_id = request.GET.get('language')
    if language_id:
        courses = courses.filter(language_id=language_id)
    
    context = {
        'courses': courses,
        'languages': Language.objects.all(),
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/courses/list.html', context)


@admin_required
def admin_course_create(request):
    """Создание курса"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Курс успешно создан!')
            return redirect('admin_courses')
    else:
        form = CourseForm()
    
    context = {
        'form': form,
        'title': 'Создание курса',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/courses/form.html', context)


@admin_required
def admin_course_edit(request, pk):
    """Редактирование курса"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Курс успешно обновлен!')
            return redirect('admin_courses')
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'title': f'Редактирование: {course.title}',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/courses/form.html', context)


@admin_required
def admin_course_delete(request, pk):
    """Удаление курса"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Курс успешно удален!')
        return redirect('admin_courses')
    
    context = {
        'course': course,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/courses/delete.html', context)


# ========== УПРАВЛЕНИЕ УРОКАМИ ==========
@admin_required
def admin_lessons(request):
    """Список уроков"""
    lessons = Lesson.objects.select_related('course__language').all().order_by('course', 'order')
    
    # Фильтрация по курсу
    course_id = request.GET.get('course')
    if course_id:
        lessons = lessons.filter(course_id=course_id)
    
    # Пагинация
    paginator = Paginator(lessons, 20)
    page = request.GET.get('page')
    lessons_page = paginator.get_page(page)
    
    context = {
        'lessons': lessons_page,
        'courses': Course.objects.select_related('language').all(),
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/lessons/list.html', context)


@admin_required
def admin_lesson_create(request):
    """Создание урока"""
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, 'Урок успешно создан!')
            return redirect('admin_lessons')
    else:
        form = LessonForm()
    
    context = {
        'form': form,
        'title': 'Создание урока',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/lessons/form.html', context)


@admin_required
def admin_lesson_edit(request, pk):
    """Редактирование урока"""
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Урок успешно обновлен!')
            return redirect('admin_lessons')
    else:
        form = LessonForm(instance=lesson)
    
    context = {
        'form': form,
        'title': f'Редактирование: {lesson.title}',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/lessons/form.html', context)


@admin_required
def admin_lesson_delete(request, pk):
    """Удаление урока"""
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Урок успешно удален!')
        return redirect('admin_lessons')
    
    context = {
        'lesson': lesson,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/lessons/delete.html', context)


# ========== УПРАВЛЕНИЕ СЛОВАМИ ==========
@admin_required
def admin_words(request):
    """Список слов"""
    words = Word.objects.select_related('lesson__course__language').all().order_by('word')
    
    # Фильтрация по уроку
    lesson_id = request.GET.get('lesson')
    if lesson_id:
        words = words.filter(lesson_id=lesson_id)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        words = words.filter(
            Q(word__icontains=search) | 
            Q(translation__icontains=search)
        )
    
    # Пагинация
    paginator = Paginator(words, 30)
    page = request.GET.get('page')
    words_page = paginator.get_page(page)
    
    context = {
        'words': words_page,
        'lessons': Lesson.objects.select_related('course__language').all(),
        'search': search,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/words/list.html', context)


@admin_required
def admin_word_create(request):
    """Создание слова"""
    if request.method == 'POST':
        form = WordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Слово успешно создано!')
            return redirect('admin_words')
    else:
        form = WordForm()
    
    context = {
        'form': form,
        'title': 'Создание слова',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/words/form.html', context)


@admin_required
def admin_word_edit(request, pk):
    """Редактирование слова"""
    word = get_object_or_404(Word, pk=pk)
    
    if request.method == 'POST':
        form = WordForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            messages.success(request, 'Слово успешно обновлено!')
            return redirect('admin_words')
    else:
        form = WordForm(instance=word)
    
    context = {
        'form': form,
        'title': f'Редактирование: {word.word}',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/words/form.html', context)


@admin_required
def admin_word_delete(request, pk):
    """Удаление слова"""
    word = get_object_or_404(Word, pk=pk)
    
    if request.method == 'POST':
        word.delete()
        messages.success(request, 'Слово успешно удалено!')
        return redirect('admin_words')
    
    context = {
        'word': word,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/words/delete.html', context)


# ========== УПРАВЛЕНИЕ ТЕСТАМИ ==========
@admin_required
def admin_tests(request):
    """Список тестов"""
    tests = Test.objects.select_related('lesson__course__language').all().order_by('lesson')
    
    context = {
        'tests': tests,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/list.html', context)


@admin_required
def admin_test_create(request):
    """Создание теста"""
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save()
            messages.success(request, 'Тест успешно создан! Добавьте вопросы.')
            return redirect('admin_questions', test_id=test.id)
    else:
        form = TestForm()
    
    context = {
        'form': form,
        'title': 'Создание теста',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/form.html', context)


@admin_required
def admin_test_edit(request, pk):
    """Редактирование теста"""
    test = get_object_or_404(Test, pk=pk)
    
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тест успешно обновлен!')
            return redirect('admin_tests')
    else:
        form = TestForm(instance=test)
    
    context = {
        'form': form,
        'title': f'Редактирование: {test.title}',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/form.html', context)


@admin_required
def admin_test_delete(request, pk):
    """Удаление теста"""
    test = get_object_or_404(Test, pk=pk)
    
    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Тест успешно удален!')
        return redirect('admin_tests')
    
    context = {
        'test': test,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/delete.html', context)


@admin_required
def admin_questions(request, test_id):
    """Управление вопросами теста"""
    test = get_object_or_404(Test, pk=test_id)
    questions = test.questions.all().prefetch_related('answers')
    
    context = {
        'test': test,
        'questions': questions,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/questions.html', context)


@admin_required
def admin_question_create(request, test_id):
    """Создание вопроса"""
    test = get_object_or_404(Test, pk=test_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            
            # Обработка ответов
            answers = request.POST.getlist('answers[]')
            is_correct = request.POST.getlist('is_correct[]')
            
            for i, answer_text in enumerate(answers):
                if answer_text.strip():
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=str(i) in is_correct
                    )
            
            messages.success(request, 'Вопрос успешно создан!')
            return redirect('admin_questions', test_id=test.id)
    else:
        form = QuestionForm()
    
    context = {
        'form': form,
        'test': test,
        'title': 'Создание вопроса',
        'action': 'Создать',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/question_form.html', context)


@admin_required
def admin_question_edit(request, pk):
    """Редактирование вопроса"""
    question = get_object_or_404(Question, pk=pk)
    test = question.test
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            
            # Обновление ответов
            # Сначала удаляем старые
            question.answers.all().delete()
            
            # Добавляем новые
            answers = request.POST.getlist('answers[]')
            is_correct = request.POST.getlist('is_correct[]')
            
            for i, answer_text in enumerate(answers):
                if answer_text.strip():
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=str(i) in is_correct
                    )
            
            messages.success(request, 'Вопрос успешно обновлен!')
            return redirect('admin_questions', test_id=test.id)
    else:
        form = QuestionForm(instance=question)
    
    # Получаем текущие ответы для отображения в форме
    current_answers = question.answers.all()
    
    context = {
        'form': form,
        'test': test,
        'question': question,
        'current_answers': current_answers,
        'title': f'Редактирование вопроса',
        'action': 'Сохранить',
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/question_form.html', context)


@admin_required
def admin_question_delete(request, pk):
    """Удаление вопроса"""
    question = get_object_or_404(Question, pk=pk)
    test_id = question.test.id
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Вопрос успешно удален!')
        return redirect('admin_questions', test_id=test_id)
    
    context = {
        'question': question,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/tests/question_delete.html', context)


# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========
@admin_required
def admin_users(request):
    """Список пользователей"""
    users = User.objects.select_related('userprofile').all().order_by('-date_joined')
    
    # Поиск
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Фильтрация по роли
    role = request.GET.get('role')
    if role == 'admin':
        users = users.filter(is_staff=True)
    elif role == 'user':
        users = users.filter(is_staff=False)
    
    # Пагинация
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'search': search,
        'role': role,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/users/list.html', context)


@admin_required
def admin_user_toggle_active(request, user_id):
    """Активация/деактивация пользователя"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'активирован' if user.is_active else 'деактивирован'
        messages.success(request, f'Пользователь {user.username} успешно {status}!')
    
    return redirect('admin_users')

def admin_user_bulk_action(request):
    """Массовые действия с пользователями"""
    if request.method != 'POST':
        return redirect('admin_users')
    
    action = request.POST.get('action')
    user_ids = request.POST.getlist('user_ids')
    
    if not user_ids:
        messages.error(request, 'Не выбраны пользователи')
        return redirect('admin_users')
    
    users = User.objects.filter(id__in=user_ids)
    count = users.count()
    
    if action == 'activate':
        users.update(is_active=True)
        messages.success(request, f'Активировано {count} пользователей')
        
    elif action == 'deactivate':
        users.update(is_active=False)
        messages.success(request, f'Деактивировано {count} пользователей')
        
    elif action == 'make_student':
        for user in users:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'student'
            profile.save()
            # Убираем права staff у студентов (кроме суперпользователей)
            if user.is_staff and not user.is_superuser:
                user.is_staff = False
                user.save()
        messages.success(request, f'{count} пользователей назначены студентами')
        
    elif action == 'make_moderator':
        for user in users:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'moderator'
            profile.save()
            # НЕ ДАЕМ права staff модераторам
            if user.is_staff and not user.is_superuser:
                user.is_staff = False
                user.save()
        messages.success(request, f'{count} пользователей назначены модераторами')
        
    elif action == 'make_admin':
        for user in users:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'admin'
            profile.save()
            # Только админы получают права staff
            if not user.is_staff:
                user.is_staff = True
            user.is_superuser = True
            user.save()
        messages.success(request, f'{count} пользователей назначены администраторами')
        
    elif action == 'reset_progress':
        for user in users:
            Progress.objects.filter(user=user).update(completed=False, completed_at=None)
            UserWord.objects.filter(user=user).update(learned=False, learned_at=None)
            try:
                profile = user.userprofile
                profile.xp = 0
                profile.level = 1
                profile.streak_days = 0
                profile.save()
            except UserProfile.DoesNotExist:
                pass
        messages.success(request, f'Прогресс сброшен для {count} пользователей')
        
    elif action == 'delete':
        # Не удаляем суперпользователей
        for user in users:
            if not user.is_superuser:
                user.delete()
        messages.success(request, f'Удалено {count} пользователей')
    
    return redirect('admin_users')


def admin_user_reset_progress(request, user_id):
    """Сброс прогресса отдельного пользователя"""
    user = get_object_or_404(User, id=user_id)
    
    Progress.objects.filter(user=user).update(completed=False, completed_at=None)
    UserWord.objects.filter(user=user).update(learned=False, learned_at=None)
    
    try:
        profile = user.userprofile
        profile.xp = 0
        profile.level = 1
        profile.streak_days = 0
        profile.save()
        messages.success(request, f'Прогресс пользователя {user.username} сброшен')
    except UserProfile.DoesNotExist:
        messages.warning(request, f'Профиль пользователя {user.username} не найден')
    
    return redirect('admin_users')


# ========== СТАТИСТИКА ==========
@admin_required
def admin_statistics(request):
    """Статистика платформы"""
    # Общая статистика
    total_users = User.objects.count()
    total_lessons_completed = Progress.objects.filter(completed=True).count()
    total_tests_passed = TestResult.objects.filter(passed=True).count()
    
    # Статистика по языкам
    language_stats = []
    for language in Language.objects.all():
        lessons_count = 0
        completed_count = 0
        for course in language.courses.all():
            lessons_count += course.lessons.count()
            completed_count += Progress.objects.filter(
                lesson__course=course,
                completed=True
            ).count()
        
        language_stats.append({
            'language': language,
            'lessons_count': lessons_count,
            'completed_count': completed_count,
            'completion_rate': (completed_count / lessons_count * 100) if lessons_count > 0 else 0
        })
    
    # Статистика по тестам
    test_stats = []
    for test in Test.objects.all()[:10]:
        results = TestResult.objects.filter(test=test)
        total_attempts = results.count()
        passed_count = results.filter(passed=True).count()
        
        test_stats.append({
            'test': test,
            'total_attempts': total_attempts,
            'passed_count': passed_count,
            'avg_score': results.aggregate(avg=Avg('percentage'))['avg'] or 0
        })
    
    # Активность по дням (последние 30 дней)
    daily_activity = []
    for i in range(29, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        lessons = Progress.objects.filter(
            completed=True,
            completed_at__date=day
        ).count()
        registrations = User.objects.filter(
            date_joined__date=day
        ).count()
        daily_activity.append({
            'date': day.strftime('%d.%m'),
            'lessons': lessons,
            'registrations': registrations
        })
    
    context = {
        'total_users': total_users,
        'total_lessons_completed': total_lessons_completed,
        'total_tests_passed': total_tests_passed,
        'language_stats': language_stats,
        'test_stats': test_stats,
        'daily_activity': daily_activity,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
    }
    return render(request, 'courses/admin/statistics.html', context)


# ========== ЖУРНАЛ АУДИТА ==========
@admin_required
def admin_audit_log(request):
    """Журнал аудита - последние действия пользователей"""
    
    recent_lessons = Progress.objects.filter(
        completed=True
    ).select_related('user', 'lesson__course__language').order_by('-completed_at')[:50]
    
    recent_tests = TestResult.objects.select_related(
        'user', 'test__lesson__course__language'
    ).order_by('-created_at')[:50]
    
    # Объединяем и сортируем
    activities = []
    
    for p in recent_lessons:
        activities.append({
            'type': 'lesson',
            'user': p.user.username,
            'action': 'завершил урок',
            'target': f'{p.lesson.title} ({p.lesson.course.language.name})',
            'time': p.completed_at,
            'icon': '📚'
        })
    
    for t in recent_tests:
        activities.append({
            'type': 'test',
            'user': t.user.username,
            'action': 'прошел тест',
            'target': f'{t.test.title} - {t.score}/{t.total} ({t.percentage:.0f}%)',
            'time': t.created_at,
            'icon': '📝'
        })
    
    # Добавляем новых пользователей
    new_users = User.objects.order_by('-date_joined')[:20]
    for u in new_users:
        activities.append({
            'type': 'registration',
            'user': u.username,
            'action': 'зарегистрировался',
            'target': '',
            'time': u.date_joined,
            'icon': '👤'
        })
    
    activities.sort(key=lambda x: x['time'], reverse=True)
    
    # Пагинация
    paginator = Paginator(activities, 30)
    page = request.GET.get('page')
    activities_page = paginator.get_page(page)
    
    context = {
        'activities': activities_page,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/audit_log.html', context)
# ========== УПРАВЛЕНИЕ СТУДЕНТАМИ МОДЕРАТОРА ==========

@admin_required
def admin_moderator_students(request, moderator_id):
    """Страница управления студентами модератора"""
    moderator = get_object_or_404(User, id=moderator_id)
    
    # Проверяем, что пользователь действительно модератор
    try:
        if not moderator.userprofile.is_moderator:
            messages.error(request, f'Пользователь {moderator.username} не является модератором')
            return redirect('admin_users')
    except:
        messages.error(request, 'Профиль пользователя не найден')
        return redirect('admin_users')
    
    # Получаем всех студентов модератора
    students = ModeratorStudent.objects.filter(moderator=moderator).select_related('student')
    
    # Получаем всех студентов, которые еще не назначены этому модератору
    existing_student_ids = students.values_list('student_id', flat=True)
    available_students = User.objects.filter(
        userprofile__role='student',
        is_active=True
    ).exclude(id__in=existing_student_ids)
    
    # Поиск по студентам
    search_query = request.GET.get('search', '')
    if search_query:
        available_students = available_students.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(available_students, 20)
    page_number = request.GET.get('page')
    available_students_page = paginator.get_page(page_number)
    
    context = {
        'moderator': moderator,
        'students': students,
        'available_students': available_students_page,
        'search_query': search_query,
        'total_languages': Language.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lessons': Lesson.objects.count(),
        'total_words': Word.objects.count(),
        'total_tests': Test.objects.count(),
        'total_users': User.objects.count(),
    }
    return render(request, 'courses/admin/users/moderator_students.html', context)


@admin_required
def admin_moderator_add_student(request, moderator_id):
    """Добавление студента к модератору"""
    moderator = get_object_or_404(User, id=moderator_id)
    
    # Проверяем, что пользователь действительно модератор
    try:
        if not moderator.userprofile.is_moderator:
            messages.error(request, f'Пользователь {moderator.username} не является модератором')
            return redirect('admin_users')
    except:
        messages.error(request, 'Профиль пользователя не найден')
        return redirect('admin_users')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        notes = request.POST.get('notes', '')
        
        if student_id:
            try:
                student = User.objects.get(id=student_id)
                
                # Проверяем, не назначен ли уже этот студент
                relation, created = ModeratorStudent.objects.get_or_create(
                    moderator=moderator,
                    student=student,
                    defaults={'notes': notes}
                )
                
                if not created and notes:
                    relation.notes = notes
                    relation.save()
                    messages.info(request, f'Заметки обновлены для студента {student.username}')
                elif created:
                    messages.success(request, f'Студент {student.username} добавлен к модератору {moderator.username}')
                else:
                    messages.warning(request, f'Студент {student.username} уже назначен этому модератору')
                    
            except User.DoesNotExist:
                messages.error(request, 'Студент не найден')
        else:
            messages.error(request, 'Выберите студента')
    
    return redirect('admin_moderator_students', moderator_id=moderator.id)


@admin_required
def admin_moderator_remove_student(request, relation_id):
    """Удаление студента от модератора"""
    relation = get_object_or_404(ModeratorStudent, id=relation_id)
    moderator_id = relation.moderator.id
    student_name = relation.student.username
    moderator_name = relation.moderator.username
    
    if request.method == 'POST':
        relation.delete()
        messages.success(request, f'Студент {student_name} удален от модератора {moderator_name}')
    
    return redirect('admin_moderator_students', moderator_id=moderator_id)