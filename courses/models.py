from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q  


class Language(models.Model):
    """Модель языка"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-language')
    
    def __str__(self):
        return self.name
    
    @property
    def total_lessons(self):
        return sum(course.lessons.count() for course in self.courses.all())
    
    @property
    def total_words(self):
        total = 0
        for course in self.courses.all():
            for lesson in course.lessons.all():
                total += lesson.words.count()
        return total


class Course(models.Model):
    """Модель курса (уровень языка)"""
    LEVEL_CHOICES = [
        ('A1', 'Начальный (A1)'),
        ('A2', 'Элементарный (A2)'),
        ('B1', 'Средний (B1)'),
        ('B2', 'Выше среднего (B2)'),
        ('C1', 'Продвинутый (C1)'),
        ('C2', 'В совершенстве (C2)'),
    ]
    
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    order = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=7, default='#4361ee')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['language', 'order']
        unique_together = ['language', 'level']
    
    def __str__(self):
        return f"{self.language.name} - {self.get_level_display()}"
    
    @property
    def total_words(self):
        total = 0
        for lesson in self.lessons.all():
            total += lesson.words.count()
        return total
    
    @property
    def difficulty_percentage(self):
        levels = {'A1': 20, 'A2': 40, 'B1': 60, 'B2': 80, 'C1': 90, 'C2': 100}
        return levels.get(self.level, 50)


class Lesson(models.Model):
    """Модель урока"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    estimated_time_minutes = models.PositiveIntegerField(default=15)
    
    class Meta:
        ordering = ['course', 'order']
    
    def __str__(self):
        return f"{self.course} - {self.title}"
    
    @property
    def next_lesson(self):
        return Lesson.objects.filter(
            course=self.course,
            order__gt=self.order
        ).order_by('order').first()
    
    @property
    def prev_lesson(self):
        return Lesson.objects.filter(
            course=self.course,
            order__lt=self.order
        ).order_by('-order').first()


class Word(models.Model):
    """Модель слова"""
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='words'
    )
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    transcription = models.CharField(max_length=100, blank=True)
    example = models.TextField(blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.word


class UserWord(models.Model):
    """Слова пользователя (для избранного и изучения)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    is_favorite = models.BooleanField(default=False)
    times_viewed = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(auto_now=True)
    learned = models.BooleanField(default=False)
    learned_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'word']
    
    def __str__(self):
        return f"{self.user.username} - {self.word.word}"


class Progress(models.Model):
    """Прогресс пользователя по урокам"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"
    
    class Meta:
        unique_together = ['user', 'lesson']
    
    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Профиль пользователя"""
    USER_ROLES = [
        ('student', 'Студент'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='student')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Аватар')
    avatar_url = models.URLField(blank=True, verbose_name='Ссылка на аватар')
    current_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    daily_goal_minutes = models.PositiveIntegerField(default=30)
    streak_days = models.PositiveIntegerField(default=0)
    total_study_time_minutes = models.PositiveIntegerField(default=0)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Профиль {self.user.username} ({self.get_role_display()})"
    
    @property
    def is_moderator(self):
        return self.role == 'moderator'
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.user.is_superuser
    
    @property
    def get_avatar_url(self):
        """Получить URL аватара"""
        if self.avatar:
            return self.avatar.url
        elif self.avatar_url:
            return self.avatar_url
        else:
            # Генерируем аватар на основе инициалов
            return f'https://ui-avatars.com/api/?background=4361ee&color=fff&name={self.user.username}'
    
    @property
    def can_access_admin_panel(self):
        """Только настоящие администраторы имеют доступ к админ-панели"""
        return self.is_admin or self.user.is_superuser


class ModeratorStudent(models.Model):
    """Связь модератора с учениками"""
    moderator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='my_students'
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='my_moderators'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Заметки модератора об ученике")
    
    class Meta:
        unique_together = ['moderator', 'student']
    
    def __str__(self):
        return f"{self.moderator.username} -> {self.student.username}"


class ModeratorNote(models.Model):
    """Заметки модератора о прогрессе ученика"""
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderator_notes')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Заметка от {self.moderator.username} для {self.student.username}"


class Test(models.Model):
    """Тест"""
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Question(models.Model):
    """Вопрос теста"""
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    """Ответ на вопрос"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class TestResult(models.Model):
    """Результат теста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Рассчитываем процент при сохранении
        self.percentage = (self.score / self.total * 100) if self.total > 0 else 0
        super().save(*args, **kwargs)

class LevelTest(models.Model):
    """Вступительный тест для определения уровня"""
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='level_tests')
    title = models.CharField(max_length=200, default="Определение уровня")
    description = models.TextField(blank=True)
    passing_score = models.IntegerField(default=70)
    
    def __str__(self):
        return f"Тест уровня: {self.language.name}"
    
    def get_questions_count(self):
        return self.questions.count()


class LevelTestQuestion(models.Model):
    """Вопросы для вступительного теста"""
    test = models.ForeignKey(LevelTest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class LevelTestAnswer(models.Model):
    """Ответы на вопросы вступительного теста"""
    question = models.ForeignKey(LevelTestQuestion, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    difficulty_level = models.CharField(max_length=2, blank=True, null=True)
    
    def __str__(self):
        return self.text


class UserLevelTestResult(models.Model):
    """Результаты вступительного теста пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    test = models.ForeignKey(LevelTest, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    recommended_level = models.CharField(max_length=2, default='A1')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.language.name}: {self.recommended_level} ({self.percentage:.0f}%)"

class ChatRoom(models.Model):
    """Модель чат-комнаты"""
    ROOM_TYPES = [
        ('moderator_student', 'Модератор-Студент'),
        ('admin_moderator', 'Админ-Модератор'),
        ('admin_student', 'Админ-Студент'),
    ]
    
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='moderator_student')
    moderator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='moderator_chats',
        null=True,
        blank=True
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_chats',
        null=True,
        blank=True
    )
    admin = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='admin_chats',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['moderator', 'student']
    
    def __str__(self):
        if self.room_type == 'moderator_student':
            return f"Чат: {self.moderator.username} ↔ {self.student.username}"
        elif self.room_type == 'admin_moderator':
            return f"Чат: {self.admin.username} ↔ {self.moderator.username}"
        else:
            return f"Чат: {self.admin.username} ↔ {self.student.username}"
    
    def get_other_user(self, current_user):
        """Получить собеседника"""
        if self.room_type == 'moderator_student':
            return self.student if current_user == self.moderator else self.moderator
        elif self.room_type == 'admin_moderator':
            return self.moderator if current_user == self.admin else self.admin
        else:
            return self.student if current_user == self.admin else self.admin
    
    def get_unread_count(self, user):
        """Получить количество непрочитанных сообщений"""
        other_user = self.get_other_user(user)
        return ChatMessage.objects.filter(
            room=self,
            receiver=user,
            sender=other_user,
            is_read=False
        ).count()
    
    def get_last_message(self):
        """Получить последнее сообщение в чате"""
        return ChatMessage.objects.filter(room=self).order_by('-created_at').first()
    
    def get_participants_info(self, current_user):
        """Получить информацию об участниках чата"""
        other_user = self.get_other_user(current_user)
        
        # Определяем роль собеседника
        try:
            other_profile = other_user.userprofile
            if other_profile.is_admin:
                role = "Админ"
                role_icon = ""
            elif other_profile.is_moderator:
                role = "Модератор"
                role_icon = ""
            else:
                role = "Ученик"
                role_icon = ""
        except:
            role = "Пользователь"
            role_icon = "👤"
        
        return {
            'user': other_user,
            'username': other_user.username,
            'role': role,
            'role_icon': role_icon,
            'avatar': other_user.username|first|upper
        }


class ChatMessage(models.Model):
    """Модель сообщения в чате"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.message[:50]}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()