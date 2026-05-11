from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Language, Course, Lesson, Word, UserProfile, UserWord,
    Progress, Test, Question, Answer, TestResult,
    ModeratorStudent, ModeratorNote,
    LevelTest, LevelTestQuestion, LevelTestAnswer, UserLevelTestResult
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профили'
    fieldsets = (
        ('Основная информация', {
            'fields': ('role', 'bio', 'avatar_url', 'current_language')
        }),
        ('Статистика', {
            'fields': ('daily_goal_minutes', 'streak_days', 'total_study_time_minutes')
        }),
        ('Прогресс', {
            'fields': ('xp', 'level')
        }),
    )
    classes = ('wide',)


class ModeratorStudentInline(admin.TabularInline):
    """Inline для отображения учеников модератора"""
    model = ModeratorStudent
    fk_name = 'moderator'
    extra = 1
    raw_id_fields = ('student',)
    verbose_name = 'Ученик'
    verbose_name_plural = 'Ученики'
    fields = ('student', 'assigned_at', 'notes')
    readonly_fields = ('assigned_at',)


class ModeratorNoteInline(admin.TabularInline):
    """Inline для отображения заметок модератора"""
    model = ModeratorNote
    fk_name = 'moderator'
    extra = 1
    raw_id_fields = ('student',)
    verbose_name = 'Заметка'
    verbose_name_plural = 'Заметки'
    fields = ('student', 'note', 'created_at')
    readonly_fields = ('created_at',)


class StudentModeratorInline(admin.TabularInline):
    """Inline для отображения модераторов ученика"""
    model = ModeratorStudent
    fk_name = 'student'
    extra = 1
    raw_id_fields = ('moderator',)
    verbose_name = 'Модератор'
    verbose_name_plural = 'Модераторы'
    fields = ('moderator', 'assigned_at', 'notes')
    readonly_fields = ('assigned_at',)


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline, ModeratorStudentInline]
    list_display = ('username', 'email', 'role_display', 'students_count', 'is_active', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'userprofile__role')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    # ДОБАВЛЯЕМ ACTIONS
    actions = ['make_active', 'make_inactive', 'make_moderator', 'make_student', 'reset_user_progress']
    
    def role_display(self, obj):
        try:
            role = obj.userprofile.get_role_display()
            colors = {
                'admin': '#dc3545',
                'moderator': '#ff9e00',
                'student': '#28a745'
            }
            color = colors.get(obj.userprofile.role, '#6c757d')
            return format_html(
                '<span style="background: {}; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">{}</span>',
                color, role
            )
        except UserProfile.DoesNotExist:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.85rem;">Студент</span>'
            )
    role_display.short_description = 'Роль'
    
    def students_count(self, obj):
        try:
            if hasattr(obj, 'userprofile') and obj.userprofile.is_moderator:
                count = ModeratorStudent.objects.filter(moderator=obj).count()
                if count > 0:
                    return format_html(
                        '<span style="background: #17a2b8; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.85rem;">{} учеников</span>',
                        count
                    )
                return '0'
        except:
            pass
        return '-'
    students_count.short_description = 'Ученики'
    
    # ========== ДЕЙСТВИЯ ДЛЯ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ==========
    
    def make_active(self, request, queryset):
        """Активировать выбранных пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} пользователей активировано.')
    make_active.short_description = 'Активировать выбранных пользователей'
    
    def make_inactive(self, request, queryset):
        """Деактивировать (заблокировать) выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} пользователей деактивировано.')
    make_inactive.short_description = 'Деактивировать (заблокировать) выбранных пользователей'
    
    def make_moderator(self, request, queryset):
        """Назначить выбранных пользователей модераторами"""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'moderator':
                profile.role = 'moderator'
                profile.save()
                updated += 1
            # Даем права staff
            if not user.is_staff:
                user.is_staff = True
                user.save()
        self.message_user(request, f'{updated} пользователей назначены модераторами.')
    make_moderator.short_description = 'Назначить модераторами'
    
    def make_student(self, request, queryset):
        """Назначить выбранных пользователей студентами"""
        updated = 0
        for user in queryset:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'student':
                profile.role = 'student'
                profile.save()
                updated += 1
            # Убираем права staff если пользователь не суперпользователь
            if user.is_staff and not user.is_superuser:
                user.is_staff = False
                user.save()
        self.message_user(request, f'{updated} пользователей назначены студентами.')
    make_student.short_description = 'Назначить студентами'
    
    def reset_user_progress(self, request, queryset):
        """Сбросить прогресс выбранных пользователей"""
        updated = 0
        for user in queryset:
            # Сбрасываем прогресс уроков
            Progress.objects.filter(user=user).update(completed=False, completed_at=None)
            # Сбрасываем изученные слова
            UserWord.objects.filter(user=user).update(learned=False, learned_at=None)
            # Сбрасываем профиль
            try:
                profile = user.userprofile
                profile.xp = 0
                profile.level = 1
                profile.streak_days = 0
                profile.total_study_time_minutes = 0
                profile.save()
                updated += 1
            except UserProfile.DoesNotExist:
                pass
        self.message_user(request, f'Прогресс сброшен для {updated} пользователей.')
    reset_user_progress.short_description = 'Сбросить прогресс выбранных пользователей'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('userprofile')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Админка для языков"""
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
    """Админка для курсов"""
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
    """Админка для уроков"""
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
    """Админка для слов"""
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
    """Админка для слов пользователя"""
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
    """Админка для прогресса"""
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
    """Админка для тестов"""
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
    """Админка для вопросов"""
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
    """Админка для ответов"""
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
    """Админка для результатов тестов"""
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


@admin.register(ModeratorStudent)
class ModeratorStudentAdmin(admin.ModelAdmin):
    """Админка для связей модератор-ученик"""
    list_display = ('moderator_link', 'student_link', 'assigned_at_formatted', 'notes_preview')
    list_filter = ('assigned_at',)
    search_fields = ('moderator__username', 'student__username', 'notes')
    raw_id_fields = ('moderator', 'student')
    list_per_page = 20
    date_hierarchy = 'assigned_at'
    
    def moderator_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.moderator.id])
        role = ''
        if hasattr(obj.moderator, 'userprofile'):
            role = f' ({obj.moderator.userprofile.get_role_display()})'
        return format_html('<a href="{}"><strong>{}</strong>{}</a>', url, obj.moderator.username, role)
    moderator_link.short_description = 'Модератор'
    
    def student_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Ученик'
    
    def assigned_at_formatted(self, obj):
        return obj.assigned_at.strftime('%d.%m.%Y %H:%M')
    assigned_at_formatted.short_description = 'Дата назначения'
    
    def notes_preview(self, obj):
        if obj.notes:
            preview = obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
            return format_html(
                '<span title="{}"><i class="fas fa-sticky-note"></i> {}</span>',
                obj.notes, preview
            )
        return '-'
    notes_preview.short_description = 'Заметки'
    
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        """Экспорт связей в CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="moderator_students.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Модератор', 'Ученик', 'Дата назначения', 'Заметки'])
        
        for obj in queryset:
            writer.writerow([
                obj.moderator.username,
                obj.student.username,
                obj.assigned_at.strftime('%Y-%m-%d %H:%M'),
                obj.notes
            ])
        
        return response
    export_as_csv.short_description = 'Экспортировать выбранные в CSV'


@admin.register(ModeratorNote)
class ModeratorNoteAdmin(admin.ModelAdmin):
    """Админка для заметок модераторов"""
    list_display = ('moderator_link', 'student_link', 'note_preview', 'created_at_formatted')
    list_filter = ('created_at',)
    search_fields = ('moderator__username', 'student__username', 'note')
    raw_id_fields = ('moderator', 'student')
    list_per_page = 20
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def moderator_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.moderator.id])
        return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.moderator.username)
    moderator_link.short_description = 'Модератор'
    
    def student_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Ученик'
    
    def note_preview(self, obj):
        preview = obj.note[:80] + '...' if len(obj.note) > 80 else obj.note
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    note_preview.short_description = 'Заметка'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_formatted.short_description = 'Дата создания'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Расширенная админка для профилей пользователей"""
    list_display = ('user_link', 'role_badge', 'level_badge', 'xp', 'streak_days', 'daily_goal', 'students_assigned', 'last_active')
    list_filter = ('role', 'level', 'current_language')
    search_fields = ('user__username', 'user__email', 'bio')
    raw_id_fields = ('user', 'current_language')
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'role', 'bio', 'avatar_url', 'current_language')
        }),
        ('Статистика обучения', {
            'fields': ('daily_goal_minutes', 'streak_days', 'total_study_time_minutes', 'xp', 'level')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}"><strong>{}</strong></a><br><small style="color: #6c757d;">{}</small>', 
                          url, obj.user.username, obj.user.email)
    user_link.short_description = 'Пользователь'
    
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',
            'moderator': '#ff9e00',
            'student': '#28a745'
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Роль'
    
    def level_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600;">Ур. {}</span>',
            obj.level
        )
    level_badge.short_description = 'Уровень'
    
    def students_assigned(self, obj):
        """Количество учеников, назначенных модератору"""
        if obj.role == 'moderator':
            count = ModeratorStudent.objects.filter(moderator=obj.user).count()
            if count > 0:
                url = reverse('admin:courses_moderatorstudent_changelist') + f'?moderator__id__exact={obj.user.id}'
                return format_html('<a href="{}">{} учеников</a>', url, count)
            return '0'
        return '-'
    students_assigned.short_description = 'Назначено учеников'
    
    def daily_goal(self, obj):
        return f'{obj.daily_goal_minutes} мин'
    daily_goal.short_description = 'Дневная цель'
    
    def last_active(self, obj):
        progress = Progress.objects.filter(user=obj.user, completed=True).order_by('-completed_at').first()
        if progress and progress.completed_at:
            return progress.completed_at.strftime('%d.%m.%Y %H:%M')
        return 'Нет активности'
    last_active.short_description = 'Последняя активность'
    
    actions = ['make_moderator', 'make_admin', 'reset_progress']
    
    def make_moderator(self, request, queryset):
        """Сделать выбранных пользователей модераторами"""
        updated = queryset.update(role='moderator')
        for profile in queryset:
            profile.user.is_staff = True
            profile.user.save()
        self.message_user(request, f'{updated} пользователей назначены модераторами.')
    make_moderator.short_description = 'Назначить модераторами'
    
    def make_admin(self, request, queryset):
        """Сделать выбранных пользователей администраторами"""
        updated = queryset.update(role='admin')
        for profile in queryset:
            profile.user.is_staff = True
            profile.user.is_superuser = True
            profile.user.save()
        self.message_user(request, f'{updated} пользователей назначены администраторами.')
    make_admin.short_description = 'Назначить администраторами'
    
    def reset_progress(self, request, queryset):
        """Сбросить прогресс выбранных пользователей"""
        for profile in queryset:
            profile.xp = 0
            profile.level = 1
            profile.streak_days = 0
            profile.total_study_time_minutes = 0
            profile.save()
            Progress.objects.filter(user=profile.user).update(completed=False, completed_at=None)
            UserWord.objects.filter(user=profile.user).update(learned=False, learned_at=None)
        self.message_user(request, f'Прогресс сброшен для {queryset.count()} пользователей.')
    reset_progress.short_description = 'Сбросить прогресс'
# Добавьте в courses/admin.py после существующих админок

# ========== АДМИНКИ ДЛЯ ТЕСТОВ УРОВНЯ ==========

@admin.register(LevelTest)
class LevelTestAdmin(admin.ModelAdmin):
    """Админка для тестов уровня"""
    list_display = ('title', 'language', 'get_questions_count', 'passing_score')
    list_filter = ('language',)
    search_fields = ('title', 'language__name')
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    get_questions_count.short_description = 'Вопросов'


@admin.register(LevelTestQuestion)
class LevelTestQuestionAdmin(admin.ModelAdmin):
    """Админка для вопросов теста уровня"""
    list_display = ('text_short', 'test', 'order', 'answers_count')
    list_filter = ('test__language', 'test')
    search_fields = ('text',)
    list_editable = ('order',)
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Вопрос'
    
    def answers_count(self, obj):
        return obj.answers.count()
    answers_count.short_description = 'Ответов'


class LevelTestAnswerInline(admin.TabularInline):
    """Inline для ответов"""
    model = LevelTestAnswer
    extra = 4
    fields = ('text', 'is_correct', 'difficulty_level')


@admin.register(LevelTestAnswer)
class LevelTestAnswerAdmin(admin.ModelAdmin):
    """Админка для ответов"""
    list_display = ('text_short', 'question', 'is_correct', 'difficulty_level')
    list_filter = ('is_correct', 'difficulty_level')
    search_fields = ('text', 'question__text')
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Ответ'


@admin.register(UserLevelTestResult)
class UserLevelTestResultAdmin(admin.ModelAdmin):
    """Админка для результатов тестов"""
    list_display = ('user', 'language', 'score', 'total', 'percentage', 'recommended_level', 'created_at')
    list_filter = ('recommended_level', 'language', 'created_at')
    search_fields = ('user__username', 'language__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

# Перерегистрируем UserAdmin с кастомной админкой
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Кастомизация админ-панели
admin.site.site_header = 'LangLearn - Панель управления'
admin.site.site_title = 'LangLearn Admin'
admin.site.index_title = 'Панель управления'