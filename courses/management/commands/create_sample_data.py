# courses/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import (
    Language, Course, Lesson, Word, Test, Question, Answer,
    LevelTest, LevelTestQuestion, LevelTestAnswer, UserLevelTestResult,
    Progress, UserWord, UserProfile, TestResult,
    ModeratorStudent, ModeratorNote, ChatRoom, ChatMessage
)
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Создаёт корректные данные для языковых курсов'

    def handle(self, *args, **kwargs):
        self.stdout.write('=' * 60)
        self.stdout.write('СОЗДАНИЕ ДАННЫХ ДЛЯ ПЛАТФОРМЫ LANGLEARN')
        self.stdout.write('=' * 60)
        
        self.clear_old_data()
        languages = self.create_languages()
        total_lessons, total_words, total_tests = self.create_all_courses_and_content(languages)
        self.create_level_tests_for_all_languages()
        self.print_statistics(total_lessons, total_words, total_tests)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('ВСЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def clear_old_data(self):
        """Очищает старые данные перед созданием новых"""
        self.stdout.write('\nОЧИСТКА СТАРЫХ ДАННЫХ...')
        
        models_to_delete = [
            TestResult, UserLevelTestResult,
            ModeratorNote, ModeratorStudent,
            ChatMessage, ChatRoom,
            LevelTestAnswer, LevelTestQuestion, LevelTest,
            Answer, Question, Test,
            UserWord, Progress,
            Word, Lesson, Course, Language,
        ]
        
        for model in models_to_delete:
            try:
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    self.stdout.write(f'  - Удалено {count} записей {model.__name__}')
            except Exception:
                pass
        
        self.stdout.write('  ОЧИСТКА ЗАВЕРШЕНА!\n')

    def create_languages(self):
        """Создаёт 6 языков"""
        self.stdout.write('СОЗДАНИЕ ЯЗЫКОВ...')
        
        languages_data = [
            {'name': 'Английский', 'desc': 'Самый распространённый язык в мире, язык международного общения.', 'icon': 'fas fa-flag-usa'},
            {'name': 'Испанский', 'desc': 'Второй по распространённости родной язык в мире.', 'icon': 'fas fa-sun'},
            {'name': 'Французский', 'desc': 'Язык любви, искусства и дипломатии.', 'icon': 'fas fa-flag'},
            {'name': 'Немецкий', 'desc': 'Самый распространённый язык в Европе.', 'icon': 'fas fa-landmark'},
            {'name': 'Итальянский', 'desc': 'Язык искусства, музыки и кулинарии.', 'icon': 'fas fa-pizza-slice'},
            {'name': 'Японский', 'desc': 'Уникальный язык с тремя системами письма.', 'icon': 'fas fa-torii-gate'},
        ]

        languages = []
        for lang_data in languages_data:
            language = Language.objects.create(
                name=lang_data['name'],
                description=lang_data['desc'],
                icon=lang_data['icon']
            )
            languages.append(language)
            self.stdout.write(f'  - Создан язык: {language.name}')
        
        self.stdout.write('  ЯЗЫКИ СОЗДАНЫ!\n')
        return languages

    def create_courses_for_language(self, language):
        """Создаёт 5 курсов (уровней) для языка"""
        levels = [
            {'code': 'A1', 'title': 'Начинающий', 'desc': 'Изучите базовые слова и простые фразы.'},
            {'code': 'A2', 'title': 'Элементарный', 'desc': 'Расширьте словарный запас, научитесь говорить о себе.'},
            {'code': 'B1', 'title': 'Средний', 'desc': 'Уверенно общайтесь на повседневные темы.'},
            {'code': 'B2', 'title': 'Выше среднего', 'desc': 'Свободно говорите на любые темы.'},
            {'code': 'C1', 'title': 'Продвинутый', 'desc': 'В совершенстве владейте языком.'},
        ]

        courses = []
        for i, level_data in enumerate(levels):
            course = Course.objects.create(
                language=language,
                title=f'{language.name} - {level_data["title"]}',
                description=level_data['desc'],
                level=level_data['code'],
                order=i + 1,
                is_active=True,
                color=self.get_course_color(level_data['code'])
            )
            courses.append(course)
        return courses

    def get_course_color(self, level):
        colors = {'A1': '#28a745', 'A2': '#20c997', 'B1': '#17a2b8', 'B2': '#007bff', 'C1': '#6f42c1'}
        return colors.get(level, '#4361ee')

    def create_all_courses_and_content(self, languages):
        """Создаёт все курсы, уроки и тесты для каждого языка"""
        self.stdout.write('СОЗДАНИЕ КУРСОВ И УРОКОВ...')

        total_lessons = 0
        total_words = 0
        total_tests = 0

        for language in languages:
            self.stdout.write(f'\n{"="*50}')
            self.stdout.write(f'  Язык: {language.name}')
            self.stdout.write(f'{"="*50}')
            
            courses = self.create_courses_for_language(language)

            for course in courses:
                self.stdout.write(f'\n  Курс: {course.title}')
                lessons = self.create_lessons_for_course(course)
                total_lessons += len(lessons)

                for lesson in lessons:
                    words_count = lesson.words.count()
                    total_words += words_count
                    self.stdout.write(f'      Урок: {lesson.title} - {words_count} слов')

                for lesson in lessons:
                    self.create_test_for_lesson(lesson)
                    total_tests += 1
                self.stdout.write(f'      Тестов создано: {len(lessons)}')

        return total_lessons, total_words, total_tests

    def create_lessons_for_course(self, course):
        """Создаёт уроки для курса"""
        language_name = course.language.name
        level = course.level

        lessons_data = {
            'A1': [
                ('Урок 1: Приветствия', self.get_greeting_lesson(language_name)),
                ('Урок 2: Семья', self.get_family_lesson(language_name)),
                ('Урок 3: Числа', self.get_numbers_lesson(language_name)),
                ('Урок 4: Цвета', self.get_colors_lesson(language_name)),
                ('Урок 5: Еда', self.get_food_lesson(language_name)),
            ],
            'A2': [
                ('Урок 1: Профессии', self.get_jobs_lesson(language_name)),
                ('Урок 2: Мой день', self.get_routine_lesson(language_name)),
                ('Урок 3: Хобби', self.get_hobbies_lesson(language_name)),
                ('Урок 4: Покупки', self.get_shopping_lesson(language_name)),
                ('Урок 5: Погода', self.get_weather_lesson(language_name)),
            ],
            'B1': [
                ('Урок 1: Путешествия', self.get_travel_lesson(language_name)),
                ('Урок 2: Здоровье', self.get_health_lesson(language_name)),
                ('Урок 3: Образование', self.get_education_lesson(language_name)),
                ('Урок 4: Технологии', self.get_tech_lesson(language_name)),
                ('Урок 5: Экология', self.get_environment_lesson(language_name)),
            ],
            'B2': [
                ('Урок 1: Бизнес', self.get_business_lesson(language_name)),
                ('Урок 2: СМИ', self.get_media_lesson(language_name)),
                ('Урок 3: Искусство', self.get_art_lesson(language_name)),
                ('Урок 4: Наука', self.get_science_lesson(language_name)),
                ('Урок 5: Политика', self.get_politics_lesson(language_name)),
            ],
            'C1': [
                ('Урок 1: Академическое письмо', '<h1>Академическое письмо</h1><p>Структура эссе, аргументация</p>'),
                ('Урок 2: Идиомы', '<h1>Идиомы</h1><p>Устойчивые выражения в языке</p>'),
                ('Урок 3: Деловая переписка', '<h1>Деловая переписка</h1><p>Правила formal writing</p>'),
                ('Урок 4: Литература', '<h1>Литература</h1><p>Анализ текстов</p>'),
                ('Урок 5: Дебаты', '<h1>Дебаты</h1><p>Искусство убеждения</p>'),
            ],
        }

        topics = lessons_data.get(level, lessons_data['A1'])
        
        lessons = []
        for i, (title, get_content_func) in enumerate(topics[:5]):
            lesson = Lesson.objects.create(
                course=course,
                title=title,
                content=get_content_func,
                order=i + 1,
                estimated_time_minutes=45
            )
            
            words = self.get_words_for_lesson(language_name, level, i + 1)
            for word_data in words:
                Word.objects.create(
                    lesson=lesson,
                    word=word_data['word'],
                    translation=word_data['translation'],
                    example=word_data.get('example', ''),
                    part_of_speech=word_data.get('part_of_speech', '')
                )
            lessons.append(lesson)
        
        return lessons

    # ==================== УРОКИ ====================
    
    def get_lang_words(self, lang):
        """Возвращает словарь слов на изучаемом языке"""
        words = {
            'Английский': {
                'hello': 'Hello', 'good_morning': 'Good morning', 'goodbye': 'Goodbye',
                'thank_you': 'Thank you', 'please': 'Please', 'sorry': 'Sorry',
                'mother': 'Mother', 'father': 'Father', 'brother': 'Brother', 'sister': 'Sister',
                'one': 'One', 'two': 'Two', 'three': 'Three',
                'red': 'Red', 'blue': 'Blue', 'green': 'Green',
                'bread': 'Bread', 'water': 'Water', 'coffee': 'Coffee', 'restaurant': 'Restaurant',
                'teacher': 'Teacher', 'doctor': 'Doctor', 'wake_up': 'Wake up',
                'breakfast': 'Breakfast', 'work': 'Work', 'hobby': 'Hobby',
                'read': 'Read', 'music': 'Music', 'shop': 'Shop',
                'price': 'Price', 'money': 'Money', 'sunny': 'Sunny', 'rain': 'Rain',
                'airport': 'Airport', 'passport': 'Passport', 'hotel': 'Hotel',
                'health': 'Health', 'exercise': 'Exercise', 'school': 'School',
                'computer': 'Computer', 'internet': 'Internet', 'environment': 'Environment',
                'business': 'Business', 'contract': 'Contract', 'media': 'Media',
                'art': 'Art', 'science': 'Science', 'politics': 'Politics'
            },
            'Испанский': {
                'hello': 'Hola', 'good_morning': 'Buenos días', 'goodbye': 'Adiós',
                'thank_you': 'Gracias', 'please': 'Por favor', 'sorry': 'Lo siento',
                'mother': 'Madre', 'father': 'Padre', 'brother': 'Hermano', 'sister': 'Hermana',
                'one': 'Uno', 'two': 'Dos', 'three': 'Tres',
                'red': 'Rojo', 'blue': 'Azul', 'green': 'Verde',
                'bread': 'Pan', 'water': 'Agua', 'coffee': 'Café', 'restaurant': 'Restaurante',
                'teacher': 'Profesor', 'doctor': 'Médico', 'wake_up': 'Despertarse',
                'breakfast': 'Desayuno', 'work': 'Trabajo', 'hobby': 'Pasatiempo',
                'read': 'Leer', 'music': 'Música', 'shop': 'Tienda',
                'price': 'Precio', 'money': 'Dinero', 'sunny': 'Soleado', 'rain': 'Lluvia',
                'airport': 'Aeropuerto', 'passport': 'Pasaporte', 'hotel': 'Hotel',
                'health': 'Salud', 'exercise': 'Ejercicio', 'school': 'Escuela',
                'computer': 'Ordenador', 'internet': 'Internet', 'environment': 'Medio ambiente',
                'business': 'Negocio', 'contract': 'Contrato', 'media': 'Medios',
                'art': 'Arte', 'science': 'Ciencia', 'politics': 'Política'
            },
            'Французский': {
                'hello': 'Bonjour', 'good_morning': 'Bonjour', 'goodbye': 'Au revoir',
                'thank_you': 'Merci', 'please': "S'il vous plaît", 'sorry': 'Désolé',
                'mother': 'Mère', 'father': 'Père', 'brother': 'Frère', 'sister': 'Soeur',
                'one': 'Un', 'two': 'Deux', 'three': 'Trois',
                'red': 'Rouge', 'blue': 'Bleu', 'green': 'Vert',
                'bread': 'Pain', 'water': 'Eau', 'coffee': 'Café', 'restaurant': 'Restaurant',
                'teacher': 'Professeur', 'doctor': 'Médecin', 'wake_up': 'Se réveiller',
                'breakfast': 'Petit-déjeuner', 'work': 'Travail', 'hobby': 'Loisir',
                'read': 'Lire', 'music': 'Musique', 'shop': 'Magasin',
                'price': 'Prix', 'money': 'Argent', 'sunny': 'Ensoleillé', 'rain': 'Pluie',
                'airport': 'Aéroport', 'passport': 'Passeport', 'hotel': 'Hôtel',
                'health': 'Santé', 'exercise': 'Exercice', 'school': 'École',
                'computer': 'Ordinateur', 'internet': 'Internet', 'environment': 'Environnement',
                'business': 'Affaires', 'contract': 'Contrat', 'media': 'Médias',
                'art': 'Art', 'science': 'Science', 'politics': 'Politique'
            },
            'Немецкий': {
                'hello': 'Hallo', 'good_morning': 'Guten Morgen', 'goodbye': 'Auf Wiedersehen',
                'thank_you': 'Danke', 'please': 'Bitte', 'sorry': 'Entschuldigung',
                'mother': 'Mutter', 'father': 'Vater', 'brother': 'Bruder', 'sister': 'Schwester',
                'one': 'Eins', 'two': 'Zwei', 'three': 'Drei',
                'red': 'Rot', 'blue': 'Blau', 'green': 'Grün',
                'bread': 'Brot', 'water': 'Wasser', 'coffee': 'Kaffee', 'restaurant': 'Restaurant',
                'teacher': 'Lehrer', 'doctor': 'Arzt', 'wake_up': 'Aufwachen',
                'breakfast': 'Frühstück', 'work': 'Arbeit', 'hobby': 'Hobby',
                'read': 'Lesen', 'music': 'Musik', 'shop': 'Geschäft',
                'price': 'Preis', 'money': 'Geld', 'sunny': 'Sonnig', 'rain': 'Regen',
                'airport': 'Flughafen', 'passport': 'Reisepass', 'hotel': 'Hotel',
                'health': 'Gesundheit', 'exercise': 'Übung', 'school': 'Schule',
                'computer': 'Computer', 'internet': 'Internet', 'environment': 'Umwelt',
                'business': 'Geschäft', 'contract': 'Vertrag', 'media': 'Medien',
                'art': 'Kunst', 'science': 'Wissenschaft', 'politics': 'Politik'
            },
            'Итальянский': {
                'hello': 'Ciao', 'good_morning': 'Buongiorno', 'goodbye': 'Arrivederci',
                'thank_you': 'Grazie', 'please': 'Per favore', 'sorry': 'Scusa',
                'mother': 'Madre', 'father': 'Padre', 'brother': 'Fratello', 'sister': 'Sorella',
                'one': 'Uno', 'two': 'Due', 'three': 'Tre',
                'red': 'Rosso', 'blue': 'Blu', 'green': 'Verde',
                'bread': 'Pane', 'water': 'Acqua', 'coffee': 'Caffè', 'restaurant': 'Ristorante',
                'teacher': 'Insegnante', 'doctor': 'Medico', 'wake_up': 'Svegliarsi',
                'breakfast': 'Colazione', 'work': 'Lavoro', 'hobby': 'Passatempo',
                'read': 'Leggere', 'music': 'Musica', 'shop': 'Negozio',
                'price': 'Prezzo', 'money': 'Denaro', 'sunny': 'Soleggiato', 'rain': 'Pioggia',
                'airport': 'Aeroporto', 'passport': 'Passaporto', 'hotel': 'Hotel',
                'health': 'Salute', 'exercise': 'Esercizio', 'school': 'Scuola',
                'computer': 'Computer', 'internet': 'Internet', 'environment': 'Ambiente',
                'business': 'Affari', 'contract': 'Contratto', 'media': 'Media',
                'art': 'Arte', 'science': 'Scienza', 'politics': 'Politica'
            },
            'Японский': {
                'hello': 'こんにちは', 'good_morning': 'おはようございます', 'goodbye': 'さようなら',
                'thank_you': 'ありがとう', 'please': 'お願いします', 'sorry': 'すみません',
                'mother': '母', 'father': '父', 'brother': '兄弟', 'sister': '姉妹',
                'one': '一', 'two': '二', 'three': '三',
                'red': '赤', 'blue': '青', 'green': '緑',
                'bread': 'パン', 'water': '水', 'coffee': 'コーヒー', 'restaurant': 'レストラン',
                'teacher': '先生', 'doctor': '医者', 'wake_up': '起きる',
                'breakfast': '朝ごはん', 'work': '仕事', 'hobby': '趣味',
                'read': '読む', 'music': '音楽', 'shop': '店',
                'price': '値段', 'money': 'お金', 'sunny': '晴れ', 'rain': '雨',
                'airport': '空港', 'passport': 'パスポート', 'hotel': 'ホテル',
                'health': '健康', 'exercise': '運動', 'school': '学校',
                'computer': 'コンピュータ', 'internet': 'インターネット', 'environment': '環境',
                'business': 'ビジネス', 'contract': '契約', 'media': 'メディア',
                'art': '芸術', 'science': '科学', 'politics': '政治'
            }
        }
        return words.get(lang, words['Английский'])

    def get_greeting_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'''<h1>Урок 1: Приветствия</h1>

<h2>Изучаемые слова:</h2>
<p><strong>{w['hello']}</strong> - привет / здравствуйте</p>
<p><strong>{w['good_morning']}</strong> - доброе утро</p>
<p><strong>{w['goodbye']}</strong> - до свидания</p>
<p><strong>{w['thank_you']}</strong> - спасибо</p>
<p><strong>{w['please']}</strong> - пожалуйста</p>

<h2>Пример диалога:</h2>
<p><strong>- {w['hello']}! Как дела?</strong></p>
<p><strong>- {w['hello']}! Хорошо, {w['thank_you']}. А у тебя?</strong></p>
<p><strong>- Тоже хорошо. {w['goodbye']}!</strong></p>
<p><strong>- {w['goodbye']}!</strong></p>'''

    def get_family_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'''<h1>Урок 2: Семья</h1>

<h2>Изучаемые слова:</h2>
<p><strong>{w['mother']}</strong> - мама</p>
<p><strong>{w['father']}</strong> - папа</p>
<p><strong>{w['brother']}</strong> - брат</p>
<p><strong>{w['sister']}</strong> - сестра</p>

<h2>Пример:</h2>
<p>Моя {w['mother']} - учительница. Мой {w['father']} - врач. У меня есть {w['brother']} и {w['sister']}.</p>'''

    def get_numbers_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'''<h1>Урок 3: Числа</h1>

<h2>Изучаемые слова:</h2>
<p><strong>{w['one']}</strong> - один</p>
<p><strong>{w['two']}</strong> - два</p>
<p><strong>{w['three']}</strong> - три</p>'''

    def get_colors_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'''<h1>Урок 4: Цвета</h1>

<h2>Изучаемые слова:</h2>
<p><strong>{w['red']}</strong> - красный</p>
<p><strong>{w['blue']}</strong> - синий</p>
<p><strong>{w['green']}</strong> - зелёный</p>'''

    def get_food_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'''<h1>Урок 5: Еда</h1>

<h2>Изучаемые слова:</h2>
<p><strong>{w['bread']}</strong> - хлеб</p>
<p><strong>{w['water']}</strong> - вода</p>
<p><strong>{w['coffee']}</strong> - кофе</p>
<p><strong>{w['restaurant']}</strong> - ресторан</p>'''

    def get_jobs_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Профессии</h1><p><strong>{w["teacher"]}</strong> - учитель<br><strong>{w["doctor"]}</strong> - врач</p>'
    
    def get_routine_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Мой день</h1><p><strong>{w["wake_up"]}</strong> - просыпаться<br><strong>{w["breakfast"]}</strong> - завтрак<br><strong>{w["work"]}</strong> - работа</p>'
    
    def get_hobbies_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Хобби</h1><p><strong>{w["hobby"]}</strong> - хобби<br><strong>{w["music"]}</strong> - музыка</p>'
    
    def get_shopping_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Покупки</h1><p><strong>{w["shop"]}</strong> - магазин<br><strong>{w["price"]}</strong> - цена<br><strong>{w["money"]}</strong> - деньги</p>'
    
    def get_weather_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Погода</h1><p><strong>{w["sunny"]}</strong> - солнечно<br><strong>{w["rain"]}</strong> - дождь</p>'
    
    def get_travel_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Путешествия</h1><p><strong>{w["airport"]}</strong> - аэропорт<br><strong>{w["passport"]}</strong> - паспорт<br><strong>{w["hotel"]}</strong> - отель</p>'
    
    def get_health_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Здоровье</h1><p><strong>{w["health"]}</strong> - здоровье<br><strong>{w["exercise"]}</strong> - упражнения</p>'
    
    def get_education_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Образование</h1><p><strong>{w["school"]}</strong> - школа</p>'
    
    def get_tech_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Технологии</h1><p><strong>{w["computer"]}</strong> - компьютер<br><strong>{w["internet"]}</strong> - интернет</p>'
    
    def get_environment_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Экология</h1><p><strong>{w["environment"]}</strong> - окружающая среда</p>'
    
    def get_business_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Бизнес</h1><p><strong>{w["business"]}</strong> - бизнес<br><strong>{w["contract"]}</strong> - контракт</p>'
    
    def get_media_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>СМИ</h1><p><strong>{w["media"]}</strong> - медиа</p>'
    
    def get_art_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Искусство</h1><p><strong>{w["art"]}</strong> - искусство</p>'
    
    def get_science_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Наука</h1><p><strong>{w["science"]}</strong> - наука</p>'
    
    def get_politics_lesson(self, lang):
        w = self.get_lang_words(lang)
        return f'<h1>Политика</h1><p><strong>{w["politics"]}</strong> - политика</p>'

    # ==================== СЛОВА ДЛЯ УРОКОВ ====================
    
    def get_words_for_lesson(self, language_name, level, lesson_num):
        w = self.get_lang_words(language_name)
        
        words_by_level = {
            'A1': {
                1: [{'word': w['hello'], 'translation': 'привет'}, {'word': w['good_morning'], 'translation': 'доброе утро'}, {'word': w['thank_you'], 'translation': 'спасибо'}, {'word': w['please'], 'translation': 'пожалуйста'}, {'word': w['goodbye'], 'translation': 'до свидания'}],
                2: [{'word': w['mother'], 'translation': 'мама'}, {'word': w['father'], 'translation': 'папа'}, {'word': w['brother'], 'translation': 'брат'}, {'word': w['sister'], 'translation': 'сестра'}],
                3: [{'word': w['one'], 'translation': 'один'}, {'word': w['two'], 'translation': 'два'}, {'word': w['three'], 'translation': 'три'}],
                4: [{'word': w['red'], 'translation': 'красный'}, {'word': w['blue'], 'translation': 'синий'}, {'word': w['green'], 'translation': 'зелёный'}],
                5: [{'word': w['bread'], 'translation': 'хлеб'}, {'word': w['water'], 'translation': 'вода'}, {'word': w['coffee'], 'translation': 'кофе'}],
            },
            'A2': {
                1: [{'word': w['teacher'], 'translation': 'учитель'}, {'word': w['doctor'], 'translation': 'врач'}],
                2: [{'word': w['wake_up'], 'translation': 'просыпаться'}, {'word': w['breakfast'], 'translation': 'завтрак'}, {'word': w['work'], 'translation': 'работа'}],
                3: [{'word': w['hobby'], 'translation': 'хобби'}, {'word': w['music'], 'translation': 'музыка'}],
                4: [{'word': w['shop'], 'translation': 'магазин'}, {'word': w['price'], 'translation': 'цена'}, {'word': w['money'], 'translation': 'деньги'}],
                5: [{'word': w['sunny'], 'translation': 'солнечно'}, {'word': w['rain'], 'translation': 'дождь'}],
            },
            'B1': {
                1: [{'word': w['airport'], 'translation': 'аэропорт'}, {'word': w['passport'], 'translation': 'паспорт'}, {'word': w['hotel'], 'translation': 'отель'}],
                2: [{'word': w['health'], 'translation': 'здоровье'}, {'word': w['exercise'], 'translation': 'упражнения'}],
                3: [{'word': w['school'], 'translation': 'школа'}],
                4: [{'word': w['computer'], 'translation': 'компьютер'}, {'word': w['internet'], 'translation': 'интернет'}],
                5: [{'word': w['environment'], 'translation': 'окружающая среда'}],
            },
            'B2': {
                1: [{'word': w['business'], 'translation': 'бизнес'}, {'word': w['contract'], 'translation': 'контракт'}],
                2: [{'word': w['media'], 'translation': 'медиа'}],
                3: [{'word': w['art'], 'translation': 'искусство'}],
                4: [{'word': w['science'], 'translation': 'наука'}],
                5: [{'word': w['politics'], 'translation': 'политика'}],
            },
            'C1': {
                1: [{'word': 'Research', 'translation': 'исследование'}, {'word': 'Analysis', 'translation': 'анализ'}],
                2: [{'word': 'Idiom', 'translation': 'идиома'}],
                3: [{'word': 'Negotiation', 'translation': 'переговоры'}],
                4: [{'word': 'Literature', 'translation': 'литература'}],
                5: [{'word': 'Argument', 'translation': 'аргумент'}],
            },
        }
        
        level_words = words_by_level.get(level, words_by_level['A1'])
        return level_words.get(lesson_num, level_words.get(1, []))

    def create_test_for_lesson(self, lesson):
        test = Test.objects.create(lesson=lesson, title=f'Тест: {lesson.title}')

        words = list(lesson.words.all())
        if not words:
            return test

        for i in range(min(5, len(words))):
            word = words[i]
            q = Question.objects.create(test=test, text=f'Как переводится слово "{word.word}"?')
            Answer.objects.create(question=q, text=word.translation, is_correct=True)
            for other in random.sample(words, min(3, len(words))):
                if other.translation != word.translation:
                    Answer.objects.create(question=q, text=other.translation, is_correct=False)

        return test

    # ==================== ТЕСТЫ УРОВНЯ С РЕАЛЬНЫМИ ВОПРОСАМИ ====================
    
    def create_level_tests_for_all_languages(self):
        """Создает тесты уровня для всех языков"""
        self.stdout.write('\nСОЗДАНИЕ ТЕСТОВ УРОВНЯ...')
        
        languages = Language.objects.all()
        
        for language in languages:
            level_test, created = LevelTest.objects.get_or_create(
                language=language,
                defaults={
                    'title': f'Определение уровня {language.name}',
                    'description': f'Ответьте на 15 вопросов, чтобы определить ваш уровень {language.name}.',
                    'passing_score': 70
                }
            )
            
            if created or level_test.questions.count() == 0:
                self.create_level_test_questions(level_test, language.name)
                self.stdout.write(f'  - Создан тест для {language.name}')
            else:
                self.stdout.write(f'  - Тест для {language.name} уже существует')
        
        self.stdout.write('  ТЕСТЫ УРОВНЯ СОЗДАНЫ!\n')

    def create_level_test_questions(self, level_test, language_name):
        """Создает реальные вопросы для теста уровня"""
        
        # Реальные вопросы для английского
        if language_name == 'Английский':
            questions_data = [
                # A1 - 3 вопроса
                {'q': 'Как переводится слово "Hello"?', 'correct': 'Привет', 'options': ['Пока', 'Привет', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': 'Как переводится слово "Cat"?', 'correct': 'Кошка', 'options': ['Собака', 'Кошка', 'Птица', 'Рыба'], 'level': 'A1'},
                {'q': 'Что означает "Good morning"?', 'correct': 'Доброе утро', 'options': ['Добрый день', 'Добрый вечер', 'Доброе утро', 'Спокойной ночи'], 'level': 'A1'},
                # A2 - 3 вопроса
                {'q': 'Как будет "Ресторан" по-английски?', 'correct': 'Restaurant', 'options': ['Hotel', 'Restaurant', 'Cafe', 'Shop'], 'level': 'A2'},
                {'q': 'Что означает "I love you"?', 'correct': 'Я люблю тебя', 'options': ['Я ненавижу тебя', 'Я люблю тебя', 'Я жду тебя', 'Я вижу тебя'], 'level': 'A2'},
                {'q': 'Как переводится слово "Beautiful"?', 'correct': 'Красивый', 'options': ['Страшный', 'Красивый', 'Маленький', 'Большой'], 'level': 'A2'},
                # B1 - 3 вопроса
                {'q': 'Что означает фраза "Break a leg"?', 'correct': 'Удачи', 'options': ['Сломать ногу', 'Удачи', 'Осторожно', 'Быстрее'], 'level': 'B1'},
                {'q': 'Как будет "Забронировать номер" по-английски?', 'correct': 'Book a room', 'options': ['Book a room', 'Rent a room', 'Buy a room', 'Sell a room'], 'level': 'B1'},
                {'q': 'Что означает слово "Travel"?', 'correct': 'Путешествовать', 'options': ['Работать', 'Учиться', 'Путешествовать', 'Отдыхать'], 'level': 'B1'},
                # B2 - 2 вопроса
                {'q': 'Что означает слово "Negotiation"?', 'correct': 'Переговоры', 'options': ['Контракт', 'Переговоры', 'Соглашение', 'Спор'], 'level': 'B2'},
                {'q': 'Что означает фраза "Think outside the box"?', 'correct': 'Мыслить нестандартно', 'options': ['Думать о коробке', 'Мыслить нестандартно', 'Выйти из коробки', 'Думать внутри'], 'level': 'B2'},
                # C1 - 2 вопроса
                {'q': 'Что означает слово "Ubiquitous"?', 'correct': 'Повсеместный', 'options': ['Редкий', 'Повсеместный', 'Уникальный', 'Обычный'], 'level': 'C1'},
                {'q': 'Что означает фраза "At your earliest convenience"?', 'correct': 'При первой возможности', 'options': ['Сейчас же', 'При первой возможности', 'Никогда', 'Завтра'], 'level': 'C1'},
            ]
        # Реальные вопросы для испанского
        elif language_name == 'Испанский':
            questions_data = [
                {'q': 'Как переводится "Hola"?', 'correct': 'Привет', 'options': ['Пока', 'Привет', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': 'Что означает "Gracias"?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': 'Как будет "Семья" по-испански?', 'correct': 'Familia', 'options': ['Casa', 'Familia', 'Trabajo', 'Amigo'], 'level': 'A2'},
                {'q': 'Что означает "Te quiero"?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
                {'q': 'Как переводится "Restaurante"?', 'correct': 'Ресторан', 'options': ['Отель', 'Ресторан', 'Кафе', 'Магазин'], 'level': 'B1'},
                {'q': 'Как переводится "Viaje"?', 'correct': 'Путешествие', 'options': ['Работа', 'Путешествие', 'Школа', 'Дом'], 'level': 'B1'},
                {'q': 'Что означает "Empresa"?', 'correct': 'Компания', 'options': ['Работа', 'Компания', 'Дом', 'Школа'], 'level': 'B2'},
                {'q': 'Как переводится "Futuro"?', 'correct': 'Будущее', 'options': ['Прошлое', 'Будущее', 'Настоящее', 'Время'], 'level': 'B2'},
            ]
        # Реальные вопросы для французского
        elif language_name == 'Французский':
            questions_data = [
                {'q': 'Как переводится "Bonjour"?', 'correct': 'Здравствуйте', 'options': ['До свидания', 'Здравствуйте', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': 'Что означает "Merci"?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': 'Как будет "Семья" по-французски?', 'correct': 'Famille', 'options': ['Maison', 'Famille', 'Travail', 'Ami'], 'level': 'A2'},
                {'q': 'Что означает "Je t\'aime"?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
                {'q': 'Как переводится "Restaurant"?', 'correct': 'Ресторан', 'options': ['Отель', 'Ресторан', 'Кафе', 'Магазин'], 'level': 'B1'},
            ]
        # Реальные вопросы для немецкого
        elif language_name == 'Немецкий':
            questions_data = [
                {'q': 'Как переводится "Hallo"?', 'correct': 'Привет', 'options': ['Пока', 'Привет', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': 'Что означает "Danke"?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': 'Как будет "Семья" по-немецки?', 'correct': 'Familie', 'options': ['Haus', 'Familie', 'Arbeit', 'Freund'], 'level': 'A2'},
                {'q': 'Что означает "Ich liebe dich"?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
                {'q': 'Как переводится "Restaurant"?', 'correct': 'Ресторан', 'options': ['Hotel', 'Restaurant', 'Cafe', 'Geschäft'], 'level': 'B1'},
            ]
        # Реальные вопросы для итальянского
        elif language_name == 'Итальянский':
            questions_data = [
                {'q': 'Как переводится "Ciao"?', 'correct': 'Привет', 'options': ['Пока', 'Привет', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': 'Что означает "Grazie"?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': 'Как будет "Семья" по-итальянски?', 'correct': 'Famiglia', 'options': ['Casa', 'Famiglia', 'Lavoro', 'Amico'], 'level': 'A2'},
                {'q': 'Что означает "Ti amo"?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
                {'q': 'Как переводится "Ristorante"?', 'correct': 'Ресторан', 'options': ['Hotel', 'Ristorante', 'Caffè', 'Negozio'], 'level': 'B1'},
            ]
        # Реальные вопросы для японского
        elif language_name == 'Японский':
            questions_data = [
                {'q': 'Как переводится "こんにちは"?', 'correct': 'Здравствуйте', 'options': ['До свидания', 'Здравствуйте', 'Спасибо', 'Извините'], 'level': 'A1'},
                {'q': 'Что означает "ありがとう"?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': 'Как будет "Семья" по-японски?', 'correct': '家族', 'options': ['家', '家族', '仕事', '友達'], 'level': 'A2'},
                {'q': 'Что означает "愛してる"?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
                {'q': 'Как переводится "レストラン"?', 'correct': 'Ресторан', 'options': ['ホテル', 'レストラン', 'カフェ', '店'], 'level': 'B1'},
            ]
        else:
            # Общий вариант для других языков (не должен сработать)
            questions_data = [
                {'q': f'Как сказать "Привет" на {language_name}?', 'correct': 'Привет', 'options': ['Пока', 'Привет', 'Спасибо', 'Пожалуйста'], 'level': 'A1'},
                {'q': f'Как сказать "Спасибо" на {language_name}?', 'correct': 'Спасибо', 'options': ['Пожалуйста', 'Спасибо', 'Извините', 'Привет'], 'level': 'A1'},
                {'q': f'Как сказать "Я тебя люблю" на {language_name}?', 'correct': 'Я тебя люблю', 'options': ['Я тебя ненавижу', 'Я тебя люблю', 'Я тебя жду', 'Я тебя вижу'], 'level': 'A2'},
            ]
        
        for i, q in enumerate(questions_data):
            question = LevelTestQuestion.objects.create(
                test=level_test,
                text=q['q'],
                order=i + 1
            )
            
            # Правильный ответ
            LevelTestAnswer.objects.create(
                question=question,
                text=q['correct'],
                is_correct=True,
                difficulty_level=q['level']
            )
            
            # Неправильные ответы
            for option in q['options']:
                if option != q['correct']:
                    LevelTestAnswer.objects.create(
                        question=question,
                        text=option,
                        is_correct=False,
                        difficulty_level=q['level']
                    )

    def print_statistics(self, total_lessons, total_words, total_tests):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('СТАТИСТИКА ПЛАТФОРМЫ:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Языков: {Language.objects.count()}')
        self.stdout.write(f'  Курсов: {Course.objects.count()}')
        self.stdout.write(f'  Уроков: {total_lessons}')
        self.stdout.write(f'  Слов для изучения: {total_words}')
        self.stdout.write(f'  Тестов: {total_tests}')
        self.stdout.write(self.style.SUCCESS('=' * 60))