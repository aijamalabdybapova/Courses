from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Language(models.Model):
    """Модель языка"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-language', blank=True)  # Добавьте если нет
    
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
    color = models.CharField(max_length=7, default='#4361ee')  # Цвет для карточки
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(blank=True)
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
    # Убираем поле level или делаем его вычисляемым
    level = models.PositiveIntegerField(default=1, editable=False)  # Только для чтения
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Автоматически пересчитываем уровень при сохранении
        self.level = self.xp // 100 + 1
        super().save(*args, **kwargs)
    
    @property
    def current_level(self):
        """Текущий уровень на основе XP"""
        return self.xp // 100 + 1
    
    @property
    def xp_in_current_level(self):
        """XP в текущем уровне"""
        return self.xp % 100
    
    @property
    def xp_for_next_level(self):
        """Сколько XP нужно для следующего уровня"""
        return (self.current_level + 1) * 100 - self.xp
    
    @property
    def level_progress_percentage(self):
        """Процент прогресса до следующего уровня"""
        return (self.xp_in_current_level / 100) * 100 if self.xp_in_current_level > 0 else 0
    
    @property
    def avatar_display(self):
        """Возвращает URL аватарки или дефолтную"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        elif self.avatar_url:
            return self.avatar_url
        return None


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
    score = models.IntegerField()  # Количество правильных ответов
    total = models.IntegerField()  # Всего вопросов
    percentage = models.FloatField(default=0)  # Процент правильных ответов
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Автоматически вычисляем процент при сохранении
        if self.total > 0:
            self.percentage = (self.score / self.total) * 100
        else:
            self.percentage = 0
        
        # Определяем, пройден ли тест (обычно 70%+)
        self.passed = self.percentage >= 70
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.test.title}: {self.percentage:.1f}%"