from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import (
    Language, Course, Lesson, Word, UserProfile, UserWord,
    Progress, Test, Question, Answer, TestResult
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профили'
    fieldsets = (
        ('Основная информация', {
            'fields': ('bio', 'avatar_url', 'current_language')
        }),
        ('Статистика', {
            'fields': ('daily_goal_minutes', 'streak_days', 'total_study_time_minutes')
        }),
        ('Прогресс', {
            'fields': ('xp', 'level')
        }),
    )
    classes = ('wide',)


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'date_joined', 'last_login', 'user_level', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'userprofile__level')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    def user_level(self, obj):
        try:
            level = obj.userprofile.level
            xp = obj.userprofile.xp
            return format_html(
                '<span style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600;">Ур. {} ({} XP)</span>',
                level, xp
            )
        except:
            return '-'
    user_level.short_description = 'Уровень'


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_display', 'total_courses', 'total_lessons', 'total_words', 'active_students')
    list_display_links = ('name',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def icon_display(self, obj):
        return format_html('<i class="{}" style="font-size: 1.2rem; color: #4361ee;"></i>', obj.icon or 'fas fa-language')
    icon_display.short_description = 'Иконка'
    
    def total_courses(self, obj):
        count = obj.courses.count()
        url = reverse('admin:courses_course_changelist') + f'?language__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: 600;">{} курс(ов)</a>', url, count)
    total_courses.short_description = 'Курсов'
    
    def total_lessons(self, obj):
        total = sum(course.lessons.count() for course in obj.courses.all())
        return total
    total_lessons.short_description = 'Уроков'
    
    def total_words(self, obj):
        total = 0
        for course in obj.courses.all():
            for lesson in course.lessons.all():
                total += lesson.words.count()
        return f'{total} слов'
    total_words.short_description = 'Слов'
    
    def active_students(self, obj):
        last_week = timezone.now() - timedelta(days=7)
        students = Progress.objects.filter(
            lesson__course__language=obj,
            completed_at__gte=last_week
        ).values('user').distinct().count()
        return format_html('<span style="color: #28a745;">{} 👤</span>', students)
    active_students.short_description = 'Активных'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'language_link', 'level_badge', 'order', 'is_active', 'lesson_count', 'word_count', 'progress_percentage')
    list_filter = ('language', 'level', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('language', 'order')
    list_editable = ('order', 'is_active')
    list_per_page = 20
    
    def language_link(self, obj):
        url = reverse('admin:courses_language_change', args=[obj.language.id])
        return format_html('<a href="{}">{}</a>', url, obj.language.name)
    language_link.short_description = 'Язык'
    
    def level_badge(self, obj):
        colors = {
            'A1': '#28a745', 'A2': '#20c997',
            'B1': '#17a2b8', 'B2': '#007bff',
            'C1': '#fd7e14', 'C2': '#dc3545'
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600;">{}</span>',
            color, obj.get_level_display()
        )
    level_badge.short_description = 'Уровень'
    
    def lesson_count(self, obj):
        count = obj.lessons.count()
        url = reverse('admin:courses_lesson_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{} уроков</a>', url, count)
    lesson_count.short_description = 'Уроков'
    
    def word_count(self, obj):
        total = 0
        for lesson in obj.lessons.all():
            total += lesson.words.count()
        return f'{total} слов'
    word_count.short_description = 'Слов'
    
    def progress_percentage(self, obj):
        completed = Progress.objects.filter(lesson__course=obj, completed=True).count()
        total_lessons = obj.lessons.count()
        if total_lessons > 0:
            users = Progress.objects.filter(lesson__course=obj).values('user').distinct().count()
            if users > 0:
                avg_completed = completed / users
                percentage = (avg_completed / total_lessons) * 100
                return format_html(
                    '<div style="width: 100px; height: 6px; background: #e9ecef; border-radius: 3px;">'
                    '<div style="width: {}%; height: 100%; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 3px;"></div>'
                    '</div>',
                    percentage
                )
        return '-'
    progress_percentage.short_description = 'Прогресс'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_link', 'order', 'word_count', 'estimated_time')
    list_filter = ('course__language', 'course')
    search_fields = ('title', 'content')
    ordering = ('course', 'order')
    list_editable = ('order',)
    
    def course_link(self, obj):
        url = reverse('admin:courses_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Курс'
    
    def word_count(self, obj):
        count = obj.words.count()
        url = reverse('admin:courses_word_changelist') + f'?lesson__id__exact={obj.id}'
        return format_html('<a href="{}">{} слов</a>', url, count)
    word_count.short_description = 'Слов'
    
    def estimated_time(self, obj):
        return f'{obj.estimated_time_minutes} мин'
    estimated_time.short_description = 'Время'


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'transcription', 'part_of_speech', 'lesson_link', 'example_short')
    list_filter = ('lesson__course__language', 'part_of_speech', 'lesson__course')
    search_fields = ('word', 'translation', 'example')
    ordering = ('word',)
    list_per_page = 30
    
    def lesson_link(self, obj):
        url = reverse('admin:courses_lesson_change', args=[obj.lesson.id])
        return format_html('<a href="{}">{}</a>', url, obj.lesson.title)
    lesson_link.short_description = 'Урок'
    
    def example_short(self, obj):
        if obj.example:
            return obj.example[:50] + '...' if len(obj.example) > 50 else obj.example
        return '-'
    example_short.short_description = 'Пример'


@admin.register(UserWord)
class UserWordAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'word_link', 'status_icons', 'times_viewed', 'last_viewed')
    list_filter = ('is_favorite', 'learned', 'word__lesson__course__language')
    search_fields = ('user__username', 'word__word')
    list_select_related = ('user', 'word')
    raw_id_fields = ('user', 'word')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    
    def word_link(self, obj):
        url = reverse('admin:courses_word_change', args=[obj.word.id])
        return format_html('<a href="{}">{}</a>', url, obj.word.word)
    word_link.short_description = 'Слово'
    
    def status_icons(self, obj):
        icons = []
        if obj.is_favorite:
            icons.append('<span style="color: #dc3545;">❤️ Избранное</span>')
        if obj.learned:
            icons.append('<span style="color: #28a745;">✅ Изучено</span>')
        return format_html('<br>'.join(icons)) if icons else '-'
    status_icons.short_description = 'Статус'


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'lesson_link', 'completed_badge', 'completed_at')
    list_filter = ('completed', 'lesson__course__language', 'lesson__course')
    search_fields = ('user__username', 'lesson__title')
    list_select_related = ('user', 'lesson')
    raw_id_fields = ('user', 'lesson')
    date_hierarchy = 'completed_at'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    
    def lesson_link(self, obj):
        url = reverse('admin:courses_lesson_change', args=[obj.lesson.id])
        return format_html('<a href="{}">{}</a>', url, obj.lesson.title)
    lesson_link.short_description = 'Урок'
    
    def completed_badge(self, obj):
        if obj.completed:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 20px;">✓ Пройдено</span>')
        return format_html('<span style="background: #6c757d; color: white; padding: 3px 10px; border-radius: 20px;">○ В процессе</span>')
    completed_badge.short_description = 'Статус'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson_link', 'question_count', 'times_passed')
    search_fields = ('title', 'lesson__title')
    list_select_related = ('lesson',)
    raw_id_fields = ('lesson',)
    
    def lesson_link(self, obj):
        url = reverse('admin:courses_lesson_change', args=[obj.lesson.id])
        return format_html('<a href="{}">{}</a>', url, obj.lesson.title)
    lesson_link.short_description = 'Урок'
    
    def question_count(self, obj):
        count = obj.questions.count()
        url = reverse('admin:courses_question_changelist') + f'?test__id__exact={obj.id}'
        return format_html('<a href="{}">{} вопросов</a>', url, count)
    question_count.short_description = 'Вопросов'
    
    def times_passed(self, obj):
        passed = TestResult.objects.filter(test=obj, passed=True).count()
        total = TestResult.objects.filter(test=obj).count()
        if total > 0:
            percentage = (passed / total) * 100
            return f'{passed}/{total} ({percentage:.0f}%)'
        return '0'
    times_passed.short_description = 'Сдали'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'test_link', 'answer_count', 'correct_answer')
    search_fields = ('text',)
    list_select_related = ('test',)
    raw_id_fields = ('test',)
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Вопрос'
    
    def test_link(self, obj):
        url = reverse('admin:courses_test_change', args=[obj.test.id])
        return format_html('<a href="{}">{}</a>', url, obj.test.title)
    test_link.short_description = 'Тест'
    
    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = 'Ответов'
    
    def correct_answer(self, obj):
        correct = obj.answers.filter(is_correct=True).first()
        if correct:
            return correct.text[:30] + '...' if len(correct.text) > 30 else correct.text
        return '-'
    correct_answer.short_description = 'Правильный ответ'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'question_link', 'correct_badge')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')
    list_select_related = ('question',)
    raw_id_fields = ('question',)
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Ответ'
    
    def question_link(self, obj):
        url = reverse('admin:courses_question_change', args=[obj.question.id])
        return format_html('<a href="{}">{}</a>', url, obj.question.text[:30])
    question_link.short_description = 'Вопрос'
    
    def correct_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="color: #28a745;">✓ Правильный</span>')
        return format_html('<span style="color: #dc3545;">✗ Неправильный</span>')
    correct_badge.short_description = 'Статус'


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'test_link', 'score_display', 'percentage_badge', 'passed_badge', 'created_at')
    list_filter = ('passed', 'created_at', 'test__lesson__course__language')
    search_fields = ('user__username', 'test__title')
    list_select_related = ('user', 'test')
    raw_id_fields = ('user', 'test')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    
    def test_link(self, obj):
        url = reverse('admin:courses_test_change', args=[obj.test.id])
        return format_html('<a href="{}">{}</a>', url, obj.test.title)
    test_link.short_description = 'Тест'
    
    def score_display(self, obj):
        return f'{obj.score}/{obj.total}'
    score_display.short_description = 'Результат'
    
    def percentage_badge(self, obj):
        if obj.percentage >= 70:
            return format_html('<span style="color: #28a745; font-weight: 600;">{}%</span>', obj.percentage)
        return format_html('<span style="color: #dc3545; font-weight: 600;">{}%</span>', obj.percentage)
    percentage_badge.short_description = 'Процент'
    
    def passed_badge(self, obj):
        if obj.passed:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 20px;">Пройден</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 10px; border-radius: 20px;">Не пройден</span>')
    passed_badge.short_description = 'Статус'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'level_badge', 'xp', 'streak_days', 'daily_goal', 'last_active')
    list_filter = ('level', 'current_language')
    search_fields = ('user__username', 'user__email', 'bio')
    raw_id_fields = ('user', 'current_language')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    
    def level_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600;">Уровень {}</span>',
            obj.level
        )
    level_badge.short_description = 'Уровень'
    
    def daily_goal(self, obj):
        return f'{obj.daily_goal_minutes} мин'
    daily_goal.short_description = 'Цель'
    
    def last_active(self, obj):
        progress = Progress.objects.filter(user=obj.user, completed=True).order_by('-completed_at').first()
        if progress and progress.completed_at:
            return progress.completed_at.strftime('%d.%m.%Y %H:%M')
        return 'Нет активности'
    last_active.short_description = 'Последняя активность'


# Кастомный дашборд админки
class CustomAdminSite(admin.AdminSite):
    site_header = 'LangLearn - Панель управления'
    site_title = 'LangLearn Admin'
    index_title = 'Обзор системы'
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Общая статистика
        extra_context['total_users'] = User.objects.count()
        extra_context['total_languages'] = Language.objects.count()
        extra_context['total_courses'] = Course.objects.count()
        extra_context['total_lessons'] = Lesson.objects.count()
        extra_context['total_words'] = Word.objects.count()
        
        # Статистика за сегодня
        today = timezone.now().date()
        extra_context['new_users_today'] = User.objects.filter(date_joined__date=today).count()
        extra_context['completed_lessons_today'] = Progress.objects.filter(
            completed=True,
            completed_at__date=today
        ).count()
        
        # Активность
        last_week = timezone.now() - timedelta(days=7)
        extra_context['active_users_week'] = Progress.objects.filter(
            completed_at__gte=last_week
        ).values('user').distinct().count()
        
        # Топ-5 активных пользователей
        from django.db.models import Count
        extra_context['top_users'] = User.objects.annotate(
            completed_count=Count('progress', filter=models.Q(progress__completed=True))
        ).order_by('-completed_count')[:5]
        
        # Популярные курсы
        extra_context['popular_courses'] = Course.objects.annotate(
            student_count=Count('lessons__progress', distinct=True)
        ).order_by('-student_count')[:5]
        
        return super().index(request, extra_context)


# Перерегистрируем UserAdmin с кастомной админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Кастомизация админ-панели
admin.site.site_header = 'LangLearn - Панель управления'
admin.site.site_title = 'LangLearn Admin'
admin.site.index_title = 'Панель управления'