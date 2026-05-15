from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
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
from .models import ChatRoom, ChatMessage
from .forms import ChatMessageForm
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Language, Course, Lesson, Word, Progress, Test,
    Question, Answer, TestResult, UserProfile, UserWord,
    ModeratorStudent, ModeratorNote, ChatRoom, ChatMessage,
    LevelTest, LevelTestQuestion, LevelTestAnswer, UserLevelTestResult  # Добавьте эти модели
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


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def is_moderator(user):
    """Проверка, является ли пользователь модератором"""
    try:
        return user.is_authenticated and user.userprofile.is_moderator
    except:
        return False


def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    try:
        return user.is_authenticated and user.userprofile.is_admin
    except:
        return user.is_superuser


# ==================== АУТЕНТИФИКАЦИЯ ====================

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход'
        return context


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
            
            # Создаем профиль (по умолчанию роль 'student')
            UserProfile.objects.create(user=user)
            
            # Авторизуем пользователя
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})


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


# ==================== ОСНОВНЫЕ СТРАНИЦЫ ====================

def home(request):
    """Главная страница для всех пользователей"""
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        if profile.is_moderator:
            return render(request, 'courses/home.html', {
                'profile': profile,
            })
        elif profile.is_admin:
            return render(request, 'courses/home.html', {
                'profile': profile,
            })
        else:
            # Для студентов
            total_lessons_completed = Progress.objects.filter(
                user=request.user, completed=True
            ).count()
            test_results = TestResult.objects.filter(user=request.user)
            total_tests = test_results.count()
            
            if test_results.exists():
                avg_percentage = test_results.aggregate(
                    avg_percent=Avg('percentage')
                )['avg_percent'] or 0
                avg_test_score = round(avg_percentage, 1)
            else:
                avg_test_score = 0
            
            recent_activities = Progress.objects.filter(
                user=request.user,
                completed=True
            ).select_related('lesson', 'lesson__course__language').order_by('-completed_at')[:3]
            
            return render(request, 'courses/home.html', {
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
                'total_languages': Language.objects.count(),
                'total_users': User.objects.count(),
                'total_lessons': Lesson.objects.count(),
                'total_words': Word.objects.count(),
            })
    else:
        # Гости
        return render(request, 'courses/home.html', {
            'total_users': User.objects.count(),
            'total_languages': Language.objects.count(),
            'total_lessons': Lesson.objects.count(),
            'total_words': Word.objects.count(),
        })


@login_required
def dashboard(request):
    """Панель управления с прогрессом"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Если пользователь модератор - перенаправляем на его панель
    if profile.is_moderator:
        return redirect('moderator_dashboard')
    
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
    total_tests = test_results.count()
    
    if test_results.exists():
        avg_percentage = test_results.aggregate(
            avg_percent=Avg('percentage')
        )['avg_percent'] or 0
        avg_test_score = round(avg_percentage, 1)
    else:
        avg_test_score = 0
    
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
            percentage = int((completed / total_lessons) * 100)
            languages_progress.append({
                'language': language,
                'completed': completed,
                'total': total_lessons,
                'percentage': percentage
            })
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_study = Progress.objects.filter(
        user=request.user,
        completed_at__gte=today_start
    ).count() * 15
    
    daily_goal = profile.daily_goal_minutes
    
    if daily_goal > 0:
        goal_percentage_raw = (today_study / daily_goal) * 100
        goal_percentage = min(goal_percentage_raw, 100)
    else:
        goal_percentage = 0
    
    goal_percentage = round(goal_percentage, 1)
    
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
        'goal_percentage': goal_percentage,
        'recent_activity': recent_activity,
        'profile': profile,
    })


# ==================== ЯЗЫКИ И КУРСЫ ====================

def language_list(request):
    """Список языков с прогрессом пользователя"""
    languages = Language.objects.all()
    
    for language in languages:
        total_lessons = 0
        completed_lessons = 0
        
        if request.user.is_authenticated:
            for course in language.courses.all():
                total_lessons += course.lessons.count()
                completed_in_course = Progress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    completed=True
                ).count()
                completed_lessons += completed_in_course
        else:
            for course in language.courses.all():
                total_lessons += course.lessons.count()
        
        if total_lessons > 0:
            progress_percentage = int((completed_lessons / total_lessons) * 100)
        else:
            progress_percentage = 0
        
        language.total_lessons_count = total_lessons
        language.completed_lessons_count = completed_lessons
        language.progress_percentage = progress_percentage
        language.total_words_count = language.total_words
    
    return render(request, 'courses/language_list.html', {
        'languages': languages
    })


def language_detail(request, language_id):
    """Детальная страница языка с курсами"""
    language = get_object_or_404(Language, id=language_id)
    courses = language.courses.filter(is_active=True).order_by('order')
    
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
    
    completed_lesson_ids = []
    if request.user.is_authenticated:
        completed_lesson_ids = Progress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            completed=True
        ).values_list('lesson_id', flat=True)
    
    lesson_data = []
    for lesson in lessons:
        lesson_data.append({
            'lesson': lesson,
            'completed': lesson.id in completed_lesson_ids,
            'words_count': lesson.words.count(),
        })
    
    course_available = True
    if request.user.is_authenticated and course.order > 1:
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


# ==================== УРОКИ ====================

@login_required
def lesson_detail(request, lesson_id):
    """Детальная страница урока"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    words = lesson.words.all()
    course = lesson.course
    
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
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
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += 10
        profile.total_study_time_minutes += 15
        profile.save()
        
        messages.success(request, f'Урок "{lesson.title}" пройден!')
    
    return redirect('lesson_detail', lesson_id=lesson.id)


# ==================== ТЕСТЫ ====================

@login_required
def test_detail(request, test_id):
    """Страница теста с обработкой ответов"""
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all().prefetch_related('answers')
    
    questions_count = questions.count()
    max_xp = questions_count * 5
    
    if request.method == 'POST':
        score = 0
        total = questions_count
        
        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id, question=question)
                    if selected_answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    pass
        
        percentage = (score / total * 100) if total > 0 else 0
        
        result = TestResult.objects.create(
            user=request.user,
            test=test,
            score=score,
            total=total,
            percentage=percentage,
            passed=percentage >= 70
        )
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.xp += score * 5
        profile.save()
        
        return redirect('test_result_detail', test_id=test_id, result_id=result.id)
    
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
    
    if result_id:
        result = get_object_or_404(TestResult, id=result_id, user=request.user, test=test)
    else:
        result = TestResult.objects.filter(
            user=request.user,
            test=test
        ).order_by('-created_at').first()
        
        if not result:
            messages.error(request, 'Вы еще не проходили этот тест')
            return redirect('test_detail', test_id=test_id)
    
    earned_xp = result.score * 5
    wrong_answers = result.total - result.score
    
    return render(request, 'courses/test_result.html', {
        'test': test,
        'result': result,
        'earned_xp': earned_xp,
        'wrong_answers': wrong_answers,
        'percentage': result.percentage,
    })


# ==================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ====================

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
    
    progress = Progress.objects.filter(user=request.user, completed=True).select_related('lesson')
    results = TestResult.objects.filter(user=request.user).select_related('test')
    
    test_results = TestResult.objects.filter(user=request.user)
    total_tests = test_results.count()
    
    if test_results.exists():
        avg_percentage = test_results.aggregate(
            avg_percent=Avg('percentage')
        )['avg_percent'] or 0
        avg_test_score = round(avg_percentage, 1)
    else:
        avg_test_score = 0
    
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
    
    level = profile_obj.xp // 100 + 1
    xp_for_next_level = level * 100
    xp_progress = profile_obj.xp % 100
    
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


# ==================== СЛОВАРЬ ====================

@login_required
def dictionary(request):
    """Словарь пользователя с фильтрацией по языкам"""
    form = SearchForm(request.GET or None)
    
    words = UserWord.objects.filter(user=request.user).select_related(
        'word', 
        'word__lesson', 
        'word__lesson__course', 
        'word__lesson__course__language'
    )
    
    languages = Language.objects.all()
    
    current_language_id = request.GET.get('language')
    if not current_language_id and 'current_dict_language' in request.session:
        current_language_id = request.session.get('current_dict_language')
    
    if current_language_id:
        words = words.filter(word__lesson__course__language_id=current_language_id)
        request.session['current_dict_language'] = current_language_id
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            words = words.filter(
                Q(word__word__icontains=query) |
                Q(word__translation__icontains=query)
            )
    
    words = words.order_by('-last_viewed')
    
    paginator = Paginator(words, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
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
def clear_dictionary_filter(request):
    """Очистка фильтра по языку в словаре"""
    if 'current_dict_language' in request.session:
        del request.session['current_dict_language']
    return redirect('dictionary')


# ==================== ПАНЕЛЬ МОДЕРАТОРА ====================

@login_required
@user_passes_test(is_moderator)
def moderator_dashboard(request):
    """Панель модератора с учениками"""
    profile = request.user.userprofile
    
    students = ModeratorStudent.objects.filter(
        moderator=request.user
    ).select_related('student', 'student__userprofile')
    
    total_students = students.count()
    total_notes = ModeratorNote.objects.filter(moderator=request.user).count()
    
    students_data = []
    for relation in students:
        student = relation.student
        student_profile = student.userprofile
        
        total_lessons = Progress.objects.filter(user=student, completed=True).count()
        total_words = UserWord.objects.filter(user=student, learned=True).count()
        total_xp = student_profile.xp if student_profile else 0
        
        last_activity = Progress.objects.filter(
            user=student, 
            completed=True
        ).order_by('-completed_at').first()
        
        notes = ModeratorNote.objects.filter(
            moderator=request.user,
            student=student
        ).order_by('-created_at')[:5]
        
        # Получаем прогресс по курсам для каждого ученика
        courses_progress = []
        courses = Course.objects.filter(is_active=True)
        for course in courses:
            total_lessons_course = course.lessons.count()
            completed = Progress.objects.filter(
                user=student,
                lesson__course=course,
                completed=True
            ).count()
            if total_lessons_course > 0:
                courses_progress.append({
                    'course': course,
                    'completed': completed,
                    'total': total_lessons_course,
                    'percentage': int((completed / total_lessons_course) * 100) if total_lessons_course > 0 else 0
                })
        
        students_data.append({
            'student': student,
            'profile': student_profile,
            'total_lessons': total_lessons,
            'total_words': total_words,
            'total_xp': total_xp,
            'last_activity': last_activity.completed_at if last_activity else None,
            'notes': notes,
            'relation_id': relation.id,
            'courses_progress': courses_progress[:3],  # Показываем первые 3 курса
        })
    
    top_students = sorted(students_data, key=lambda x: x['total_xp'], reverse=True)[:5]
    
    last_week = timezone.now() - timedelta(days=7)
    weekly_activity = Progress.objects.filter(
        user__in=[s.student for s in students],
        completed=True,
        completed_at__gte=last_week
    ).count()
    
    # Для админов - список всех пользователей для назначения
    all_moderators = []
    all_students = []
    if request.user.is_superuser:
        all_moderators = User.objects.filter(userprofile__role='moderator')
        all_students = User.objects.filter(userprofile__role='student')
    
    return render(request, 'courses/moderator/dashboard.html', {
        'profile': profile,
        'students_data': students_data,
        'total_students': total_students,
        'total_notes': total_notes,
        'top_students': top_students,
        'weekly_activity': weekly_activity,
        'all_moderators': all_moderators,
        'all_students': all_students,
    })


@login_required
@user_passes_test(is_moderator)
def moderator_student_detail(request, student_id):
    """Детальная страница ученика для модератора"""
    try:
        relation = ModeratorStudent.objects.get(
            moderator=request.user,
            student_id=student_id
        )
    except ModeratorStudent.DoesNotExist:
        messages.error(request, 'У вас нет доступа к этому ученику')
        return redirect('moderator_dashboard')
    
    student = relation.student
    student_profile = student.userprofile
    
    total_lessons = Progress.objects.filter(user=student, completed=True).count()
    total_tests = TestResult.objects.filter(user=student).count()
    
    test_results_avg = TestResult.objects.filter(user=student)
    if test_results_avg.exists():
        avg_test_score = test_results_avg.aggregate(avg=Avg('percentage'))['avg'] or 0
    else:
        avg_test_score = 0
    
    total_words_learned = UserWord.objects.filter(user=student, learned=True).count()
    total_study_time = Progress.objects.filter(user=student, completed=True).aggregate(
        total=Sum('lesson__estimated_time_minutes')
    )['total'] or 0
    
    courses_progress = []
    courses = Course.objects.filter(is_active=True)
    for course in courses:
        total_lessons_course = course.lessons.count()
        completed = Progress.objects.filter(
            user=student,
            lesson__course=course,
            completed=True
        ).count()
        
        if total_lessons_course > 0:
            courses_progress.append({
                'course': course,
                'completed': completed,
                'total': total_lessons_course,
                'percentage': int((completed / total_lessons_course) * 100)
            })
    
    recent_progress = Progress.objects.filter(
        user=student,
        completed=True
    ).select_related('lesson', 'lesson__course').order_by('-completed_at')[:10]
    
    notes = ModeratorNote.objects.filter(
        moderator=request.user,
        student=student
    ).order_by('-created_at')
    
    test_results = TestResult.objects.filter(
        user=student
    ).select_related('test', 'test__lesson').order_by('-created_at')[:10]
    
    return render(request, 'courses/moderator/student_detail.html', {
        'student': student,
        'student_profile': student_profile,
        'relation': relation,
        'total_lessons': total_lessons,
        'total_tests': total_tests,
        'avg_test_score': round(avg_test_score, 1),
        'total_words_learned': total_words_learned,
        'total_study_hours': round(total_study_time / 60, 1),
        'courses_progress': courses_progress,
        'recent_progress': recent_progress,
        'notes': notes,
        'test_results': test_results,
    })


@login_required
@user_passes_test(is_moderator)
def moderator_add_note(request, student_id):
    """Добавление заметки об ученике"""
    if request.method == 'POST':
        note_text = request.POST.get('note', '').strip()
        
        if note_text:
            ModeratorNote.objects.create(
                moderator=request.user,
                student_id=student_id,
                note=note_text
            )
            messages.success(request, 'Заметка добавлена')
        else:
            messages.error(request, 'Заметка не может быть пустой')
    
    return redirect('moderator_student_detail', student_id=student_id)


@login_required
@user_passes_test(is_moderator)
def moderator_delete_note(request, note_id):
    """Удаление заметки"""
    try:
        note = ModeratorNote.objects.get(id=note_id, moderator=request.user)
        student_id = note.student.id
        note.delete()
        messages.success(request, 'Заметка удалена')
        return redirect('moderator_student_detail', student_id=student_id)
    except ModeratorNote.DoesNotExist:
        messages.error(request, 'Заметка не найдена')
        return redirect('moderator_dashboard')


@login_required
@user_passes_test(is_admin)
def moderator_assign_student(request):
    """Назначение ученика модератору (только для админов)"""
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        moderator_id = request.POST.get('moderator_id')
        
        try:
            student = User.objects.get(id=student_id)
            moderator = User.objects.get(id=moderator_id)
            
            if not moderator.userprofile.is_moderator:
                messages.error(request, 'Выбранный пользователь не является модератором')
                return redirect('moderator_dashboard')
            
            ModeratorStudent.objects.get_or_create(
                moderator=moderator,
                student=student
            )
            messages.success(request, f'Ученик {student.username} назначен модератору {moderator.username}')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден')
    
    return redirect('moderator_dashboard')


@login_required
@user_passes_test(is_moderator)
def moderator_remove_student(request, relation_id):
    """Удаление ученика от модератора"""
    if request.method == 'POST':
        try:
            relation = ModeratorStudent.objects.get(
                id=relation_id,
                moderator=request.user
            )
            student_name = relation.student.username
            relation.delete()
            messages.success(request, f'Ученик {student_name} удален')
            return JsonResponse({'success': True})
        except ModeratorStudent.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Связь не найдена'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# ==================== API И ТЕСТОВЫЕ ФУНКЦИИ ====================

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
            'avg_test_score': avg_test_score,
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


def test_email(request):
    """Тестовая отправка email"""
    try:
        send_mail(
            'Тестовое письмо от LangLearn',
            'Это тестовое письмо для проверки настроек email.',
            settings.DEFAULT_FROM_EMAIL,
            ['your-test-email@gmail.com'],
            fail_silently=False,
            html_message='<h1>Тестовое письмо</h1><p>Если вы видите это, email работает!</p>'
        )
        return HttpResponse('Email отправлен успешно!')
    except Exception as e:
        return HttpResponse(f'Ошибка отправки email: {str(e)}')


def password_reset_done_custom(request):
    messages.success(request, 'Письмо для восстановления пароля отправлено на ваш email!')
    return render(request, 'registration/password_reset_done.html')


# ==================== ЧАТ ====================
# ==================== ЧАТ ====================

@login_required
def chat_list(request):
    """Список чатов пользователя"""
    user = request.user
    profile = user.userprofile
    
    chats = []
    
    if profile.is_admin:
        # Админ: чаты с модераторами и студентами
        moderator_chats = ChatRoom.objects.filter(
            room_type='admin_moderator',
            admin=user
        ).select_related('moderator')
        
        student_chats = ChatRoom.objects.filter(
            room_type='admin_student',
            admin=user
        ).select_related('student')
        
        for chat in moderator_chats:
            chat.other_user = chat.moderator
            chat.unread_count = chat.get_unread_count(user)
            chat.last_message = chat.get_last_message()
            chat.role = "Модератор"
            chat.role_icon = ""
            chats.append(chat)
        
        for chat in student_chats:
            chat.other_user = chat.student
            chat.unread_count = chat.get_unread_count(user)
            chat.last_message = chat.get_last_message()
            chat.role = "Ученик"
            chat.role_icon = ""
            chats.append(chat)
            
    elif profile.is_moderator:
        # Модератор: чаты со студентами и админом
        student_chats = ChatRoom.objects.filter(
            room_type='moderator_student',
            moderator=user
        ).select_related('student')
        
        admin_chat = ChatRoom.objects.filter(
            room_type='admin_moderator',
            moderator=user
        ).first()
        
        for chat in student_chats:
            chat.other_user = chat.student
            chat.unread_count = chat.get_unread_count(user)
            chat.last_message = chat.get_last_message()
            chat.role = "Ученик"
            chat.role_icon = ""
            chats.append(chat)
        
        if admin_chat:
            admin_chat.other_user = admin_chat.admin
            admin_chat.unread_count = admin_chat.get_unread_count(user)
            admin_chat.last_message = admin_chat.get_last_message()
            admin_chat.role = "Админ"
            admin_chat.role_icon = ""
            chats.append(admin_chat)
            
    else:
        # Студент: чаты с модераторами
        moderator_chats = ChatRoom.objects.filter(
            room_type='moderator_student',
            student=user
        ).select_related('moderator')
        
        for chat in moderator_chats:
            chat.other_user = chat.moderator
            chat.unread_count = chat.get_unread_count(user)
            chat.last_message = chat.get_last_message()
            chat.role = "Модератор"
            chat.role_icon = ""
            chats.append(chat)
    
    # Сортируем по дате последнего сообщения
    chats.sort(key=lambda x: x.updated_at if x.updated_at else x.created_at, reverse=True)
    
    context = {
        'chats': chats,
        'profile': profile,
    }
    return render(request, 'courses/chat/list.html', context)


@login_required
def chat_detail(request, room_id):
    """Детальная страница чата"""
    room = get_object_or_404(ChatRoom, id=room_id)
    user = request.user
    profile = user.userprofile
    
    # Проверяем доступ к чату
    has_access = False
    if profile.is_admin:
        has_access = (room.room_type == 'admin_moderator' and room.admin == user) or \
                     (room.room_type == 'admin_student' and room.admin == user)
    elif profile.is_moderator:
        has_access = (room.room_type == 'moderator_student' and room.moderator == user) or \
                     (room.room_type == 'admin_moderator' and room.moderator == user)
    else:
        has_access = (room.room_type == 'moderator_student' and room.student == user)
    
    if not has_access:
        messages.error(request, 'У вас нет доступа к этому чату')
        return redirect('chat_list')
    
    other_user = room.get_other_user(user)
    other_profile = other_user.userprofile
    
    # Определяем роль собеседника
    if other_profile.is_admin:
        other_role = "Администратор"
        other_role_icon = "👑"
    elif other_profile.is_moderator:
        other_role = "Модератор"
        other_role_icon = "👨‍🏫"
    else:
        other_role = "Студент"
        other_role_icon = "👨‍🎓"
    
    # Получаем все сообщения
    messages_list = ChatMessage.objects.filter(room=room).order_by('created_at')
    
    # Отмечаем непрочитанные сообщения
    unread_messages = messages_list.filter(receiver=user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()
    
    # Обработка отправки
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.room = room
            message.sender = user
            message.receiver = other_user
            message.save()
            
            room.updated_at = timezone.now()
            room.save()
            
            return redirect('chat_detail', room_id=room.id)
    else:
        form = ChatMessageForm()
    
    context = {
        'room': room,
        'other_user': other_user,
        'other_role': other_role,
        'other_role_icon': other_role_icon,
        'messages': messages_list,
        'form': form,
        'profile': profile,
    }
    return render(request, 'courses/chat/detail.html', context)


@login_required
def chat_create(request):
    """Создание нового чата"""
    user = request.user
    profile = user.userprofile
    user_id = request.GET.get('user_id')
    room_type = request.GET.get('type', '')
    
    if not user_id:
        messages.error(request, 'Не указан пользователь')
        return redirect('chat_list')
    
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect('chat_list')
    
    other_profile = other_user.userprofile
    
    room = None
    
    if profile.is_admin:
        # Админ создает чат
        if other_profile.is_moderator:
            room, created = ChatRoom.objects.get_or_create(
                room_type='admin_moderator',
                admin=user,
                moderator=other_user
            )
        else:
            room, created = ChatRoom.objects.get_or_create(
                room_type='admin_student',
                admin=user,
                student=other_user
            )
            
    elif profile.is_moderator:
        # Модератор создает чат со студентом или админом
        if not other_profile.is_moderator and not other_profile.is_admin:
            # Чат со студентом
            room, created = ChatRoom.objects.get_or_create(
                room_type='moderator_student',
                moderator=user,
                student=other_user
            )
        elif other_profile.is_admin:
            # Чат с админом
            room, created = ChatRoom.objects.get_or_create(
                room_type='admin_moderator',
                admin=other_user,
                moderator=user
            )
        else:
            messages.error(request, 'Вы можете общаться только со студентами и администратором')
            return redirect('chat_list')
            
    else:
        # Студент может создать чат только со своим модератором
        # Проверяем, есть ли у студента модератор
        student_relation = ModeratorStudent.objects.filter(student=user).first()
        if student_relation and student_relation.moderator == other_user:
            room, created = ChatRoom.objects.get_or_create(
                room_type='moderator_student',
                moderator=other_user,
                student=user
            )
        else:
            messages.error(request, 'Вы можете общаться только со своим модератором')
            return redirect('chat_list')
    
    if room:
        if created:
            messages.success(request, f'Чат с {other_user.username} создан!')
        else:
            messages.info(request, f'Чат с {other_user.username} уже существует')
        return redirect('chat_detail', room_id=room.id)
    
    messages.error(request, 'Не удалось создать чат')
    return redirect('chat_list')


@login_required
def chat_send_ajax(request):
    """Отправка сообщения через AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'error': 'Message is empty'}, status=400)
        
        room = get_object_or_404(ChatRoom, id=room_id)
        user = request.user
        profile = user.userprofile
        
        # Проверяем доступ
        has_access = False
        if profile.is_admin:
            has_access = (room.room_type == 'admin_moderator' and room.admin == user) or \
                         (room.room_type == 'admin_student' and room.admin == user)
        elif profile.is_moderator:
            has_access = (room.room_type == 'moderator_student' and room.moderator == user) or \
                         (room.room_type == 'admin_moderator' and room.moderator == user)
        else:
            has_access = (room.room_type == 'moderator_student' and room.student == user)
        
        if not has_access:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        other_user = room.get_other_user(user)
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user,
            receiver=other_user,
            message=message_text
        )
        
        room.updated_at = timezone.now()
        room.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'text': message.message,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def chat_get_messages_ajax(request, room_id):
    """Получение новых сообщений через AJAX"""
    last_message_id = request.GET.get('last_id', 0)
    
    try:
        last_id = int(last_message_id)
    except ValueError:
        last_id = 0
    
    room = get_object_or_404(ChatRoom, id=room_id)
    user = request.user
    
    # Проверяем доступ
    profile = user.userprofile
    has_access = False
    if profile.is_admin:
        has_access = (room.room_type == 'admin_moderator' and room.admin == user) or \
                     (room.room_type == 'admin_student' and room.admin == user)
    elif profile.is_moderator:
        has_access = (room.room_type == 'moderator_student' and room.moderator == user) or \
                     (room.room_type == 'admin_moderator' and room.moderator == user)
    else:
        has_access = (room.room_type == 'moderator_student' and room.student == user)
    
    if not has_access:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    new_messages = ChatMessage.objects.filter(
        room=room,
        id__gt=last_id
    ).order_by('created_at')
    
    # Отмечаем прочитанные
    unread_messages = new_messages.filter(receiver=user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()
    
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'text': msg.message,
            'sender': msg.sender.username,
            'is_mine': msg.sender == user,
            'created_at': msg.created_at.strftime('%H:%M'),
            'is_read': msg.is_read
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'last_id': new_messages.last().id if new_messages else last_id
    })


@login_required
def chat_unread_count_ajax(request):
    """Получение количества непрочитанных сообщений"""
    user = request.user
    profile = user.userprofile
    
    unread_count = 0
    
    if profile.is_admin:
        rooms = ChatRoom.objects.filter(
            Q(room_type='admin_moderator', admin=user) |
            Q(room_type='admin_student', admin=user)
        )
    elif profile.is_moderator:
        rooms = ChatRoom.objects.filter(
            Q(room_type='moderator_student', moderator=user) |
            Q(room_type='admin_moderator', moderator=user)
        )
    else:
        rooms = ChatRoom.objects.filter(room_type='moderator_student', student=user)
    
    for room in rooms:
        unread_count += room.get_unread_count(user)
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count
    })
# ==================== ОБРАБОТЧИКИ ОШИБОК ====================

def custom_404(request, exception):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)

@login_required
@user_passes_test(is_moderator)
def chat_admin(request):
    """Чат модератора с администратором"""
    user = request.user
    
    # Находим или создаем чат с админом
    # Берем первого суперпользователя как админа
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        messages.error(request, 'Администратор не найден')
        return redirect('moderator_dashboard')
    
    # Создаем или получаем существующий чат
    room, created = ChatRoom.objects.get_or_create(
        room_type='admin_moderator',
        admin=admin_user,
        moderator=user
    )
    
    return redirect('chat_detail', room_id=room.id)
# ==================== ВСТУПИТЕЛЬНЫЙ ТЕСТ ====================


@login_required
def level_test_start(request, language_id):
    """Начало вступительного теста"""
    language = get_object_or_404(Language, id=language_id)
    
    # Проверяем, проходил ли пользователь тест ранее
    existing_result = UserLevelTestResult.objects.filter(
        user=request.user,
        language=language
    ).order_by('-created_at').first()
    
    if existing_result:
        return render(request, 'courses/level_test/start.html', {
            'language': language,
            'existing_result': existing_result,
        })
    
    # Получаем тест для языка
    try:
        level_test = LevelTest.objects.get(language=language)
    except LevelTest.DoesNotExist:
        messages.warning(request, f'Тест для {language.name} еще не настроен. Обратитесь к администратору.')
        return redirect('language_detail', language_id=language_id)
    
    questions = level_test.questions.all().order_by('order')
    
    if questions.count() == 0:
        messages.warning(request, f'Тест для {language.name} не содержит вопросов. Обратитесь к администратору.')
        return redirect('language_detail', language_id=language_id)
    
    return render(request, 'courses/level_test/test.html', {
        'language': language,
        'test': level_test,
        'questions': questions,
        'total_questions': questions.count()
    })

@login_required
def level_test_submit(request, language_id):
    """Обработка результатов вступительного теста"""
    if request.method != 'POST':
        return redirect('level_test_start', language_id=language_id)
    
    language = get_object_or_404(Language, id=language_id)
    level_test = LevelTest.objects.filter(language=language).first()
    
    if not level_test:
        messages.error(request, 'Тест не найден')
        return redirect('language_detail', language_id=language_id)
    
    questions = level_test.questions.all().order_by('order')
    total = questions.count()
    score = 0
    
    # Подсчет баллов по сложности вопросов
    level_correct = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0, 'C1': 0}
    level_total = {'A1': 0, 'A2': 0, 'B1': 0, 'B2': 0, 'C1': 0}
    
    for question in questions:
        selected_answer_id = request.POST.get(f'question_{question.id}')
        if selected_answer_id:
            try:
                selected_answer = LevelTestAnswer.objects.get(id=selected_answer_id, question=question)
                q_level = selected_answer.difficulty_level or 'A1'
                level_total[q_level] = level_total.get(q_level, 0) + 1
                
                if selected_answer.is_correct:
                    score += 1
                    level_correct[q_level] = level_correct.get(q_level, 0) + 1
            except LevelTestAnswer.DoesNotExist:
                pass
    
    # Вычисление процента для каждого уровня
    level_percentages = {}
    for level in ['A1', 'A2', 'B1', 'B2', 'C1']:
        if level_total[level] > 0:
            level_percentages[level] = (level_correct[level] / level_total[level]) * 100
        else:
            level_percentages[level] = 0
    
    # Определение рекомендуемого уровня
    recommended_level = 'A1'  # По умолчанию
    
    # Проверяем прохождение каждого уровня
    if level_percentages.get('C1', 0) >= 70:
        recommended_level = 'C1'
    elif level_percentages.get('B2', 0) >= 70:
        recommended_level = 'B2'
    elif level_percentages.get('B1', 0) >= 70:
        recommended_level = 'B1'
    elif level_percentages.get('A2', 0) >= 70:
        recommended_level = 'A2'
    else:
        recommended_level = 'A1'
    
    overall_percentage = (score / total * 100) if total > 0 else 0
    
    # Сохраняем результат
    result = UserLevelTestResult.objects.create(
        user=request.user,
        language=language,
        test=level_test,
        score=score,
        total=total,
        percentage=overall_percentage,
        recommended_level=recommended_level
    )
    
    # Открываем уроки до рекомендуемого уровня
    auto_complete_lessons_up_to_level(request.user, language, recommended_level)
    
    messages.success(request, f'Тест пройден! Результат: {score}/{total} ({overall_percentage:.0f}%). Ваш уровень: {recommended_level}')
    
    return redirect('level_test_result', language_id=language_id, result_id=result.id)

@login_required
def level_test_skip(request, language_id):
    """Пропустить тест и начать с A1"""
    language = get_object_or_404(Language, id=language_id)
    
    UserLevelTestResult.objects.create(
        user=request.user,
        language=language,
        test=None,
        score=0,
        total=0,
        percentage=0,
        recommended_level='A1'
    )
    
    messages.info(request, f'Вы начали изучение {language.name} с уровня A1')
    return redirect('language_detail', language_id=language_id)


@login_required
def level_test_question(request, language_id):
    """Страница с вопросами теста"""
    language = get_object_or_404(Language, id=language_id)
    level_test = LevelTest.objects.filter(language=language).first()
    
    if not level_test:
        # Создаем тест, если его нет
        level_test = LevelTest.objects.create(
            language=language,
            title=f'Определение уровня {language.name}'
        )
        # Здесь нужно добавить создание вопросов
    
    questions = level_test.questions.all().order_by('order')
    
    if questions.count() == 0:
        messages.warning(request, 'Тест еще не настроен. Пожалуйста, попробуйте позже.')
        return redirect('language_detail', language_id=language_id)
    
    return render(request, 'courses/level_test/question.html', {
        'language': language,
        'test': level_test,
        'questions': questions,
        'total_questions': questions.count()
    })
def auto_complete_lessons_up_to_level(user, language, target_level):
    """Автоматически отмечает уроки как ДОСТУПНЫЕ (не пройденные) до целевого уровня"""
    levels_order = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
    target_order = levels_order.get(target_level, 1)
    
    courses = language.courses.filter(is_active=True).order_by('order')
    
    for course in courses:
        course_order = levels_order.get(course.level, 1)
        
        # Если курс ниже целевого уровня - делаем все уроки ПРОЙДЕННЫМИ
        if course_order < target_order:
            for lesson in course.lessons.all():
                progress, created = Progress.objects.get_or_create(
                    user=user,
                    lesson=lesson
                )
                if not progress.completed:
                    progress.completed = True
                    progress.completed_at = timezone.now()
                    progress.save()
                    
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.xp += 10
                    profile.save()
        
        # Если курс равен целевому уровню - делаем уроки ДОСТУПНЫМИ, но НЕ ПРОЙДЕННЫМИ
        elif course_order == target_order:
            # Создаем записи прогресса, но НЕ отмечаем как пройденные
            for lesson in course.lessons.all():
                Progress.objects.get_or_create(
                    user=user,
                    lesson=lesson,
                    defaults={'completed': False}
                )

@login_required
def level_test_result(request, language_id, result_id):
    """Страница результата теста уровня"""
    language = get_object_or_404(Language, id=language_id)
    result = get_object_or_404(UserLevelTestResult, id=result_id, user=request.user, language=language)
    
    return render(request, 'courses/level_test/result.html', {
        'language': language,
        'result': result,
        'score': result.score,
        'total': result.total,
        'percentage': result.percentage,
        'recommended_level': result.recommended_level,
    })

@login_required
def chat_user_list(request):
    """API для получения списка пользователей для нового чата"""
    user = request.user
    profile = user.userprofile
    
    users_list = []
    
    if profile.is_admin:
        # Админ может писать всем модераторам и студентам
        # Модераторы
        moderators = User.objects.filter(userprofile__role='moderator').exclude(id=user.id)
        for m in moderators:
            users_list.append({
                'id': m.id,
                'username': m.username,
                'role': 'Модератор',
                'role_icon': 'fa-user-tie'
            })
        # Студенты
        students = User.objects.filter(userprofile__role='student').exclude(id=user.id)
        for s in students:
            users_list.append({
                'id': s.id,
                'username': s.username,
                'role': 'Студент',
                'role_icon': 'fa-user-graduate'
            })
            
    elif profile.is_moderator:
        # Модератор может писать своим ученикам и админу
        # Свои ученики
        students = ModeratorStudent.objects.filter(moderator=user).select_related('student')
        for s in students:
            users_list.append({
                'id': s.student.id,
                'username': s.student.username,
                'role': 'Мой ученик',
                'role_icon': 'fa-user-graduate'
            })
        # Админ
        admin = User.objects.filter(is_superuser=True).first()
        if admin and admin.id != user.id:
            users_list.append({
                'id': admin.id,
                'username': admin.username,
                'role': 'Администратор',
                'role_icon': 'fa-crown'
            })
            
    else:
        # Студент может писать только своему модератору
        moderator_rel = ModeratorStudent.objects.filter(student=user).first()
        if moderator_rel:
            users_list.append({
                'id': moderator_rel.moderator.id,
                'username': moderator_rel.moderator.username,
                'role': 'Мой модератор',
                'role_icon': 'fa-user-tie'
            })
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        users_list = [u for u in users_list if search.lower() in u['username'].lower()]
    
    return JsonResponse({
        'success': True,
        'users': users_list
    })