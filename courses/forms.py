from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError

from .models import (
    UserProfile, Language, Word, UserWord,
    Course, Lesson, Test, Question, Answer, ChatMessage
)


# ========== ФОРМЫ ДЛЯ АУТЕНТИФИКАЦИИ И РЕГИСТРАЦИИ ==========

class RegisterForm(forms.ModelForm):
    """Форма регистрации нового пользователя"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Подтверждение пароля'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label='Имя'
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label='Фамилия'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        
        return cleaned_data


class CustomAuthenticationForm(AuthenticationForm):
    """Кастомная форма для входа в систему"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Имя пользователя или Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Кастомная форма для сброса пароля с проверкой существования email"""
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'auth-form-control-fullscreen',
            'placeholder': 'Введите ваш email',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        """Проверка существования email в базе"""
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError(
                'Пользователь с таким email не найден. Проверьте правильность ввода или зарегистрируйтесь.'
            )
        return email
    
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """Отправка письма с красивым HTML шаблоном"""
        context.update({
            'protocol': 'http' if context.get('protocol') == 'http' else 'https',
        })
        super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name
        )


# ========== ФОРМЫ ДЛЯ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ ==========

class UserUpdateForm(forms.ModelForm):
    """Форма для обновления данных пользователя"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
    
    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        username = self.instance.username
        
        if email and User.objects.exclude(username=username).filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        
        return email


class ProfileUpdateForm(forms.ModelForm):
    """Форма для обновления профиля пользователя"""
    class Meta:
        model = UserProfile
        fields = ['bio', 'current_language', 'daily_goal_minutes', 'avatar', 'avatar_url']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Расскажите о себе...'}),
            'current_language': forms.Select(attrs={'class': 'form-control'}),
            'daily_goal_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 480}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'avatar_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/avatar.jpg'}),
        }
        labels = {
            'bio': 'О себе',
            'current_language': 'Изучаемый язык',
            'daily_goal_minutes': 'Ежедневная цель (минуты)',
            'avatar': 'Загрузить аватар',
            'avatar_url': 'Или ссылка на аватар',
        }
        help_texts = {
            'avatar': 'Поддерживаются форматы: JPG, PNG, GIF. Максимальный размер: 5MB',
            'avatar_url': 'Укажите прямую ссылку на изображение',
        }


# ========== ФОРМЫ ДЛЯ СЛОВАРЯ ==========

class WordForm(forms.ModelForm):
    """Форма для создания/редактирования слова"""
    class Meta:
        model = Word
        fields = ['lesson', 'word', 'translation', 'transcription', 'example', 'part_of_speech']
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-control'}),
            'word': forms.TextInput(attrs={'class': 'form-control'}),
            'translation': forms.TextInput(attrs={'class': 'form-control'}),
            'transcription': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '[wɜːd]'}),
            'example': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'part_of_speech': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'noun, verb, adj...'}),
        }


class SearchForm(forms.Form):
    """Форма поиска и фильтрации в словаре"""
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по словарю...'
        })
    )
    language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# ========== ФОРМЫ ДЛЯ АДМИН-ПАНЕЛИ ==========

class LanguageForm(forms.ModelForm):
    """Форма для создания/редактирования языка"""
    class Meta:
        model = Language
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-language'
            }),
        }
        labels = {
            'name': 'Название языка',
            'description': 'Описание',
            'icon': 'Иконка (FontAwesome класс)',
        }


class CourseForm(forms.ModelForm):
    """Форма для создания/редактирования курса"""
    class Meta:
        model = Course
        fields = ['language', 'title', 'description', 'level', 'order', 'color', 'is_active']
        widgets = {
            'language': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'language': 'Язык',
            'title': 'Название курса',
            'description': 'Описание',
            'level': 'Уровень',
            'order': 'Порядок отображения',
            'color': 'Цвет карточки',
            'is_active': 'Активен',
        }


class LessonForm(forms.ModelForm):
    """Форма для создания/редактирования урока"""
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'order', 'estimated_time_minutes']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'estimated_time_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'course': 'Курс',
            'title': 'Название урока',
            'content': 'Содержание (HTML)',
            'order': 'Порядок',
            'estimated_time_minutes': 'Время изучения (мин)',
        }


class TestForm(forms.ModelForm):
    """Форма для создания/редактирования теста"""
    class Meta:
        model = Test
        fields = ['lesson', 'title']
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'lesson': 'Урок',
            'title': 'Название теста',
        }


class QuestionForm(forms.ModelForm):
    """Форма для создания/редактирования вопроса"""
    class Meta:
        model = Question
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вопрос...'}),
        }
        labels = {
            'text': 'Текст вопроса',
        }


class AnswerForm(forms.ModelForm):
    """Форма для создания/редактирования ответа"""
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'text': 'Текст ответа',
            'is_correct': 'Правильный ответ',
        }


# ========== ФОРМА ДЛЯ НАСТРОЕК ПОЛЬЗОВАТЕЛЯ ==========

class UserSettingsForm(forms.Form):
    """Форма для настроек пользователя (тема, уведомления и т.д.)"""
    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Темная'),
    ]
    
    theme = forms.ChoiceField(
        choices=THEME_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Тема оформления'
    )
    
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Получать уведомления на email'
    )


# ========== ФОРМА ДЛЯ ЧАТА ==========
# ========== ФОРМЫ ДЛЯ ТЕСТА УРОВНЯ ==========

class LevelTestForm(forms.Form):
    """Форма для вступительного теста"""
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                choices=[(ans.id, ans.text) for ans in question.answers.all()],
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                label=question.text,
                required=True
            )
class ChatMessageForm(forms.ModelForm):
    """Форма для отправки сообщения в чате"""
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите сообщение...',
                'style': 'resize: none;'
            })
        }
        labels = {
            'message': ''
        }