from django.urls import path, include
from . import views
from .views import (
    home, language_list, language_detail, lesson_detail,
    register, complete_lesson, test_detail, profile,
    dictionary, toggle_favorite_word, mark_word_learned,
    dashboard, change_password, test_result, course_detail,
    clear_dictionary_filter 
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
    admin_statistics, admin_audit_log
)

urlpatterns = [
    # Основные маршруты (публичные)
    path('', home, name='home'),
    path('languages/', language_list, name='language_list'),
    path('languages/<int:language_id>/', language_detail, name='language_detail'),
    
    # Пользовательские маршруты (требуют авторизации)
    path('dashboard/', dashboard, name='dashboard'),
    path('courses/<int:course_id>/', course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/complete/', complete_lesson, name='complete_lesson'),
    path('tests/<int:test_id>/', test_detail, name='test_detail'),
    path('tests/<int:test_id>/result/', test_result, name='test_result'),
    path('tests/<int:test_id>/result/<int:result_id>/', test_result, name='test_result_detail'),
    path('profile/', profile, name='profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('dictionary/', dictionary, name='dictionary'),
    path('dictionary/<int:word_id>/toggle-favorite/', toggle_favorite_word, name='toggle_favorite_word'),
    path('dictionary/<int:word_id>/mark-learned/', mark_word_learned, name='mark_word_learned'),
    
    # API endpoints
    path('api/user-stats/', views.api_user_stats, name='api_user_stats'),
    path('api/recent-progress/', views.api_recent_progress, name='api_recent_progress'),

    # Аутентификация
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', register, name='register'),
    
    # Восстановление пароля
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
    
    # ========== КАСТОМНАЯ АДМИН-ПАНЕЛЬ ==========
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
    path('cms/users/', admin_users, name='admin_users'),
    path('cms/users/<int:user_id>/toggle-active/', admin_user_toggle_active, name='admin_user_toggle_active'),
    
    # Статистика и аудит
    path('cms/statistics/', admin_statistics, name='admin_statistics'),
    path('cms/audit-log/', admin_audit_log, name='admin_audit_log'),

    path('dictionary/clear-filter/', clear_dictionary_filter, name='clear_dictionary_filter'),

    
]