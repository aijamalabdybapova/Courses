from django.urls import path, include
from django.shortcuts import redirect
from . import views
from .views import (
    home, language_list, language_detail, lesson_detail,
    register, complete_lesson, test_detail, profile,
    dictionary, toggle_favorite_word, mark_word_learned,
    dashboard, change_password, test_result, course_detail,
    clear_dictionary_filter,
    # Модераторские views
    moderator_dashboard, moderator_student_detail, moderator_add_note,
    moderator_delete_note, moderator_assign_student, moderator_remove_student, 
    chat_list, chat_detail, chat_create, chat_send_ajax, chat_get_messages_ajax, chat_unread_count_ajax,chat_user_list,
     # Тест уровня
    level_test_start, level_test_submit, level_test_skip, level_test_question, level_test_result  
)
from django.contrib.auth import views as auth_views
from .views import CustomLoginView
from .forms import CustomPasswordResetForm  

# Импортируем админские view
from .admin_views import (
    admin_dashboard, admin_languages, admin_language_create,
    admin_language_edit, admin_language_delete, admin_courses,
    admin_course_create, admin_course_edit, admin_course_delete,
    admin_lessons, admin_lesson_create, admin_lesson_edit,
    admin_lesson_delete, admin_words, admin_word_create,
    admin_word_edit, admin_word_delete, admin_tests,
    admin_test_create, admin_test_edit, admin_test_delete,
    admin_questions, admin_question_create, admin_question_edit,
    admin_question_delete, admin_users, admin_user_toggle_active,
    admin_statistics, admin_audit_log,
    admin_user_bulk_action, admin_user_reset_progress,
    admin_moderator_students, admin_moderator_add_student, admin_moderator_remove_student
)


def admin_redirect(request):
    """Перенаправление модераторов со стандартной админки"""
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.is_moderator:
                return redirect('moderator_dashboard')
        except:
            pass
    return redirect('home')


urlpatterns = [
    # ==================== ОСНОВНЫЕ МАРШРУТЫ (ПУБЛИЧНЫЕ) ====================
    path('', home, name='home'),
    path('languages/', language_list, name='language_list'),
    path('languages/<int:language_id>/', language_detail, name='language_detail'),
    
    # ==================== ПОЛЬЗОВАТЕЛЬСКИЕ МАРШРУТЫ (ТРЕБУЮТ АВТОРИЗАЦИИ) ====================
    path('dashboard/', dashboard, name='dashboard'),
    path('courses/<int:course_id>/', course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/complete/', complete_lesson, name='complete_lesson'),
    
    # Тесты
    path('tests/<int:test_id>/', test_detail, name='test_detail'),
    path('tests/<int:test_id>/result/', test_result, name='test_result'),
    path('tests/<int:test_id>/result/<int:result_id>/', test_result, name='test_result_detail'),
    
    # Профиль
    path('profile/', profile, name='profile'),
    path('profile/change-password/', change_password, name='change_password'),
    
    # Словарь
    path('dictionary/', dictionary, name='dictionary'),
    path('dictionary/<int:word_id>/toggle-favorite/', toggle_favorite_word, name='toggle_favorite_word'),
    path('dictionary/<int:word_id>/mark-learned/', mark_word_learned, name='mark_word_learned'),
    path('dictionary/clear-filter/', clear_dictionary_filter, name='clear_dictionary_filter'),
    
    # ==================== API ENDPOINTS ====================
    path('api/user-stats/', views.api_user_stats, name='api_user_stats'),
    path('api/recent-progress/', views.api_recent_progress, name='api_recent_progress'),
    
    # ==================== АУТЕНТИФИКАЦИЯ ====================
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', register, name='register'),
    
    # ==================== ПЕРЕНАПРАВЛЕНИЕ СТАНДАРТНОЙ АДМИНКИ ====================
    path('admin/', admin_redirect, name='admin_redirect'),
    path('admin/login/', admin_redirect),
    
    # ==================== ВОССТАНОВЛЕНИЕ ПАРОЛЯ ====================
    path('accounts/password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             form_class=CustomPasswordResetForm,
             email_template_name='registration/password_reset_email.html',
             html_email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/accounts/password_reset/done/'
         ), 
         name='password_reset'),
    path('accounts/password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/'
         ), 
         name='password_reset_confirm'),
    path('accounts/reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # ==================== ПАНЕЛЬ МОДЕРАТОРА ====================
    path('moderator/dashboard/', moderator_dashboard, name='moderator_dashboard'),
    path('moderator/student/<int:student_id>/', moderator_student_detail, name='moderator_student_detail'),
    path('moderator/student/<int:student_id>/add-note/', moderator_add_note, name='moderator_add_note'),
    path('moderator/delete-note/<int:note_id>/', moderator_delete_note, name='moderator_delete_note'),
    path('moderator/assign-student/', moderator_assign_student, name='moderator_assign_student'),
    path('moderator/remove-student/<int:relation_id>/', moderator_remove_student, name='moderator_remove_student'),
    
    # ==================== КАСТОМНАЯ АДМИН-ПАНЕЛЬ ====================
    path('cms/', admin_dashboard, name='admin_dashboard'),
    
    # Языки
    path('cms/languages/', admin_languages, name='admin_languages'),
    path('cms/languages/create/', admin_language_create, name='admin_language_create'),
    path('cms/languages/<int:pk>/edit/', admin_language_edit, name='admin_language_edit'),
    path('cms/languages/<int:pk>/delete/', admin_language_delete, name='admin_language_delete'),
    
    # Курсы
    path('cms/courses/', admin_courses, name='admin_courses'),
    path('cms/courses/create/', admin_course_create, name='admin_course_create'),
    path('cms/courses/<int:pk>/edit/', admin_course_edit, name='admin_course_edit'),
    path('cms/courses/<int:pk>/delete/', admin_course_delete, name='admin_course_delete'),
    
    # Уроки
    path('cms/lessons/', admin_lessons, name='admin_lessons'),
    path('cms/lessons/create/', admin_lesson_create, name='admin_lesson_create'),
    path('cms/lessons/<int:pk>/edit/', admin_lesson_edit, name='admin_lesson_edit'),
    path('cms/lessons/<int:pk>/delete/', admin_lesson_delete, name='admin_lesson_delete'),
    
    # Слова
    path('cms/words/', admin_words, name='admin_words'),
    path('cms/words/create/', admin_word_create, name='admin_word_create'),
    path('cms/words/<int:pk>/edit/', admin_word_edit, name='admin_word_edit'),
    path('cms/words/<int:pk>/delete/', admin_word_delete, name='admin_word_delete'),
    
    # Тесты и вопросы
    path('cms/tests/', admin_tests, name='admin_tests'),
    path('cms/tests/create/', admin_test_create, name='admin_test_create'),
    path('cms/tests/<int:pk>/edit/', admin_test_edit, name='admin_test_edit'),
    path('cms/tests/<int:pk>/delete/', admin_test_delete, name='admin_test_delete'),
    path('cms/tests/<int:test_id>/questions/', admin_questions, name='admin_questions'),
    path('cms/tests/<int:test_id>/questions/create/', admin_question_create, name='admin_question_create'),
    path('cms/questions/<int:pk>/edit/', admin_question_edit, name='admin_question_edit'),
    path('cms/questions/<int:pk>/delete/', admin_question_delete, name='admin_question_delete'),
    
    # Пользователи
    path('cms/users/bulk-action/', admin_user_bulk_action, name='admin_user_bulk_action'),
    path('cms/users/<int:user_id>/reset-progress/', admin_user_reset_progress, name='admin_user_reset_progress'),
    path('cms/users/', admin_users, name='admin_users'),
    path('cms/users/<int:user_id>/toggle-active/', admin_user_toggle_active, name='admin_user_toggle_active'),
    
    # Управление студентами модератора
    path('cms/users/moderator/<int:moderator_id>/students/', admin_moderator_students, name='admin_moderator_students'),
    path('cms/users/moderator/<int:moderator_id>/add-student/', admin_moderator_add_student, name='admin_moderator_add_student'),
    path('cms/users/moderator-students/<int:relation_id>/remove/', admin_moderator_remove_student, name='admin_moderator_remove_student'),
    
    # Статистика и аудит
    path('cms/statistics/', admin_statistics, name='admin_statistics'),
    path('cms/audit-log/', admin_audit_log, name='admin_audit_log'),
    
    # ==================== ЧАТ ====================
    path('chat/', chat_list, name='chat_list'),
    path('chat/<int:room_id>/', chat_detail, name='chat_detail'),
    path('chat/create/', chat_create, name='chat_create'),
    path('chat/send-ajax/', chat_send_ajax, name='chat_send_ajax'),
    path('chat/get-messages/<int:room_id>/', chat_get_messages_ajax, name='chat_get_messages_ajax'),
    path('chat/unread-count/', chat_unread_count_ajax, name='chat_unread_count_ajax'),
    path('chat/admin/', views.chat_admin, name='chat_admin'),
     path('level-test/<int:language_id>/', level_test_start, name='level_test_start'),
    path('level-test/<int:language_id>/submit/', level_test_submit, name='level_test_submit'),
    path('level-test/<int:language_id>/skip/', level_test_skip, name='level_test_skip'),
    path('level-test/<int:language_id>/question/', level_test_question, name='level_test_question'),
    path('level-test/<int:language_id>/result/<int:result_id>/', level_test_result, name='level_test_result'),
    path('chat/user-list/', chat_user_list, name='chat_user_list'),
]

