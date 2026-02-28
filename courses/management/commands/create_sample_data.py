# courses/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import Language, Course, Lesson, Word, Test, Question, Answer
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Создает полные тестовые данные для приложения'

    def handle(self, *args, **kwargs):
        self.stdout.write('=' * 60)
        self.stdout.write('Создание полных тестовых данных...')
        self.stdout.write('=' * 60)
        
        # Удаляем старые данные
        self.clear_old_data()
        
        # Создаем 6 языков
        languages = self.create_languages()
        
        # Создаем курсы, уроки и тесты
        self.create_all_courses_and_content(languages)
        
        # Выводим статистику
        self.print_statistics()
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('Все данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def clear_old_data(self):
        """Очищает старые данные"""
        self.stdout.write('Очистка старых данных...')
        models = [Answer, Question, Test, Word, Lesson, Course, Language]
        for model in models:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'  Удалено {count} записей {model.__name__}')

    def create_languages(self):
        """Создает 6 языков"""
        self.stdout.write('\nСоздание языков...')
        
        languages_data = [
            {
                'name': 'Английский',
                'description': '''Английский язык - самый распространенный язык в мире, lingua franca современности. На нем говорят более 1.5 миллиарда человек в 67 странах. Это язык международного бизнеса, науки, технологий, авиации и туризма. Английский открывает доступ к 60% всего контента в интернете, большинству научных публикаций и мировых новостей. Изучение английского увеличивает зарплату на 20-30% и открывает возможности для работы в международных компаниях.''',
                'icon': 'fas fa-flag-usa',
                'color': '#4361ee'
            },
            {
                'name': 'Испанский',
                'description': '''Испанский язык - второй по распространенности родной язык в мире. На нем говорят 580 миллионов человек в 21 стране. Испанский - язык страсти, фламенко, корриды и великой литературы. Это официальный язык ООН, Евросоюза и многих международных организаций. Испания и Латинская Америка - быстрорастущие экономики, что делает испанский ценным для бизнеса. Язык Сервантеса, Гарсиа Маркеса и Лорки отличается богатством и эмоциональностью.''',
                'icon': 'fas fa-sun',
                'color': '#f72585'
            },
            {
                'name': 'Французский',
                'description': '''Французский язык - язык любви, искусства и дипломатии. На нем говорят 300 миллионов человек в 29 странах. Французский - официальный язык ООН, Евросоюза, НАТО и Международного Олимпийского комитета. Это язык высокой моды, кулинарии, философии и кинематографа. Франция - мировой лидер в туризме, вине и парфюмерии. Изучение французского позволяет понять произведения Виктора Гюго, Альбера Камю и Коко Шанель.''',
                'icon': 'fas fa-flag',
                'color': '#7209b7'
            },
            {
                'name': 'Немецкий',
                'description': '''Немецкий язык - самый распространенный язык в Европейском Союзе. На нем говорят 130 миллионов человек. Германия - крупнейшая экономика Европы, мировой лидер в автомобилестроении (Mercedes, BMW, Volkswagen), инженерии и химической промышленности. Немецкий - язык философии (Кант, Гегель, Ницше), литературы (Гёте, Кафка) и классической музыки (Бах, Бетховен, Моцарт). Изучение немецкого открывает доступ к качественному бесплатному образованию в Германии.''',
                'icon': 'fas fa-landmark',
                'color': '#4cc9f0'
            },
            {
                'name': 'Итальянский',
                'description': '''Итальянский язык - язык искусства, музыки и кулинарии. На нем говорят 85 миллионов человек. Италия - родина Возрождения, мировой центр моды, дизайна и оперы. Итальянский - язык Данте, Леонардо да Винчи, Верди и Феллини. 60% мирового культурного наследия находится в Италии. Язык отличается мелодичностью, большинство музыкальных терминов имеют итальянское происхождение. Итальянская кухня признана ЮНЕСКО культурным наследием человечества.''',
                'icon': 'fas fa-pizza-slice',
                'color': '#ff9e00'
            },
            {
                'name': 'Японский',
                'description': '''Японский язык - уникальный язык с тремя системами письма. На нем говорят 125 миллионов человек. Япония - третья экономика мира, лидер в робототехнике, электронике и автомобилестроении (Toyota, Sony, Panasonic). Японский открывает доступ к аниме, манге, видеоиграм и боевым искусствам. Японская культура сочетает древние традиции с высокими технологиями. Изучение японского развивает дисциплину, память и понимание восточной философии.''',
                'icon': 'fas fa-torii-gate',
                'color': '#3a0ca3'
            }
        ]
        
        languages = []
        for lang_data in languages_data:
            language = Language.objects.create(
                name=lang_data['name'],
                description=lang_data['description'],
                icon=lang_data['icon']
            )
            languages.append(language)
            self.stdout.write(f'  ✓ Создан язык: {language.name}')
        
        return languages

    def create_all_courses_and_content(self, languages):
        """Создает все курсы, уроки и тесты"""
        self.stdout.write('\nСоздание курсов, уроков и тестов...')
        
        total_lessons = 0
        total_words = 0
        total_tests = 0
        
        for language in languages:
            self.stdout.write(f'\nЯзык: {language.name}')
            
            # Создаем 5 курсов (уровней) для каждого языка
            courses = self.create_courses_for_language(language)
            
            for course in courses:
                self.stdout.write(f'  Курс: {course.title} ({course.level})')
                
                # Создаем 5 уроков для курса
                lessons = self.create_lessons_for_course(course)
                total_lessons += len(lessons)
                
                # Подсчитываем слова
                for lesson in lessons:
                    words_count = lesson.words.count()
                    total_words += words_count
                
                # Создаем тесты для уроков
                for lesson in lessons:
                    self.create_comprehensive_test_for_lesson(lesson)
                    total_tests += 1
        
        return total_lessons, total_words, total_tests

    def create_courses_for_language(self, language):
        """Создает 5 курсов (уровней) для языка"""
        levels = [
            {
                'code': 'A1',
                'title': 'Для начинающих',
                'description': 'Основы языка: алфавит, базовые фразы, простые диалоги, числа, цвета, семья.',
                'color': '#4361ee',
                'hours': 40,
                'words': 300
            },
            {
                'code': 'A2',
                'title': 'Элементарный',
                'description': 'Повседневные темы: работа, хобби, путешествия, ресторан, покупки, здоровье.',
                'color': '#4895ef',
                'hours': 60,
                'words': 600
            },
            {
                'code': 'B1',
                'title': 'Средний',
                'description': 'Свободное общение: опыт, планы, мнения, обсуждение книг и фильмов, простые переговоры.',
                'color': '#4cc9f0',
                'hours': 80,
                'words': 1200
            },
            {
                'code': 'B2',
                'title': 'Выше среднего',
                'description': 'Сложные темы: абстрактные идеи, технические тексты, профессиональная лексика, презентации.',
                'color': '#3a0ca3',
                'hours': 100,
                'words': 2000
            },
            {
                'code': 'C1',
                'title': 'Продвинутый',
                'description': 'Углубленное изучение: идиомы, нюансы, специализированная лексика, литературный анализ.',
                'color': '#7209b7',
                'hours': 120,
                'words': 3000
            }
        ]
        
        courses = []
        for i, level_data in enumerate(levels):
            course = Course.objects.create(
                language=language,
                title=f'{language.name} - {level_data["title"]}',
                description=f'''Курс уровня {level_data["code"]} по изучению {language.name.lower()}. {level_data["description"]}
                
                <strong>Что вы изучите:</strong>
                • {level_data["words"]} самых важных слов и выражений
                • Все основные грамматические конструкции
                • Правильное произношение и интонацию
                • Культурные особенности и этикет
                
                <strong>Результат:</strong>
                По окончании курса вы сможете {self.get_course_outcome(level_data["code"], language.name)}.
                
                <strong>Продолжительность:</strong> {level_data["hours"]} часов обучения
                <strong>Формат:</strong> 5 уроков + тесты + практические задания''',
                level=level_data['code'],
                order=i + 1,
                color=level_data['color'],
                is_active=True
            )
            courses.append(course)
        
        return courses

    def get_course_outcome(self, level, language_name):
        """Возвращает описание результата курса"""
        outcomes = {
            'A1': f'понимать и использовать элементарные фразы на {language_name.lower()}, представиться, задавать простые вопросы о себе и других, общаться на базовые темы при условии, что собеседник говорит медленно и четко',
            'A2': f'общаться на повседневные темы (работа, семья, покупки), понимать отдельные предложения и часто используемые выражения, описывать простым языком аспекты своей жизни и окружения',
            'B1': f'понимать основные идеи сложных текстов на конкретные и абстрактные темы, спонтанно общаться с носителями языка без напряжения для любой из сторон, ясно выражать мнение по широкому кругу вопросов',
            'B2': f'понимать содержание сложных текстов на конкретные и абстрактные темы, включая технические дискуссии в своей области специализации, свободно и спонтанно общаться с носителями языка, создавать четкие подробные тексты на различные темы',
            'C1': f'понимать объемные сложные тексты различной тематики, распознавать скрытые значения, свободно и спонтанно выражать мысли без явных затруднений с подбором слов, эффективно использовать язык в социальной, профессиональной и академической деятельности'
        }
        return outcomes.get(level, 'овладеть основами языка')

    def create_lessons_for_course(self, course):
        """Создает 5 уроков для курса"""
        language_name = course.language.name
        level = course.level
        
        # Выбираем соответствующий метод для получения уроков
        if language_name == 'Английский':
            lessons_data = self.get_english_lessons(level)
        elif language_name == 'Испанский':
            lessons_data = self.get_spanish_lessons(level)
        elif language_name == 'Французский':
            lessons_data = self.get_french_lessons(level)
        elif language_name == 'Немецкий':
            lessons_data = self.get_german_lessons(level)
        elif language_name == 'Итальянский':
            lessons_data = self.get_italian_lessons(level)
        elif language_name == 'Японский':
            lessons_data = self.get_japanese_lessons(level)
        else:
            lessons_data = self.get_general_lessons(language_name, level)
        
        lessons = []
        for i, lesson_data in enumerate(lessons_data):
            lesson = Lesson.objects.create(
                course=course,
                title=lesson_data['title'],
                content=lesson_data['content'],
                order=i + 1,
                estimated_time_minutes=45 + i * 15
            )
            
            # Добавляем слова
            for word_data in lesson_data['words']:
                Word.objects.create(
                    lesson=lesson,
                    word=word_data['word'],
                    translation=word_data['translation'],
                    transcription=word_data.get('transcription', ''),
                    example=word_data['example'],
                    part_of_speech=word_data.get('part_of_speech', '')
                )
            
            lessons.append(lesson)
        
        return lessons

    def get_english_lessons(self, level):
        """Уроки для английского языка по уровням"""
        lessons = {
            'A1': [
                {
                    'title': 'Greetings and Introductions',
                    'content': '''<h1>Lesson 1: Greetings and Introductions</h1>
                    
                    <h2>📚 Lesson Goals</h2>
                    <ul>
                        <li>Learn to greet people at different times of day</li>
                        <li>Introduce yourself and meet others</li>
                        <li>Ask and answer basic questions about yourself</li>
                    </ul>
                    
                    <h2>👋 Basic Greetings</h2>
                    <div class="phrase-box">
                        <p><strong>Hello / Hi</strong> - Universal greeting</p>
                        <p><strong>Good morning</strong> - Before 12:00 PM</p>
                        <p><strong>Good afternoon</strong> - 12:00 PM - 6:00 PM</p>
                        <p><strong>Good evening</strong> - After 6:00 PM</p>
                        <p><strong>Good night</strong> - When going to sleep</p>
                    </div>
                    
                    <h2>🗣️ Dialogue</h2>
                    <div class="dialogue">
                        <p><strong>John:</strong> Hello! Good morning. How are you?</p>
                        <p><strong>Sarah:</strong> Hi! I'm fine, thank you. And you?</p>
                        <p><strong>John:</strong> I'm good too. What's your name?</p>
                        <p><strong>Sarah:</strong> My name is Sarah. Nice to meet you!</p>
                        <p><strong>John:</strong> Nice to meet you too, Sarah!</p>
                    </div>
                    
                    <h2>🔑 Key Phrases</h2>
                    <ul>
                        <li><strong>What's your name?</strong> - Как тебя зовут?</li>
                        <li><strong>My name is...</strong> - Меня зовут...</li>
                        <li><strong>How are you?</strong> - Как дела?</li>
                        <li><strong>I'm fine, thank you.</strong> - У меня все хорошо, спасибо.</li>
                        <li><strong>Nice to meet you!</strong> - Приятно познакомиться!</li>
                    </ul>''',
                    'words': [
                        {'word': 'hello', 'translation': 'привет', 'transcription': '[həˈləʊ]', 'example': 'Hello, how are you today?', 'part_of_speech': 'interjection'},
                        {'word': 'goodbye', 'translation': 'до свидания', 'transcription': '[ɡʊdˈbaɪ]', 'example': 'Goodbye, see you tomorrow!', 'part_of_speech': 'interjection'},
                        {'word': 'name', 'translation': 'имя', 'transcription': '[neɪm]', 'example': 'My name is John.', 'part_of_speech': 'noun'},
                        {'word': 'meet', 'translation': 'встречать', 'transcription': '[miːt]', 'example': 'Nice to meet you!', 'part_of_speech': 'verb'},
                        {'word': 'friend', 'translation': 'друг', 'transcription': '[frend]', 'example': 'He is my best friend.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Family and Relatives',
                    'content': '''<h1>Lesson 2: Family and Relatives</h1>
                    
                    <h2>👨‍👩‍👧‍👦 Family Members</h2>
                    <table class="table">
                        <tr><th>English</th><th>Russian</th></tr>
                        <tr><td>mother</td><td>мама</td></tr>
                        <tr><td>father</td><td>папа</td></tr>
                        <tr><td>brother</td><td>брат</td></tr>
                        <tr><td>sister</td><td>сестра</td></tr>
                        <tr><td>grandmother</td><td>бабушка</td></tr>
                        <tr><td>grandfather</td><td>дедушка</td></tr>
                        <tr><td>uncle</td><td>дядя</td></tr>
                        <tr><td>aunt</td><td>тетя</td></tr>
                    </table>
                    
                    <h2>📝 Example</h2>
                    <p>My family is big. I have a mother, a father, two brothers and one sister. My mother's name is Anna and my father's name is Peter. My grandmother lives with us.</p>
                    
                    <h2>🎯 Practice</h2>
                    <p>Describe your family using the new words.</p>''',
                    'words': [
                        {'word': 'mother', 'translation': 'мама', 'transcription': '[ˈmʌðə]', 'example': 'My mother is a doctor.', 'part_of_speech': 'noun'},
                        {'word': 'father', 'translation': 'папа', 'transcription': '[ˈfɑːðə]', 'example': 'My father works in an office.', 'part_of_speech': 'noun'},
                        {'word': 'brother', 'translation': 'брат', 'transcription': '[ˈbrʌðə]', 'example': 'I have an older brother.', 'part_of_speech': 'noun'},
                        {'word': 'sister', 'translation': 'сестра', 'transcription': '[ˈsɪstə]', 'example': 'My sister is younger than me.', 'part_of_speech': 'noun'},
                        {'word': 'family', 'translation': 'семья', 'transcription': '[ˈfæməli]', 'example': 'My family is very important to me.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Numbers and Age',
                    'content': '''<h1>Lesson 3: Numbers and Age</h1>
                    
                    <h2>🔢 Numbers 1-20</h2>
                    <p>1 - one, 2 - two, 3 - three, 4 - four, 5 - five, 6 - six, 7 - seven, 8 - eight, 9 - nine, 10 - ten</p>
                    <p>11 - eleven, 12 - twelve, 13 - thirteen, 14 - fourteen, 15 - fifteen, 16 - sixteen, 17 - seventeen, 18 - eighteen, 19 - nineteen, 20 - twenty</p>
                    
                    <h2>🎂 Talking about Age</h2>
                    <p><strong>How old are you?</strong> - Сколько тебе лет?</p>
                    <p><strong>I am [age] years old.</strong> - Мне [возраст] лет.</p>
                    
                    <h2>📝 Examples</h2>
                    <ul>
                        <li>I am 25 years old.</li>
                        <li>My brother is 30 years old.</li>
                        <li>She is 18 years old.</li>
                    </ul>''',
                    'words': [
                        {'word': 'one', 'translation': 'один', 'transcription': '[wʌn]', 'example': 'I have one cat.', 'part_of_speech': 'numeral'},
                        {'word': 'two', 'translation': 'два', 'transcription': '[tuː]', 'example': 'I have two brothers.', 'part_of_speech': 'numeral'},
                        {'word': 'three', 'translation': 'три', 'transcription': '[θriː]', 'example': 'She has three apples.', 'part_of_speech': 'numeral'},
                        {'word': 'ten', 'translation': 'десять', 'transcription': '[ten]', 'example': 'Ten students in the class.', 'part_of_speech': 'numeral'},
                        {'word': 'age', 'translation': 'возраст', 'transcription': '[eɪdʒ]', 'example': 'What is your age?', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Colors',
                    'content': '''<h1>Lesson 4: Colors</h1>
                    
                    <h2>🎨 Basic Colors</h2>
                    <ul>
                        <li><span style="color: red;">red</span> - красный</li>
                        <li><span style="color: blue;">blue</span> - синий</li>
                        <li><span style="color: green;">green</span> - зеленый</li>
                        <li><span style="color: yellow;">yellow</span> - желтый</li>
                        <li><span style="color: black;">black</span> - черный</li>
                        <li><span style="color: white;">white</span> - белый</li>
                        <li>orange - оранжевый</li>
                        <li>purple - фиолетовый</li>
                        <li>pink - розовый</li>
                        <li>brown - коричневый</li>
                    </ul>
                    
                    <h2>📝 Examples</h2>
                    <ul>
                        <li>The sky is blue.</li>
                        <li>The grass is green.</li>
                        <li>My car is red.</li>
                        <li>Snow is white.</li>
                    </ul>''',
                    'words': [
                        {'word': 'red', 'translation': 'красный', 'transcription': '[red]', 'example': 'The apple is red.', 'part_of_speech': 'adjective'},
                        {'word': 'blue', 'translation': 'синий', 'transcription': '[bluː]', 'example': 'The ocean is blue.', 'part_of_speech': 'adjective'},
                        {'word': 'green', 'translation': 'зеленый', 'transcription': '[ɡriːn]', 'example': 'The leaves are green.', 'part_of_speech': 'adjective'},
                        {'word': 'yellow', 'translation': 'желтый', 'transcription': '[ˈjeləʊ]', 'example': 'The sun is yellow.', 'part_of_speech': 'adjective'},
                        {'word': 'black', 'translation': 'черный', 'transcription': '[blæk]', 'example': 'My cat is black.', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': 'Food and Drinks',
                    'content': '''<h1>Lesson 5: Food and Drinks</h1>
                    
                    <h2>🍎 Food Vocabulary</h2>
                    <ul>
                        <li>bread - хлеб</li>
                        <li>butter - масло</li>
                        <li>cheese - сыр</li>
                        <li>milk - молоко</li>
                        <li>eggs - яйца</li>
                        <li>meat - мясо</li>
                        <li>fish - рыба</li>
                        <li>vegetables - овощи</li>
                        <li>fruit - фрукты</li>
                    </ul>
                    
                    <h2>☕ Drinks</h2>
                    <ul>
                        <li>water - вода</li>
                        <li>coffee - кофе</li>
                        <li>tea - чай</li>
                        <li>juice - сок</li>
                    </ul>
                    
                    <h2>📝 Dialogue at a Restaurant</h2>
                    <div class="dialogue">
                        <p><strong>Waiter:</strong> What would you like to drink?</p>
                        <p><strong>Customer:</strong> I would like coffee, please.</p>
                        <p><strong>Waiter:</strong> And to eat?</p>
                        <p><strong>Customer:</strong> I'll have bread and cheese.</p>
                    </div>''',
                    'words': [
                        {'word': 'bread', 'translation': 'хлеб', 'transcription': '[bred]', 'example': 'I eat bread every day.', 'part_of_speech': 'noun'},
                        {'word': 'water', 'translation': 'вода', 'transcription': '[ˈwɔːtə]', 'example': 'Drink water, it\'s healthy.', 'part_of_speech': 'noun'},
                        {'word': 'coffee', 'translation': 'кофе', 'transcription': '[ˈkɒfi]', 'example': 'I drink coffee in the morning.', 'part_of_speech': 'noun'},
                        {'word': 'apple', 'translation': 'яблоко', 'transcription': '[ˈæpl]', 'example': 'An apple a day keeps the doctor away.', 'part_of_speech': 'noun'},
                        {'word': 'restaurant', 'translation': 'ресторан', 'transcription': '[ˈrestrɒnt]', 'example': 'Let\'s go to a restaurant.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'A2': [
                {
                    'title': 'Jobs and Professions',
                    'content': '''<h1>Lesson 1: Jobs and Professions</h1>
                    
                    <h2>👔 Common Professions</h2>
                    <table class="table">
                        <tr><th>English</th><th>Russian</th></tr>
                        <tr><td>teacher</td><td>учитель</td></tr>
                        <tr><td>doctor</td><td>врач</td></tr>
                        <tr><td>engineer</td><td>инженер</td></tr>
                        <tr><td>lawyer</td><td>юрист</td></tr>
                        <tr><td>accountant</td><td>бухгалтер</td></tr>
                        <tr><td>programmer</td><td>программист</td></tr>
                        <tr><td>manager</td><td>менеджер</td></tr>
                        <tr><td>salesperson</td><td>продавец</td></tr>
                    </table>
                    
                    <h2>🗣️ Dialogue about Work</h2>
                    <div class="dialogue">
                        <p><strong>Tom:</strong> What do you do?</p>
                        <p><strong>Anna:</strong> I'm a teacher. I work at a school. And you?</p>
                        <p><strong>Tom:</strong> I'm an engineer. I work for a construction company.</p>
                        <p><strong>Anna:</strong> Do you like your job?</p>
                        <p><strong>Tom:</strong> Yes, I love it. It's very interesting.</p>
                    </div>
                    
                    <h2>📝 Workplace Vocabulary</h2>
                    <ul>
                        <li>office - офис</li>
                        <li>colleague - коллега</li>
                        <li>boss - начальник</li>
                        <li>salary - зарплата</li>
                        <li>meeting - встреча</li>
                    </ul>''',
                    'words': [
                        {'word': 'teacher', 'translation': 'учитель', 'transcription': '[ˈtiːtʃə]', 'example': 'My mother is a teacher.', 'part_of_speech': 'noun'},
                        {'word': 'doctor', 'translation': 'врач', 'transcription': '[ˈdɒktə]', 'example': 'The doctor works at the hospital.', 'part_of_speech': 'noun'},
                        {'word': 'engineer', 'translation': 'инженер', 'transcription': '[ˌendʒɪˈnɪə]', 'example': 'He is a civil engineer.', 'part_of_speech': 'noun'},
                        {'word': 'office', 'translation': 'офис', 'transcription': '[ˈɒfɪs]', 'example': 'I work in a big office.', 'part_of_speech': 'noun'},
                        {'word': 'job', 'translation': 'работа', 'transcription': '[dʒɒb]', 'example': 'I love my job.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Daily Routine',
                    'content': '''<h1>Lesson 2: Daily Routine</h1>
                    
                    <h2>⏰ Morning Routine</h2>
                    <ul>
                        <li>wake up - просыпаться</li>
                        <li>get up - вставать</li>
                        <li>take a shower - принимать душ</li>
                        <li>brush teeth - чистить зубы</li>
                        <li>get dressed - одеваться</li>
                        <li>have breakfast - завтракать</li>
                        <li>go to work - идти на работу</li>
                    </ul>
                    
                    <h2>📝 Example Text</h2>
                    <p>I wake up at 7 AM every day. I take a shower and brush my teeth. Then I have breakfast. I usually have coffee and cereal. I leave home at 8 AM and go to work. I start work at 9 AM.</p>
                    
                    <h2>🕐 Time Expressions</h2>
                    <ul>
                        <li>in the morning - утром</li>
                        <li>in the afternoon - днем</li>
                        <li>in the evening - вечером</li>
                        <li>at night - ночью</li>
                    </ul>''',
                    'words': [
                        {'word': 'wake up', 'translation': 'просыпаться', 'transcription': '[weɪk ʌp]', 'example': 'I wake up at 7 AM.', 'part_of_speech': 'verb'},
                        {'word': 'breakfast', 'translation': 'завтрак', 'transcription': '[ˈbrekfəst]', 'example': 'Breakfast is the most important meal.', 'part_of_speech': 'noun'},
                        {'word': 'work', 'translation': 'работа', 'transcription': '[wɜːk]', 'example': 'I go to work by bus.', 'part_of_speech': 'noun'},
                        {'word': 'morning', 'translation': 'утро', 'transcription': '[ˈmɔːnɪŋ]', 'example': 'I exercise in the morning.', 'part_of_speech': 'noun'},
                        {'word': 'evening', 'translation': 'вечер', 'transcription': '[ˈiːvnɪŋ]', 'example': 'I watch TV in the evening.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Hobbies and Free Time',
                    'content': '''<h1>Lesson 3: Hobbies and Free Time</h1>
                    
                    <h2>🎨 Common Hobbies</h2>
                    <ul>
                        <li>reading - чтение</li>
                        <li>watching movies - просмотр фильмов</li>
                        <li>playing sports - занятия спортом</li>
                        <li>listening to music - слушать музыку</li>
                        <li>cooking - готовка</li>
                        <li>traveling - путешествия</li>
                        <li>photography - фотография</li>
                        <li>gardening - садоводство</li>
                    </ul>
                    
                    <h2>🗣️ Dialogue about Hobbies</h2>
                    <div class="dialogue">
                        <p><strong>Mike:</strong> What do you like to do in your free time?</p>
                        <p><strong>Lisa:</strong> I love reading books and watching movies. What about you?</p>
                        <p><strong>Mike:</strong> I enjoy playing football and listening to music.</p>
                        <p><strong>Lisa:</strong> That sounds fun! What kind of music do you like?</p>
                        <p><strong>Mike:</strong> I like rock and pop music.</p>
                    </div>''',
                    'words': [
                        {'word': 'hobby', 'translation': 'хобби', 'transcription': '[ˈhɒbi]', 'example': 'My hobby is photography.', 'part_of_speech': 'noun'},
                        {'word': 'read', 'translation': 'читать', 'transcription': '[riːd]', 'example': 'I read books every day.', 'part_of_speech': 'verb'},
                        {'word': 'music', 'translation': 'музыка', 'transcription': '[ˈmjuːzɪk]', 'example': 'I listen to music in the car.', 'part_of_speech': 'noun'},
                        {'word': 'sport', 'translation': 'спорт', 'transcription': '[spɔːt]', 'example': 'Football is a popular sport.', 'part_of_speech': 'noun'},
                        {'word': 'travel', 'translation': 'путешествовать', 'transcription': '[ˈtrævl]', 'example': 'I want to travel the world.', 'part_of_speech': 'verb'}
                    ]
                },
                {
                    'title': 'Shopping',
                    'content': '''<h1>Lesson 4: Shopping</h1>
                    
                    <h2>🛍️ Shopping Vocabulary</h2>
                    <ul>
                        <li>store / shop - магазин</li>
                        <li>supermarket - супермаркет</li>
                        <li>clothes store - магазин одежды</li>
                        <li>price - цена</li>
                        <li>money - деньги</li>
                        <li>credit card - кредитная карта</li>
                        <li>cash - наличные</li>
                        <li>receipt - чек</li>
                    </ul>
                    
                    <h2>🗣️ Shopping Dialogue</h2>
                    <div class="dialogue">
                        <p><strong>Salesperson:</strong> Can I help you?</p>
                        <p><strong>Customer:</strong> Yes, how much is this T-shirt?</p>
                        <p><strong>Salesperson:</strong> It's $25.</p>
                        <p><strong>Customer:</strong> Do you have it in a different color?</p>
                        <p><strong>Salesperson:</strong> Yes, we have it in blue and black.</p>
                        <p><strong>Customer:</strong> I'll take the blue one. Can I pay by card?</p>
                        <p><strong>Salesperson:</strong> Of course. Here's your receipt.</p>
                    </div>''',
                    'words': [
                        {'word': 'shop', 'translation': 'магазин', 'transcription': '[ʃɒp]', 'example': 'I go to the shop every weekend.', 'part_of_speech': 'noun'},
                        {'word': 'buy', 'translation': 'покупать', 'transcription': '[baɪ]', 'example': 'I want to buy a new phone.', 'part_of_speech': 'verb'},
                        {'word': 'price', 'translation': 'цена', 'transcription': '[praɪs]', 'example': 'The price is too high.', 'part_of_speech': 'noun'},
                        {'word': 'money', 'translation': 'деньги', 'transcription': '[ˈmʌni]', 'example': 'I don\'t have enough money.', 'part_of_speech': 'noun'},
                        {'word': 'receipt', 'translation': 'чек', 'transcription': '[rɪˈsiːt]', 'example': 'Keep your receipt.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Weather and Seasons',
                    'content': '''<h1>Lesson 5: Weather and Seasons</h1>
                    
                    <h2>☀️ Weather Vocabulary</h2>
                    <ul>
                        <li>sunny - солнечно</li>
                        <li>cloudy - облачно</li>
                        <li>rainy - дождливо</li>
                        <li>snowy - снежно</li>
                        <li>windy - ветрено</li>
                        <li>hot - жарко</li>
                        <li>cold - холодно</li>
                        <li>warm - тепло</li>
                        <li>cool - прохладно</li>
                    </ul>
                    
                    <h2>🍂 Seasons</h2>
                    <ul>
                        <li>spring - весна</li>
                        <li>summer - лето</li>
                        <li>autumn (fall) - осень</li>
                        <li>winter - зима</li>
                    </ul>
                    
                    <h2>🗣️ Talking about Weather</h2>
                    <div class="dialogue">
                        <p><strong>Person A:</strong> What's the weather like today?</p>
                        <p><strong>Person B:</strong> It's sunny and warm. Perfect for a walk!</p>
                        <p><strong>Person A:</strong> I love summer weather.</p>
                        <p><strong>Person B:</strong> Me too. But winter is nice for skiing.</p>
                    </div>''',
                    'words': [
                        {'word': 'sunny', 'translation': 'солнечно', 'transcription': '[ˈsʌni]', 'example': 'It is sunny today.', 'part_of_speech': 'adjective'},
                        {'word': 'rain', 'translation': 'дождь', 'transcription': '[reɪn]', 'example': 'Rain is good for plants.', 'part_of_speech': 'noun'},
                        {'word': 'snow', 'translation': 'снег', 'transcription': '[snəʊ]', 'example': 'Snow is white and cold.', 'part_of_speech': 'noun'},
                        {'word': 'summer', 'translation': 'лето', 'transcription': '[ˈsʌmə]', 'example': 'Summer is my favorite season.', 'part_of_speech': 'noun'},
                        {'word': 'winter', 'translation': 'зима', 'transcription': '[ˈwɪntə]', 'example': 'Winter is very cold.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'B1': [
                {
                    'title': 'Travel and Tourism',
                    'content': '''<h1>Lesson 1: Travel and Tourism</h1>
                    
                    <h2>✈️ Travel Vocabulary</h2>
                    <ul>
                        <li>flight - рейс</li>
                        <li>airport - аэропорт</li>
                        <li>passport - паспорт</li>
                        <li>visa - виза</li>
                        <li>luggage - багаж</li>
                        <li>boarding pass - посадочный талон</li>
                        <li>destination - пункт назначения</li>
                        <li>accommodation - жилье</li>
                        <li>reservation - бронирование</li>
                    </ul>
                    
                    <h2>🏨 Types of Accommodation</h2>
                    <ul>
                        <li>hotel - отель</li>
                        <li>hostel - хостел</li>
                        <li>apartment - квартира</li>
                        <li>villa - вилла</li>
                        <li>guesthouse - гостевой дом</li>
                    </ul>
                    
                    <h2>🗣️ Dialogue at the Airport</h2>
                    <div class="dialogue">
                        <p><strong>Passenger:</strong> Excuse me, where is the check-in desk for flight BA249?</p>
                        <p><strong>Staff:</strong> It's at counter number 7. Do you have your passport and ticket?</p>
                        <p><strong>Passenger:</strong> Yes, here they are. I'd like a window seat, please.</p>
                        <p><strong>Staff:</strong> Of course. How many bags are you checking in?</p>
                        <p><strong>Passenger:</strong> Just one suitcase. The other one is hand luggage.</p>
                    </div>''',
                    'words': [
                        {'word': 'travel', 'translation': 'путешествовать', 'transcription': '[ˈtrævl]', 'example': 'I love to travel abroad.', 'part_of_speech': 'verb'},
                        {'word': 'airport', 'translation': 'аэропорт', 'transcription': '[ˈeəpɔːt]', 'example': 'The airport is very busy.', 'part_of_speech': 'noun'},
                        {'word': 'passport', 'translation': 'паспорт', 'transcription': '[ˈpɑːspɔːt]', 'example': 'Don\'t forget your passport.', 'part_of_speech': 'noun'},
                        {'word': 'hotel', 'translation': 'отель', 'transcription': '[həʊˈtel]', 'example': 'We booked a nice hotel.', 'part_of_speech': 'noun'},
                        {'word': 'ticket', 'translation': 'билет', 'transcription': '[ˈtɪkɪt]', 'example': 'I bought a plane ticket.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Health and Fitness',
                    'content': '''<h1>Lesson 2: Health and Fitness</h1>
                    
                    <h2>🏃‍♂️ Health Vocabulary</h2>
                    <ul>
                        <li>healthy - здоровый</li>
                        <li>exercise - упражнение</li>
                        <li>fitness - фитнес</li>
                        <li>diet - диета</li>
                        <li>vitamins - витамины</li>
                        <li>gym - спортзал</li>
                        <li>workout - тренировка</li>
                    </ul>
                    
                    <h2>🤒 Illnesses</h2>
                    <ul>
                        <li>cold - простуда</li>
                        <li>flu - грипп</li>
                        <li>headache - головная боль</li>
                        <li>fever - температура</li>
                        <li>cough - кашель</li>
                    </ul>
                    
                    <h2>🗣️ Dialogue at the Doctor</h2>
                    <div class="dialogue">
                        <p><strong>Doctor:</strong> What seems to be the problem?</p>
                        <p><strong>Patient:</strong> I have a headache and a sore throat.</p>
                        <p><strong>Doctor:</strong> Do you have a fever?</p>
                        <p><strong>Patient:</strong> Yes, I think so. I feel very tired.</p>
                        <p><strong>Doctor:</strong> You have the flu. Rest and drink plenty of water.</p>
                    </div>''',
                    'words': [
                        {'word': 'health', 'translation': 'здоровье', 'transcription': '[helθ]', 'example': 'Health is the most important thing.', 'part_of_speech': 'noun'},
                        {'word': 'exercise', 'translation': 'упражнение', 'transcription': '[ˈeksəsaɪz]', 'example': 'I exercise every morning.', 'part_of_speech': 'noun'},
                        {'word': 'doctor', 'translation': 'врач', 'transcription': '[ˈdɒktə]', 'example': 'You should see a doctor.', 'part_of_speech': 'noun'},
                        {'word': 'medicine', 'translation': 'лекарство', 'transcription': '[ˈmedsn]', 'example': 'Take this medicine.', 'part_of_speech': 'noun'},
                        {'word': 'fever', 'translation': 'температура', 'transcription': '[ˈfiːvə]', 'example': 'I have a high fever.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Education and Learning',
                    'content': '''<h1>Lesson 3: Education and Learning</h1>
                    
                    <h2>📚 Education System</h2>
                    <ul>
                        <li>school - школа</li>
                        <li>university - университет</li>
                        <li>college - колледж</li>
                        <li>student - студент</li>
                        <li>teacher - учитель</li>
                        <li>professor - профессор</li>
                        <li>degree - степень</li>
                        <li>diploma - диплом</li>
                    </ul>
                    
                    <h2>📝 Subjects</h2>
                    <ul>
                        <li>mathematics - математика</li>
                        <li>physics - физика</li>
                        <li>chemistry - химия</li>
                        <li>history - история</li>
                        <li>literature - литература</li>
                        <li>languages - языки</li>
                    </ul>
                    
                    <h2>🗣️ Talking about Education</h2>
                    <div class="dialogue">
                        <p><strong>Alex:</strong> What do you study?</p>
                        <p><strong>Maria:</strong> I'm studying medicine at university.</p>
                        <p><strong>Alex:</strong> That sounds difficult. How long is the course?</p>
                        <p><strong>Maria:</strong> It's six years. After that, I want to specialize in pediatrics.</p>
                    </div>''',
                    'words': [
                        {'word': 'school', 'translation': 'школа', 'transcription': '[skuːl]', 'example': 'Children go to school.', 'part_of_speech': 'noun'},
                        {'word': 'university', 'translation': 'университет', 'transcription': '[ˌjuːnɪˈvɜːsəti]', 'example': 'She studies at university.', 'part_of_speech': 'noun'},
                        {'word': 'student', 'translation': 'студент', 'transcription': '[ˈstjuːdnt]', 'example': 'He is a good student.', 'part_of_speech': 'noun'},
                        {'word': 'study', 'translation': 'учиться', 'transcription': '[ˈstʌdi]', 'example': 'I study every day.', 'part_of_speech': 'verb'},
                        {'word': 'exam', 'translation': 'экзамен', 'transcription': '[ɪɡˈzæm]', 'example': 'I passed my exam.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Technology and Internet',
                    'content': '''<h1>Lesson 4: Technology and Internet</h1>
                    
                    <h2>💻 Technology Vocabulary</h2>
                    <ul>
                        <li>computer - компьютер</li>
                        <li>laptop - ноутбук</li>
                        <li>smartphone - смартфон</li>
                        <li>tablet - планшет</li>
                        <li>internet - интернет</li>
                        <li>website - вебсайт</li>
                        <li>app - приложение</li>
                        <li>software - программное обеспечение</li>
                    </ul>
                    
                    <h2>🌐 Internet Activities</h2>
                    <ul>
                        <li>browse the internet - сидеть в интернете</li>
                        <li>send an email - отправить email</li>
                        <li>social media - соцсети</li>
                        <li>download - скачать</li>
                        <li>upload - загрузить</li>
                        <li>stream - стримить</li>
                    </ul>
                    
                    <h2>🗣️ Dialogue about Technology</h2>
                    <div class="dialogue">
                        <p><strong>John:</strong> I just bought a new smartphone.</p>
                        <p><strong>Sarah:</strong> Which model did you get?</p>
                        <p><strong>John:</strong> The latest iPhone. The camera is amazing!</p>
                        <p><strong>Sarah:</strong> I prefer Android phones. They're more customizable.</p>
                    </div>''',
                    'words': [
                        {'word': 'computer', 'translation': 'компьютер', 'transcription': '[kəmˈpjuːtə]', 'example': 'I work on my computer.', 'part_of_speech': 'noun'},
                        {'word': 'internet', 'translation': 'интернет', 'transcription': '[ˈɪntənet]', 'example': 'The internet is fast.', 'part_of_speech': 'noun'},
                        {'word': 'email', 'translation': 'электронная почта', 'transcription': '[ˈiːmeɪl]', 'example': 'Send me an email.', 'part_of_speech': 'noun'},
                        {'word': 'phone', 'translation': 'телефон', 'transcription': '[fəʊn]', 'example': 'My phone is ringing.', 'part_of_speech': 'noun'},
                        {'word': 'app', 'translation': 'приложение', 'transcription': '[æp]', 'example': 'I downloaded a new app.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Environment and Nature',
                    'content': '''<h1>Lesson 5: Environment and Nature</h1>
                    
                    <h2>🌍 Environmental Issues</h2>
                    <ul>
                        <li>pollution - загрязнение</li>
                        <li>climate change - изменение климата</li>
                        <li>global warming - глобальное потепление</li>
                        <li>recycling - переработка</li>
                        <li>conservation - сохранение</li>
                        <li>sustainable - устойчивый</li>
                    </ul>
                    
                    <h2>🌿 Nature Vocabulary</h2>
                    <ul>
                        <li>forest - лес</li>
                        <li>ocean - океан</li>
                        <li>mountain - гора</li>
                        <li>river - река</li>
                        <li>lake - озеро</li>
                        <li>animal - животное</li>
                        <li>plant - растение</li>
                    </ul>
                    
                    <h2>🗣️ Discussing Environment</h2>
                    <div class="dialogue">
                        <p><strong>Emma:</strong> I'm worried about climate change.</p>
                        <p><strong>David:</strong> Me too. We need to protect our planet.</p>
                        <p><strong>Emma:</strong> I try to recycle and reduce plastic use.</p>
                        <p><strong>David:</strong> That's great. Small actions make a big difference.</p>
                    </div>''',
                    'words': [
                        {'word': 'environment', 'translation': 'окружающая среда', 'transcription': '[ɪnˈvaɪrənmənt]', 'example': 'We must protect the environment.', 'part_of_speech': 'noun'},
                        {'word': 'nature', 'translation': 'природа', 'transcription': '[ˈneɪtʃə]', 'example': 'I love spending time in nature.', 'part_of_speech': 'noun'},
                        {'word': 'pollution', 'translation': 'загрязнение', 'transcription': '[pəˈluːʃn]', 'example': 'Pollution is a serious problem.', 'part_of_speech': 'noun'},
                        {'word': 'recycle', 'translation': 'перерабатывать', 'transcription': '[ˌriːˈsaɪkl]', 'example': 'We should recycle more.', 'part_of_speech': 'verb'},
                        {'word': 'forest', 'translation': 'лес', 'transcription': '[ˈfɒrɪst]', 'example': 'The forest is beautiful.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'B2': [
                {
                    'title': 'Business and Negotiations',
                    'content': '''<h1>Lesson 1: Business and Negotiations</h1>
                    
                    <h2>💼 Business Vocabulary</h2>
                    <ul>
                        <li>negotiation - переговоры</li>
                        <li>contract - контракт</li>
                        <li>agreement - соглашение</li>
                        <li>proposal - предложение</li>
                        <li>deadline - срок</li>
                        <li>budget - бюджет</li>
                        <li>investment - инвестиция</li>
                        <li>profit - прибыль</li>
                    </ul>
                    
                    <h2>📊 Business Phrases</h2>
                    <ul>
                        <li>reach an agreement - достичь соглашения</li>
                        <li>sign a contract - подписать контракт</li>
                        <li>meet the deadline - уложиться в срок</li>
                        <li>negotiate terms - обсуждать условия</li>
                        <li>close a deal - заключить сделку</li>
                    </ul>
                    
                    <h2>🗣️ Business Meeting Dialogue</h2>
                    <div class="dialogue">
                        <p><strong>Mr. Smith:</strong> Thank you for coming today. Let's discuss the contract.</p>
                        <p><strong>Ms. Johnson:</strong> We've reviewed your proposal and have some concerns about the payment terms.</p>
                        <p><strong>Mr. Smith:</strong> What would you suggest?</p>
                        <p><strong>Ms. Johnson:</strong> We'd prefer a 50% upfront payment and 50% upon completion.</p>
                        <p><strong>Mr. Smith:</strong> That could work. Let's negotiate the details.</p>
                    </div>''',
                    'words': [
                        {'word': 'business', 'translation': 'бизнес', 'transcription': '[ˈbɪznəs]', 'example': 'He works in international business.', 'part_of_speech': 'noun'},
                        {'word': 'contract', 'translation': 'контракт', 'transcription': '[ˈkɒntrækt]', 'example': 'We signed a contract yesterday.', 'part_of_speech': 'noun'},
                        {'word': 'negotiation', 'translation': 'переговоры', 'transcription': '[nɪˌɡəʊʃiˈeɪʃn]', 'example': 'The negotiation was successful.', 'part_of_speech': 'noun'},
                        {'word': 'deadline', 'translation': 'крайний срок', 'transcription': '[ˈdedlaɪn]', 'example': 'The deadline is next Friday.', 'part_of_speech': 'noun'},
                        {'word': 'investment', 'translation': 'инвестиция', 'transcription': '[ɪnˈvestmənt]', 'example': 'It\'s a good investment.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Media and Communication',
                    'content': '''<h1>Lesson 2: Media and Communication</h1>
                    
                    <h2>📱 Media Types</h2>
                    <ul>
                        <li>social media - соцсети</li>
                        <li>news - новости</li>
                        <li>television - телевидение</li>
                        <li>radio - радио</li>
                        <li>podcast - подкаст</li>
                        <li>blog - блог</li>
                    </ul>
                    
                    <h2>🗞️ Journalism Vocabulary</h2>
                    <ul>
                        <li>journalist - журналист</li>
                        <li>article - статья</li>
                        <li>interview - интервью</li>
                        <li>headline - заголовок</li>
                        <li>source - источник</li>
                        <li>reporter - репортер</li>
                    </ul>
                    
                    <h2>🗣️ Discussing Media</h2>
                    <div class="dialogue">
                        <p><strong>Anna:</strong> Did you see the news today?</p>
                        <p><strong>Tom:</strong> No, I get my news from social media now.</p>
                        <p><strong>Anna:</strong> Be careful, there's a lot of fake news online.</p>
                        <p><strong>Tom:</strong> You're right. I should check multiple sources.</p>
                    </div>''',
                    'words': [
                        {'word': 'media', 'translation': 'медиа', 'transcription': '[ˈmiːdiə]', 'example': 'The media covers important events.', 'part_of_speech': 'noun'},
                        {'word': 'news', 'translation': 'новости', 'transcription': '[njuːz]', 'example': 'Good news travels fast.', 'part_of_speech': 'noun'},
                        {'word': 'interview', 'translation': 'интервью', 'transcription': '[ˈɪntəvjuː]', 'example': 'She gave an interview.', 'part_of_speech': 'noun'},
                        {'word': 'article', 'translation': 'статья', 'transcription': '[ˈɑːtɪkl]', 'example': 'I read an interesting article.', 'part_of_speech': 'noun'},
                        {'word': 'journalist', 'translation': 'журналист', 'transcription': '[ˈdʒɜːnəlɪst]', 'example': 'He works as a journalist.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Art and Culture',
                    'content': '''<h1>Lesson 3: Art and Culture</h1>
                    
                    <h2>🎨 Art Forms</h2>
                    <ul>
                        <li>painting - живопись</li>
                        <li>sculpture - скульптура</li>
                        <li>photography - фотография</li>
                        <li>architecture - архитектура</li>
                        <li>theater - театр</li>
                        <li>cinema - кино</li>
                    </ul>
                    
                    <h2>🎭 Cultural Events</h2>
                    <ul>
                        <li>exhibition - выставка</li>
                        <li>concert - концерт</li>
                        <li>festival - фестиваль</li>
                        <li>performance - представление</li>
                        <li>museum - музей</li>
                    </ul>
                    
                    <h2>🗣️ Talking about Art</h2>
                    <div class="dialogue">
                        <p><strong>Maria:</strong> Have you been to the new art exhibition?</p>
                        <p><strong>John:</strong> Not yet. Is it good?</p>
                        <p><strong>Maria:</strong> It's fantastic! Modern art from local artists.</p>
                        <p><strong>John:</strong> I prefer classical paintings, but I'll check it out.</p>
                    </div>''',
                    'words': [
                        {'word': 'art', 'translation': 'искусство', 'transcription': '[ɑːt]', 'example': 'I love modern art.', 'part_of_speech': 'noun'},
                        {'word': 'culture', 'translation': 'культура', 'transcription': '[ˈkʌltʃə]', 'example': 'Different countries have different cultures.', 'part_of_speech': 'noun'},
                        {'word': 'museum', 'translation': 'музей', 'transcription': '[mjuˈziːəm]', 'example': 'The museum is closed on Mondays.', 'part_of_speech': 'noun'},
                        {'word': 'painting', 'translation': 'картина', 'transcription': '[ˈpeɪntɪŋ]', 'example': 'This painting is beautiful.', 'part_of_speech': 'noun'},
                        {'word': 'artist', 'translation': 'художник', 'transcription': '[ˈɑːtɪst]', 'example': 'She is a talented artist.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Science and Research',
                    'content': '''<h1>Lesson 4: Science and Research</h1>
                    
                    <h2>🔬 Scientific Fields</h2>
                    <ul>
                        <li>physics - физика</li>
                        <li>chemistry - химия</li>
                        <li>biology - биология</li>
                        <li>astronomy - астрономия</li>
                        <li>genetics - генетика</li>
                        <li>neuroscience - нейронаука</li>
                    </ul>
                    
                    <h2>📊 Research Vocabulary</h2>
                    <ul>
                        <li>research - исследование</li>
                        <li>experiment - эксперимент</li>
                        <li>laboratory - лаборатория</li>
                        <li>data - данные</li>
                        <li>analysis - анализ</li>
                        <li>discovery - открытие</li>
                    </ul>
                    
                    <h2>🗣️ Scientific Discussion</h2>
                    <div class="dialogue">
                        <p><strong>Prof. Brown:</strong> Our research shows promising results.</p>
                        <p><strong>Dr. Lee:</strong> The data suggests a breakthrough in cancer treatment.</p>
                        <p><strong>Prof. Brown:</strong> We need to conduct more experiments.</p>
                        <p><strong>Dr. Lee:</strong> Absolutely. Science requires patience and precision.</p>
                    </div>''',
                    'words': [
                        {'word': 'science', 'translation': 'наука', 'transcription': '[ˈsaɪəns]', 'example': 'Science explains natural phenomena.', 'part_of_speech': 'noun'},
                        {'word': 'research', 'translation': 'исследование', 'transcription': '[rɪˈsɜːtʃ]', 'example': 'She conducts medical research.', 'part_of_speech': 'noun'},
                        {'word': 'experiment', 'translation': 'эксперимент', 'transcription': '[ɪkˈsperɪmənt]', 'example': 'The experiment was successful.', 'part_of_speech': 'noun'},
                        {'word': 'laboratory', 'translation': 'лаборатория', 'transcription': '[ləˈbɒrətri]', 'example': 'Scientists work in a laboratory.', 'part_of_speech': 'noun'},
                        {'word': 'data', 'translation': 'данные', 'transcription': '[ˈdeɪtə]', 'example': 'We collected data for analysis.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Politics and Society',
                    'content': '''<h1>Lesson 5: Politics and Society</h1>
                    
                    <h2>🏛️ Government Vocabulary</h2>
                    <ul>
                        <li>government - правительство</li>
                        <li>parliament - парламент</li>
                        <li>president - президент</li>
                        <li>prime minister - премьер-министр</li>
                        <li>minister - министр</li>
                        <li>election - выборы</li>
                    </ul>
                    
                    <h2>🗳️ Political Terms</h2>
                    <ul>
                        <li>democracy - демократия</li>
                        <li>republic - республика</li>
                        <li>monarchy - монархия</li>
                        <li>policy - политика</li>
                        <li>law - закон</li>
                        <li>rights - права</li>
                    </ul>
                    
                    <h2>🗣️ Discussing Politics</h2>
                    <div class="dialogue">
                        <p><strong>Citizen:</strong> When are the next elections?</p>
                        <p><strong>Official:</strong> They're scheduled for next month.</p>
                        <p><strong>Citizen:</strong> I'm concerned about the new tax policy.</p>
                        <p><strong>Official:</strong> You should vote. Every voice matters.</p>
                    </div>''',
                    'words': [
                        {'word': 'politics', 'translation': 'политика', 'transcription': '[ˈpɒlətɪks]', 'example': 'He is interested in politics.', 'part_of_speech': 'noun'},
                        {'word': 'government', 'translation': 'правительство', 'transcription': '[ˈɡʌvənmənt]', 'example': 'The government makes laws.', 'part_of_speech': 'noun'},
                        {'word': 'election', 'translation': 'выборы', 'transcription': '[ɪˈlekʃn]', 'example': 'The election results are in.', 'part_of_speech': 'noun'},
                        {'word': 'law', 'translation': 'закон', 'transcription': '[lɔː]', 'example': 'Everyone must follow the law.', 'part_of_speech': 'noun'},
                        {'word': 'rights', 'translation': 'права', 'transcription': '[raɪts]', 'example': 'Human rights are important.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'C1': [
                {
                    'title': 'Academic Writing',
                    'content': '''<h1>Lesson 1: Academic Writing</h1>
                    
                    <h2>📝 Academic Style</h2>
                    <ul>
                        <li>formal language - формальный язык</li>
                        <li>objective tone - объективный тон</li>
                        <li>precise vocabulary - точная лексика</li>
                        <li>complex sentences - сложные предложения</li>
                        <li>passive voice - пассивный залог</li>
                    </ul>
                    
                    <h2>📚 Research Paper Structure</h2>
                    <ul>
                        <li>abstract - аннотация</li>
                        <li>introduction - введение</li>
                        <li>literature review - обзор литературы</li>
                        <li>methodology - методология</li>
                        <li>results - результаты</li>
                        <li>discussion - обсуждение</li>
                        <li>conclusion - заключение</li>
                        <li>bibliography - библиография</li>
                    </ul>
                    
                    <h2>📖 Academic Phrases</h2>
                    <ul>
                        <li>According to Smith (2020)... - Согласно Смиту (2020)...</li>
                        <li>It can be argued that... - Можно утверждать, что...</li>
                        <li>The data suggests that... - Данные предполагают, что...</li>
                        <li>Further research is needed... - Необходимы дальнейшие исследования...</li>
                    </ul>''',
                    'words': [
                        {'word': 'research', 'translation': 'исследование', 'transcription': '[rɪˈsɜːtʃ]', 'example': 'Her research focuses on climate change.', 'part_of_speech': 'noun'},
                        {'word': 'analysis', 'translation': 'анализ', 'transcription': '[əˈnæləsɪs]', 'example': 'The analysis reveals interesting patterns.', 'part_of_speech': 'noun'},
                        {'word': 'methodology', 'translation': 'методология', 'transcription': '[ˌmeθəˈdɒlədʒi]', 'example': 'The methodology is clearly explained.', 'part_of_speech': 'noun'},
                        {'word': 'conclusion', 'translation': 'заключение', 'transcription': '[kənˈkluːʒn]', 'example': 'The conclusion summarizes the findings.', 'part_of_speech': 'noun'},
                        {'word': 'hypothesis', 'translation': 'гипотеза', 'transcription': '[haɪˈpɒθəsɪs]', 'example': 'The hypothesis was confirmed.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Idioms and Expressions',
                    'content': '''<h1>Lesson 2: Idioms and Expressions</h1>
                    
                    <h2>🌟 Common Idioms</h2>
                    <table class="table">
                        <tr><th>Idiom</th><th>Meaning</th><th>Example</th></tr>
                        <tr><td>break the ice</td><td>начать разговор</td><td>He told a joke to break the ice.</td></tr>
                        <tr><td>cost an arm and a leg</td><td>очень дорого</td><td>The new car cost an arm and a leg.</td></tr>
                        <tr><td>piece of cake</td><td>легко</td><td>The exam was a piece of cake.</td></tr>
                        <tr><td>once in a blue moon</td><td>очень редко</td><td>I see him once in a blue moon.</td></tr>
                        <tr><td>hit the nail on the head</td><td>попасть в точку</td><td>You hit the nail on the head with that idea.</td></tr>
                    </table>
                    
                    <h2>🗣️ Using Idioms in Conversation</h2>
                    <div class="dialogue">
                        <p><strong>Emma:</strong> How was your presentation?</p>
                        <p><strong>James:</strong> It was a piece of cake! I was nervous at first, but telling a joke helped break the ice.</p>
                        <p><strong>Emma:</strong> Great! Did you get any feedback?</p>
                        <p><strong>James:</strong> My boss said I hit the nail on the head with the budget proposal.</p>
                    </div>''',
                    'words': [
                        {'word': 'idiom', 'translation': 'идиома', 'transcription': '[ˈɪdiəm]', 'example': 'Learning idioms makes you sound natural.', 'part_of_speech': 'noun'},
                        {'word': 'break the ice', 'translation': 'начать разговор', 'example': 'I told a joke to break the ice.', 'part_of_speech': 'phrase'},
                        {'word': 'piece of cake', 'translation': 'легко', 'example': 'The test was a piece of cake.', 'part_of_speech': 'phrase'},
                        {'word': 'cost an arm and a leg', 'translation': 'очень дорого', 'example': 'This watch cost an arm and a leg.', 'part_of_speech': 'phrase'},
                        {'word': 'once in a blue moon', 'translation': 'очень редко', 'example': 'I travel once in a blue moon.', 'part_of_speech': 'phrase'}
                    ]
                },
                {
                    'title': 'Professional Communication',
                    'content': '''<h1>Lesson 3: Professional Communication</h1>
                    
                    <h2>📧 Email Writing</h2>
                    <h3>Formal Email Structure:</h3>
                    <ul>
                        <li>Subject line - четкая тема</li>
                        <li>Salutation - Dear Mr./Ms. [Last Name]</li>
                        <li>Introduction - I am writing to inquire about...</li>
                        <li>Body - подробное изложение</li>
                        <li>Closing - I look forward to hearing from you</li>
                        <li>Signature - Sincerely, [Your Name]</li>
                    </ul>
                    
                    <h2>🗣️ Professional Phrases</h2>
                    <ul>
                        <li>I am writing in reference to...</li>
                        <li>Please find attached...</li>
                        <li>Thank you for your prompt response</li>
                        <li>I would appreciate it if you could...</li>
                        <li>Please let me know if you need any further information</li>
                    </ul>
                    
                    <h2>📝 Example Email</h2>
                    <div class="email">
                        <p><strong>Subject:</strong> Meeting Request - Project Discussion</p>
                        <p>Dear Mr. Johnson,</p>
                        <p>I am writing to schedule a meeting to discuss the upcoming project deadline. Would it be possible to meet next Tuesday at 2 PM?</p>
                        <p>Please let me know if this time works for you.</p>
                        <p>Best regards,<br>Sarah Thompson</p>
                    </div>''',
                    'words': [
                        {'word': 'professional', 'translation': 'профессиональный', 'transcription': '[prəˈfeʃənl]', 'example': 'Keep a professional tone.', 'part_of_speech': 'adjective'},
                        {'word': 'communication', 'translation': 'коммуникация', 'transcription': '[kəˌmjuːnɪˈkeɪʃn]', 'example': 'Good communication is key.', 'part_of_speech': 'noun'},
                        {'word': 'meeting', 'translation': 'встреча', 'transcription': '[ˈmiːtɪŋ]', 'example': 'Schedule a meeting.', 'part_of_speech': 'noun'},
                        {'word': 'request', 'translation': 'запрос', 'transcription': '[rɪˈkwest]', 'example': 'Submit a request.', 'part_of_speech': 'noun'},
                        {'word': 'proposal', 'translation': 'предложение', 'transcription': '[prəˈpəʊzl]', 'example': 'Send a proposal.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Literature Analysis',
                    'content': '''<h1>Lesson 4: Literature Analysis</h1>
                    
                    <h2>📖 Literary Terms</h2>
                    <ul>
                        <li>metaphor - метафора</li>
                        <li>simile - сравнение</li>
                        <li>symbolism - символизм</li>
                        <li>theme - тема</li>
                        <li>character development - развитие персонажа</li>
                        <li>plot - сюжет</li>
                        <li>setting - место действия</li>
                        <li>narrator - рассказчик</li>
                    </ul>
                    
                    <h2>🎭 Literary Analysis Phrases</h2>
                    <ul>
                        <li>The author employs symbolism to convey...</li>
                        <li>The protagonist undergoes significant development...</li>
                        <li>The setting reflects the characters' emotions...</li>
                        <li>The theme of love is explored through...</li>
                    </ul>
                    
                    <h2>📝 Analysis Example</h2>
                    <p>In Shakespeare's "Romeo and Juliet," light and dark imagery serves as a metaphor for the lovers' forbidden relationship. Juliet is often associated with light, described as the sun, while their meetings occur in darkness, symbolizing the secret nature of their love.</p>''',
                    'words': [
                        {'word': 'literature', 'translation': 'литература', 'transcription': '[ˈlɪtrətʃə]', 'example': 'Classic literature is timeless.', 'part_of_speech': 'noun'},
                        {'word': 'metaphor', 'translation': 'метафора', 'transcription': '[ˈmetəfə]', 'example': 'The poem uses metaphor.', 'part_of_speech': 'noun'},
                        {'word': 'theme', 'translation': 'тема', 'transcription': '[θiːm]', 'example': 'The main theme is love.', 'part_of_speech': 'noun'},
                        {'word': 'character', 'translation': 'персонаж', 'transcription': '[ˈkærəktə]', 'example': 'The main character is complex.', 'part_of_speech': 'noun'},
                        {'word': 'symbolism', 'translation': 'символизм', 'transcription': '[ˈsɪmbəlɪzəm]', 'example': 'The novel is rich in symbolism.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Debate and Argumentation',
                    'content': '''<h1>Lesson 5: Debate and Argumentation</h1>
                    
                    <h2>🗣️ Argument Structure</h2>
                    <ul>
                        <li>claim - утверждение</li>
                        <li>evidence - доказательство</li>
                        <li>counter-argument - контраргумент</li>
                        <li>rebuttal - опровержение</li>
                        <li>conclusion - заключение</li>
                    </ul>
                    
                    <h2>🎯 Persuasive Language</h2>
                    <ul>
                        <li>I firmly believe that...</li>
                        <li>The evidence clearly shows...</li>
                        <li>It is undeniable that...</li>
                        <li>One could argue that, however...</li>
                        <li>While it's true that..., we must consider...</li>
                    </ul>
                    
                    <h2>🗣️ Debate Example</h2>
                    <div class="debate">
                        <p><strong>Speaker 1:</strong> I believe renewable energy is essential for our future. The evidence shows that fossil fuels are running out and causing climate change.</p>
                        <p><strong>Speaker 2:</strong> While renewable energy is important, we must consider the economic impact. Many jobs depend on the fossil fuel industry.</p>
                        <p><strong>Speaker 1:</strong> That's true, but the renewable sector creates even more jobs. Furthermore, the cost of inaction on climate change is far greater.</p>
                    </div>''',
                    'words': [
                        {'word': 'debate', 'translation': 'дебаты', 'transcription': '[dɪˈbeɪt]', 'example': 'We had a heated debate.', 'part_of_speech': 'noun'},
                        {'word': 'argument', 'translation': 'аргумент', 'transcription': '[ˈɑːɡjumənt]', 'example': 'Present your argument.', 'part_of_speech': 'noun'},
                        {'word': 'evidence', 'translation': 'доказательство', 'transcription': '[ˈevɪdəns]', 'example': 'Evidence supports the claim.', 'part_of_speech': 'noun'},
                        {'word': 'persuasive', 'translation': 'убедительный', 'transcription': '[pəˈsweɪsɪv]', 'example': 'Use persuasive language.', 'part_of_speech': 'adjective'},
                        {'word': 'conclusion', 'translation': 'заключение', 'transcription': '[kənˈkluːʒn]', 'example': 'In conclusion, I argue that...', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_spanish_lessons(self, level):
        """Уроки для испанского языка"""
        lessons = {
            'A1': [
                {
                    'title': 'Saludos y presentaciones',
                    'content': '''<h1>Lección 1: Saludos y presentaciones</h1>
                    
                    <h2>📚 Objetivos de la lección</h2>
                    <ul>
                        <li>Aprender a saludar en diferentes momentos del día</li>
                        <li>Presentarse y conocer a otras personas</li>
                        <li>Preguntar y responder sobre el nombre y origen</li>
                    </ul>
                    
                    <h2>👋 Saludos básicos</h2>
                    <div class="phrase-box">
                        <p><strong>¡Hola!</strong> - Привет!</p>
                        <p><strong>Buenos días</strong> - Доброе утро</p>
                        <p><strong>Buenas tardes</strong> - Добрый день</p>
                        <p><strong>Buenas noches</strong> - Добрый вечер / Спокойной ночи</p>
                    </div>
                    
                    <h2>🗣️ Diálogo</h2>
                    <div class="dialogue">
                        <p><strong>Carlos:</strong> ¡Hola! Me llamo Carlos. ¿Y tú? ¿Cómo te llamas?</p>
                        <p><strong>Ana:</strong> ¡Hola, Carlos! Me llamo Ana. Mucho gusto.</p>
                        <p><strong>Carlos:</strong> Mucho gusto, Ana. ¿De dónde eres?</p>
                        <p><strong>Ana:</strong> Soy de España. ¿Y tú?</p>
                        <p><strong>Carlos:</strong> Soy de México.</p>
                    </div>
                    
                    <h2>🔑 Frases clave</h2>
                    <ul>
                        <li><strong>¿Cómo te llamas?</strong> - Как тебя зовут?</li>
                        <li><strong>Me llamo...</strong> - Меня зовут...</li>
                        <li><strong>Mucho gusto</strong> - Приятно познакомиться</li>
                        <li><strong>¿De dónde eres?</strong> - Откуда ты?</li>
                        <li><strong>Soy de...</strong> - Я из...</li>
                    </ul>
                    
                    <div class="tip">
                        <h3>💡 Совет по произношению:</h3>
                        <p>В испанском буква "h" всегда немая. ¡Hola! произносится как "ола". Буква "ll" произносится как "й" или "ль" в разных странах.</p>
                    </div>''',
                    'words': [
                        {'word': 'hola', 'translation': 'привет', 'transcription': '[ˈola]', 'example': '¡Hola! ¿Cómo estás?', 'part_of_speech': 'interjection'},
                        {'word': 'adiós', 'translation': 'до свидания', 'transcription': '[aˈðjos]', 'example': '¡Adiós, hasta mañana!', 'part_of_speech': 'interjection'},
                        {'word': 'gracias', 'translation': 'спасибо', 'transcription': '[ˈɡɾaθjas]', 'example': 'Muchas gracias por tu ayuda.', 'part_of_speech': 'noun'},
                        {'word': 'nombre', 'translation': 'имя', 'transcription': '[ˈnombɾe]', 'example': 'Mi nombre es María.', 'part_of_speech': 'noun'},
                        {'word': 'amigo', 'translation': 'друг', 'transcription': '[aˈmiɣo]', 'example': 'Él es mi amigo.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'La familia',
                    'content': '''<h1>Lección 2: La familia</h1>
                    
                    <h2>👨‍👩‍👧‍👦 Miembros de la familia</h2>
                    <table class="table">
                        <tr><th>Español</th><th>Русский</th></tr>
                        <tr><td>madre</td><td>мама</td></tr>
                        <tr><td>padre</td><td>папа</td></tr>
                        <tr><td>hermano</td><td>брат</td></tr>
                        <tr><td>hermana</td><td>сестра</td></tr>
                        <tr><td>abuelo</td><td>дедушка</td></tr>
                        <tr><td>abuela</td><td>бабушка</td></tr>
                        <tr><td>tío</td><td>дядя</td></tr>
                        <tr><td>tía</td><td>тетя</td></tr>
                    </table>
                    
                    <h2>📝 Ejemplo</h2>
                    <p>Mi familia es grande. Tengo una madre, un padre, dos hermanos y una hermana. Mi madre se llama Elena y mi padre se llama José. Mis abuelos viven en Madrid.</p>''',
                    'words': [
                        {'word': 'familia', 'translation': 'семья', 'transcription': '[faˈmilja]', 'example': 'Mi familia es muy unida.', 'part_of_speech': 'noun'},
                        {'word': 'madre', 'translation': 'мама', 'transcription': '[ˈmaðɾe]', 'example': 'Mi madre cocina muy bien.', 'part_of_speech': 'noun'},
                        {'word': 'padre', 'translation': 'папа', 'transcription': '[ˈpaðɾe]', 'example': 'Mi padre trabaja en una oficina.', 'part_of_speech': 'noun'},
                        {'word': 'hermano', 'translation': 'брат', 'transcription': '[erˈmano]', 'example': 'Tengo un hermano mayor.', 'part_of_speech': 'noun'},
                        {'word': 'hermana', 'translation': 'сестра', 'transcription': '[erˈmana]', 'example': 'Mi hermana es estudiante.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Números y edad',
                    'content': '''<h1>Lección 3: Números y edad</h1>
                    
                    <h2>🔢 Números 1-20</h2>
                    <p>1 - uno, 2 - dos, 3 - tres, 4 - cuatro, 5 - cinco, 6 - seis, 7 - siete, 8 - ocho, 9 - nueve, 10 - diez</p>
                    <p>11 - once, 12 - doce, 13 - trece, 14 - catorce, 15 - quince, 16 - dieciséis, 17 - diecisiete, 18 - dieciocho, 19 - diecinueve, 20 - veinte</p>
                    
                    <h2>🎂 Hablar de la edad</h2>
                    <p><strong>¿Cuántos años tienes?</strong> - Сколько тебе лет?</p>
                    <p><strong>Tengo [edad] años.</strong> - Мне [возраст] лет.</p>''',
                    'words': [
                        {'word': 'uno', 'translation': 'один', 'transcription': '[ˈuno]', 'example': 'Tengo un perro.', 'part_of_speech': 'numeral'},
                        {'word': 'dos', 'translation': 'два', 'transcription': '[dos]', 'example': 'Dos hermanos.', 'part_of_speech': 'numeral'},
                        {'word': 'tres', 'translation': 'три', 'transcription': '[tɾes]', 'example': 'Tres gatos.', 'part_of_speech': 'numeral'},
                        {'word': 'edad', 'translation': 'возраст', 'transcription': '[eˈðað]', 'example': '¿Cuál es tu edad?', 'part_of_speech': 'noun'},
                        {'word': 'años', 'translation': 'лет', 'transcription': '[ˈaɲos]', 'example': 'Tengo 25 años.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Colores',
                    'content': '''<h1>Lección 4: Colores</h1>
                    
                    <h2>🎨 Colores básicos</h2>
                    <ul>
                        <li><span style="color: red;">rojo</span> - красный</li>
                        <li><span style="color: blue;">azul</span> - синий</li>
                        <li><span style="color: green;">verde</span> - зеленый</li>
                        <li><span style="color: yellow;">amarillo</span> - желтый</li>
                        <li><span style="color: black;">negro</span> - черный</li>
                        <li><span style="color: white;">blanco</span> - белый</li>
                        <li>naranja - оранжевый</li>
                        <li>morado - фиолетовый</li>
                        <li>rosa - розовый</li>
                        <li>marrón - коричневый</li>
                    </ul>''',
                    'words': [
                        {'word': 'rojo', 'translation': 'красный', 'transcription': '[ˈroxo]', 'example': 'La manzana es roja.', 'part_of_speech': 'adjective'},
                        {'word': 'azul', 'translation': 'синий', 'transcription': '[aˈθul]', 'example': 'El cielo es azul.', 'part_of_speech': 'adjective'},
                        {'word': 'verde', 'translation': 'зеленый', 'transcription': '[ˈberðe]', 'example': 'La hierba es verde.', 'part_of_speech': 'adjective'},
                        {'word': 'amarillo', 'translation': 'желтый', 'transcription': '[amaˈɾiʎo]', 'example': 'El sol es amarillo.', 'part_of_speech': 'adjective'},
                        {'word': 'negro', 'translation': 'черный', 'transcription': '[ˈneɣɾo]', 'example': 'Mi coche es negro.', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': 'Comida y bebida',
                    'content': '''<h1>Lección 5: Comida y bebida</h1>
                    
                    <h2>🍎 Vocabulario de comida</h2>
                    <ul>
                        <li>pan - хлеб</li>
                        <li>mantequilla - масло</li>
                        <li>queso - сыр</li>
                        <li>leche - молоко</li>
                        <li>huevos - яйца</li>
                        <li>carne - мясо</li>
                        <li>pescado - рыба</li>
                        <li>verduras - овощи</li>
                        <li>fruta - фрукты</li>
                    </ul>
                    
                    <h2>☕ Bebidas</h2>
                    <ul>
                        <li>agua - вода</li>
                        <li>café - кофе</li>
                        <li>té - чай</li>
                        <li>zumo - сок</li>
                    </ul>''',
                    'words': [
                        {'word': 'pan', 'translation': 'хлеб', 'transcription': '[pan]', 'example': 'Como pan todos los días.', 'part_of_speech': 'noun'},
                        {'word': 'agua', 'translation': 'вода', 'transcription': '[ˈaɣwa]', 'example': 'Bebo agua con gas.', 'part_of_speech': 'noun'},
                        {'word': 'café', 'translation': 'кофе', 'transcription': '[kaˈfe]', 'example': 'Tomo café por la mañana.', 'part_of_speech': 'noun'},
                        {'word': 'fruta', 'translation': 'фрукты', 'transcription': '[ˈfruta]', 'example': 'La fruta es saludable.', 'part_of_speech': 'noun'},
                        {'word': 'restaurante', 'translation': 'ресторан', 'transcription': '[restaʊˈɾante]', 'example': 'Vamos a un restaurante.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'A2': [
                                {
                    'title': 'Trabajo y profesiones',
                    'content': '''<h1>Lección 1: Trabajo y profesiones</h1>
                    
                    <h2>👔 Profesiones comunes</h2>
                    <table class="table">
                        <tr><th>Español</th><th>Русский</th></tr>
                        <tr><td>profesor / maestro</td><td>учитель</td></tr>
                        <tr><td>médico / doctor</td><td>врач</td></tr>
                        <tr><td>ingeniero</td><td>инженер</td></tr>
                        <tr><td>abogado</td><td>юрист</td></tr>
                        <tr><td>contador</td><td>бухгалтер</td></tr>
                        <tr><td>programador</td><td>программист</td></tr>
                        <tr><td>gerente</td><td>менеджер</td></tr>
                        <tr><td>vendedor</td><td>продавец</td></tr>
                    </table>
                    
                    <h2>🗣️ Diálogo sobre el trabajo</h2>
                    <div class="dialogue">
                        <p><strong>Tomás:</strong> ¿A qué te dedicas?</p>
                        <p><strong>Ana:</strong> Soy profesora. Trabajo en una escuela. ¿Y tú?</p>
                        <p><strong>Tomás:</strong> Soy ingeniero. Trabajo para una empresa de construcción.</p>
                        <p><strong>Ana:</strong> ¿Te gusta tu trabajo?</p>
                        <p><strong>Tomás:</strong> Sí, me encanta. Es muy interesante.</p>
                    </div>
                    
                    <h2>📝 Vocabulario del lugar de trabajo</h2>
                    <ul>
                        <li>oficina - офис</li>
                        <li>compañero - коллега</li>
                        <li>jefe - начальник</li>
                        <li>salario - зарплата</li>
                        <li>reunión - встреча</li>
                    </ul>''',
                    'words': [
                        {'word': 'trabajo', 'translation': 'работа', 'transcription': '[tɾaˈβaxo]', 'example': 'Me gusta mi trabajo.', 'part_of_speech': 'noun'},
                        {'word': 'profesor', 'translation': 'учитель', 'transcription': '[pɾofeˈsoɾ]', 'example': 'Mi madre es profesora.', 'part_of_speech': 'noun'},
                        {'word': 'médico', 'translation': 'врач', 'transcription': '[ˈmeðiko]', 'example': 'El médico trabaja en el hospital.', 'part_of_speech': 'noun'},
                        {'word': 'oficina', 'translation': 'офис', 'transcription': '[ofiˈθina]', 'example': 'Trabajo en una oficina grande.', 'part_of_speech': 'noun'},
                        {'word': 'empresa', 'translation': 'компания', 'transcription': '[emˈpɾesa]', 'example': 'Trabajo para una empresa internacional.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Rutina diaria',
                    'content': '''<h1>Lección 2: Rutina diaria</h1>
                    
                    <h2>⏰ Rutina de la mañana</h2>
                    <ul>
                        <li>despertarse - просыпаться</li>
                        <li>levantarse - вставать</li>
                        <li>ducharse - принимать душ</li>
                        <li>cepillarse los dientes - чистить зубы</li>
                        <li>vestirse - одеваться</li>
                        <li>desayunar - завтракать</li>
                        <li>ir al trabajo - идти на работу</li>
                    </ul>
                    
                    <h2>📝 Texto de ejemplo</h2>
                    <p>Me despierto a las 7 de la mañana todos los días. Me ducho y me cepillo los dientes. Luego desayuno. Normalmente tomo café con cereales. Salgo de casa a las 8 y voy al trabajo. Empiezo a trabajar a las 9.</p>''',
                    'words': [
                        {'word': 'despertarse', 'translation': 'просыпаться', 'transcription': '[despeɾˈtaɾse]', 'example': 'Me despierto a las 7.', 'part_of_speech': 'verb'},
                        {'word': 'desayuno', 'translation': 'завтрак', 'transcription': '[desaˈʝuno]', 'example': 'El desayuno es importante.', 'part_of_speech': 'noun'},
                        {'word': 'trabajar', 'translation': 'работать', 'transcription': '[tɾaβaˈxaɾ]', 'example': 'Trabajo de lunes a viernes.', 'part_of_speech': 'verb'},
                        {'word': 'mañana', 'translation': 'утро', 'transcription': '[maˈɲana]', 'example': 'Hago ejercicio por la mañana.', 'part_of_speech': 'noun'},
                        {'word': 'noche', 'translation': 'вечер/ночь', 'transcription': '[ˈnotʃe]', 'example': 'Veo televisión por la noche.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Pasatiempos y tiempo libre',
                    'content': '''<h1>Lección 3: Pasatiempos y tiempo libre</h1>
                    
                    <h2>🎨 Pasatiempos comunes</h2>
                    <ul>
                        <li>leer - читать</li>
                        <li>ver películas - смотреть фильмы</li>
                        <li>hacer deporte - заниматься спортом</li>
                        <li>escuchar música - слушать музыку</li>
                        <li>cocinar - готовить</li>
                        <li>viajar - путешествовать</li>
                        <li>fotografía - фотография</li>
                        <li>jardinería - садоводство</li>
                    </ul>
                    
                    <h2>🗣️ Diálogo sobre pasatiempos</h2>
                    <div class="dialogue">
                        <p><strong>Miguel:</strong> ¿Qué te gusta hacer en tu tiempo libre?</p>
                        <p><strong>Laura:</strong> Me encanta leer libros y ver películas. ¿Y a ti?</p>
                        <p><strong>Miguel:</strong> Disfruto jugar al fútbol y escuchar música.</p>
                        <p><strong>Laura:</strong> ¡Qué divertido! ¿Qué tipo de música te gusta?</p>
                        <p><strong>Miguel:</strong> Me gusta el rock y la música pop.</p>
                    </div>''',
                    'words': [
                        {'word': 'hobby', 'translation': 'хобби', 'transcription': '[ˈxobi]', 'example': 'Mi hobby es la fotografía.', 'part_of_speech': 'noun'},
                        {'word': 'leer', 'translation': 'читать', 'transcription': '[leˈeɾ]', 'example': 'Leo libros todos los días.', 'part_of_speech': 'verb'},
                        {'word': 'música', 'translation': 'музыка', 'transcription': '[ˈmusika]', 'example': 'Escucho música en el coche.', 'part_of_speech': 'noun'},
                        {'word': 'deporte', 'translation': 'спорт', 'transcription': '[deˈpoɾte]', 'example': 'El fútbol es un deporte popular.', 'part_of_speech': 'noun'},
                        {'word': 'viajar', 'translation': 'путешествовать', 'transcription': '[bjaˈxaɾ]', 'example': 'Quiero viajar por el mundo.', 'part_of_speech': 'verb'}
                    ]
                },
                {
                    'title': 'Compras',
                    'content': '''<h1>Lección 4: Compras</h1>
                    
                    <h2>🛍️ Vocabulario de compras</h2>
                    <ul>
                        <li>tienda - магазин</li>
                        <li>supermercado - супермаркет</li>
                        <li>precio - цена</li>
                        <li>dinero - деньги</li>
                        <li>tarjeta de crédito - кредитная карта</li>
                        <li>efectivo - наличные</li>
                        <li>recibo - чек</li>
                    </ul>
                    
                    <h2>🗣️ Diálogo en la tienda</h2>
                    <div class="dialogue">
                        <p><strong>Vendedor:</strong> ¿Puedo ayudarle?</p>
                        <p><strong>Cliente:</strong> Sí, ¿cuánto cuesta esta camiseta?</p>
                        <p><strong>Vendedor:</strong> Cuesta 25 euros.</p>
                        <p><strong>Cliente:</strong> ¿La tiene en otro color?</p>
                        <p><strong>Vendedor:</strong> Sí, la tenemos en azul y negro.</p>
                        <p><strong>Cliente:</strong> Me llevo la azul. ¿Puedo pagar con tarjeta?</p>
                        <p><strong>Vendedor:</strong> Por supuesto. Aquí tiene su recibo.</p>
                    </div>''',
                    'words': [
                        {'word': 'tienda', 'translation': 'магазин', 'transcription': '[ˈtjenda]', 'example': 'Voy a la tienda cada fin de semana.', 'part_of_speech': 'noun'},
                        {'word': 'comprar', 'translation': 'покупать', 'transcription': '[komˈpɾaɾ]', 'example': 'Quiero comprar un móvil nuevo.', 'part_of_speech': 'verb'},
                        {'word': 'precio', 'translation': 'цена', 'transcription': '[ˈpɾeθjo]', 'example': 'El precio es muy alto.', 'part_of_speech': 'noun'},
                        {'word': 'dinero', 'translation': 'деньги', 'transcription': '[diˈneɾo]', 'example': 'No tengo suficiente dinero.', 'part_of_speech': 'noun'},
                        {'word': 'recibo', 'translation': 'чек', 'transcription': '[reˈθiβo]', 'example': 'Guarde su recibo.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'El clima y las estaciones',
                    'content': '''<h1>Lección 5: El clima y las estaciones</h1>
                    
                    <h2>☀️ Vocabulario del clima</h2>
                    <ul>
                        <li>soleado - солнечно</li>
                        <li>nublado - облачно</li>
                        <li>lluvioso - дождливо</li>
                        <li>nevado - снежно</li>
                        <li>ventoso - ветрено</li>
                        <li>calor - жарко</li>
                        <li>frío - холодно</li>
                        <li>cálido - тепло</li>
                        <li>fresco - прохладно</li>
                    </ul>
                    
                    <h2>🍂 Estaciones del año</h2>
                    <ul>
                        <li>primavera - весна</li>
                        <li>verano - лето</li>
                        <li>otoño - осень</li>
                        <li>invierno - зима</li>
                    </ul>''',
                    'words': [
                        {'word': 'clima', 'translation': 'климат', 'transcription': '[ˈklima]', 'example': 'El clima es templado.', 'part_of_speech': 'noun'},
                        {'word': 'sol', 'translation': 'солнце', 'transcription': '[sol]', 'example': 'Hace sol hoy.', 'part_of_speech': 'noun'},
                        {'word': 'lluvia', 'translation': 'дождь', 'transcription': '[ˈʎuβja]', 'example': 'La lluvia es buena para las plantas.', 'part_of_speech': 'noun'},
                        {'word': 'nieve', 'translation': 'снег', 'transcription': '[ˈnjeβe]', 'example': 'La nieve es blanca y fría.', 'part_of_speech': 'noun'},
                        {'word': 'temperatura', 'translation': 'температура', 'transcription': '[tempeɾaˈtuɾa]', 'example': 'La temperatura es agradable.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'B1': [
                {
                    'title': 'Viajes y turismo',
                    'content': '''<h1>Lección 1: Viajes y turismo</h1>
                    
                    <h2>✈️ Vocabulario de viajes</h2>
                    <ul>
                        <li>vuelo - рейс</li>
                        <li>aeropuerto - аэропорт</li>
                        <li>pasaporte - паспорт</li>
                        <li>visa - виза</li>
                        <li>equipaje - багаж</li>
                        <li>destino - пункт назначения</li>
                        <li>alojamiento - жилье</li>
                        <li>reserva - бронирование</li>
                    </ul>
                    
                    <h2>🏨 Tipos de alojamiento</h2>
                    <ul>
                        <li>hotel - отель</li>
                        <li>hostal - хостел</li>
                        <li>apartamento - квартира</li>
                        <li>villa - вилла</li>
                        <li>casa rural - гостевой дом</li>
                    </ul>
                    
                    <h2>🗣️ Diálogo en el aeropuerto</h2>
                    <div class="dialogue">
                        <p><strong>Pasajero:</strong> Disculpe, ¿dónde está el mostrador de facturación para el vuelo IB345?</p>
                        <p><strong>Empleado:</strong> Está en el mostrador número 7. ¿Tiene su pasaporte y billete?</p>
                        <p><strong>Pasajero:</strong> Sí, aquí están. Quisiera un asiento de ventana, por favor.</p>
                        <p><strong>Empleado:</strong> Por supuesto. ¿Cuántas maletas factura?</p>
                        <p><strong>Pasajero:</strong> Solo una maleta. La otra es equipaje de mano.</p>
                    </div>''',
                    'words': [
                        {'word': 'viajar', 'translation': 'путешествовать', 'transcription': '[bjaˈxaɾ]', 'example': 'Me encanta viajar al extranjero.', 'part_of_speech': 'verb'},
                        {'word': 'aeropuerto', 'translation': 'аэропорт', 'transcription': '[aeɾoˈpweɾto]', 'example': 'El aeropuerto está muy ocupado.', 'part_of_speech': 'noun'},
                        {'word': 'pasaporte', 'translation': 'паспорт', 'transcription': '[pasaˈpoɾte]', 'example': 'No olvides tu pasaporte.', 'part_of_speech': 'noun'},
                        {'word': 'hotel', 'translation': 'отель', 'transcription': '[oˈtel]', 'example': 'Reservamos un hotel bonito.', 'part_of_speech': 'noun'},
                        {'word': 'billete', 'translation': 'билет', 'transcription': '[biˈʎete]', 'example': 'Compré un billete de avión.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Salud y bienestar',
                    'content': '''<h1>Lección 2: Salud y bienestar</h1>
                    
                    <h2>🏃‍♂️ Vocabulario de salud</h2>
                    <ul>
                        <li>saludable - здоровый</li>
                        <li>ejercicio - упражнение</li>
                        <li>forma física - фитнес</li>
                        <li>dieta - диета</li>
                        <li>vitaminas - витамины</li>
                        <li>gimnasio - спортзал</li>
                        <li>entrenamiento - тренировка</li>
                    </ul>
                    
                    <h2>🤒 Enfermedades</h2>
                    <ul>
                        <li>resfriado - простуда</li>
                        <li>gripe - грипп</li>
                        <li>dolor de cabeza - головная боль</li>
                        <li>fiebre - температура</li>
                        <li>tos - кашель</li>
                    </ul>
                    
                    <h2>🗣️ Diálogo con el médico</h2>
                    <div class="dialogue">
                        <p><strong>Médico:</strong> ¿Qué le pasa?</p>
                        <p><strong>Paciente:</strong> Tengo dolor de cabeza y garganta.</p>
                        <p><strong>Médico:</strong> ¿Tiene fiebre?</p>
                        <p><strong>Paciente:</strong> Sí, creo que sí. Me siento muy cansado.</p>
                        <p><strong>Médico:</strong> Tiene gripe. Descanse y beba mucha agua.</p>
                    </div>''',
                    'words': [
                        {'word': 'salud', 'translation': 'здоровье', 'transcription': '[saˈluð]', 'example': 'La salud es lo más importante.', 'part_of_speech': 'noun'},
                        {'word': 'ejercicio', 'translation': 'упражнение', 'transcription': '[exeɾˈθiθjo]', 'example': 'Hago ejercicio cada mañana.', 'part_of_speech': 'noun'},
                        {'word': 'médico', 'translation': 'врач', 'transcription': '[ˈmeðiko]', 'example': 'Debes ver a un médico.', 'part_of_speech': 'noun'},
                        {'word': 'medicina', 'translation': 'лекарство', 'transcription': '[meðiˈθina]', 'example': 'Toma esta medicina.', 'part_of_speech': 'noun'},
                        {'word': 'fiebre', 'translation': 'температура', 'transcription': '[ˈfjeβɾe]', 'example': 'Tengo fiebre alta.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Educación y aprendizaje',
                    'content': '''<h1>Lección 3: Educación y aprendizaje</h1>
                    
                    <h2>📚 Sistema educativo</h2>
                    <ul>
                        <li>escuela - школа</li>
                        <li>universidad - университет</li>
                        <li>colegio - колледж</li>
                        <li>estudiante - студент</li>
                        <li>profesor - учитель</li>
                        <li>catedrático - профессор</li>
                        <li>título - степень</li>
                        <li>diploma - диплом</li>
                    </ul>
                    
                    <h2>📝 Asignaturas</h2>
                    <ul>
                        <li>matemáticas - математика</li>
                        <li>física - физика</li>
                        <li>química - химия</li>
                        <li>historia - история</li>
                        <li>literatura - литература</li>
                        <li>idiomas - языки</li>
                    </ul>''',
                    'words': [
                        {'word': 'escuela', 'translation': 'школа', 'transcription': '[esˈkwela]', 'example': 'Los niños van a la escuela.', 'part_of_speech': 'noun'},
                        {'word': 'universidad', 'translation': 'университет', 'transcription': '[uniβeɾsiˈðað]', 'example': 'Ella estudia en la universidad.', 'part_of_speech': 'noun'},
                        {'word': 'estudiante', 'translation': 'студент', 'transcription': '[estuˈðjante]', 'example': 'Él es un buen estudiante.', 'part_of_speech': 'noun'},
                        {'word': 'estudiar', 'translation': 'учиться', 'transcription': '[estuˈðjaɾ]', 'example': 'Estudio todos los días.', 'part_of_speech': 'verb'},
                        {'word': 'examen', 'translation': 'экзамен', 'transcription': '[ekˈsamen]', 'example': 'Aprobé mi examen.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Tecnología e internet',
                    'content': '''<h1>Lección 4: Tecnología e internet</h1>
                    
                    <h2>💻 Vocabulario de tecnología</h2>
                    <ul>
                        <li>ordenador - компьютер</li>
                        <li>portátil - ноутбук</li>
                        <li>teléfono inteligente - смартфон</li>
                        <li>tableta - планшет</li>
                        <li>internet - интернет</li>
                        <li>sitio web - вебсайт</li>
                        <li>aplicación - приложение</li>
                        <li>software - программное обеспечение</li>
                    </ul>''',
                    'words': [
                        {'word': 'ordenador', 'translation': 'компьютер', 'transcription': '[oɾðenaˈðoɾ]', 'example': 'Trabajo en mi ordenador.', 'part_of_speech': 'noun'},
                        {'word': 'internet', 'translation': 'интернет', 'transcription': '[inteɾˈnet]', 'example': 'El internet es rápido.', 'part_of_speech': 'noun'},
                        {'word': 'correo electrónico', 'translation': 'электронная почта', 'transcription': '[koˈreo elekˈtɾoniko]', 'example': 'Envíame un correo.', 'part_of_speech': 'noun'},
                        {'word': 'móvil', 'translation': 'мобильный', 'transcription': '[ˈmoβil]', 'example': 'Mi móvil está sonando.', 'part_of_speech': 'noun'},
                        {'word': 'aplicación', 'translation': 'приложение', 'transcription': '[aplikaˈθjon]', 'example': 'Descargué una nueva aplicación.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Medio ambiente',
                    'content': '''<h1>Lección 5: Medio ambiente</h1>
                    
                    <h2>🌍 Problemas ambientales</h2>
                    <ul>
                        <li>contaminación - загрязнение</li>
                        <li>cambio climático - изменение климата</li>
                        <li>calentamiento global - глобальное потепление</li>
                        <li>reciclaje - переработка</li>
                        <li>conservación - сохранение</li>
                        <li>sostenible - устойчивый</li>
                    </ul>''',
                    'words': [
                        {'word': 'medio ambiente', 'translation': 'окружающая среда', 'transcription': '[ˈmeðjo amˈbjente]', 'example': 'Debemos proteger el medio ambiente.', 'part_of_speech': 'noun'},
                        {'word': 'naturaleza', 'translation': 'природа', 'transcription': '[natuɾaˈleθa]', 'example': 'Amo pasar tiempo en la naturaleza.', 'part_of_speech': 'noun'},
                        {'word': 'contaminación', 'translation': 'загрязнение', 'transcription': '[kontaminaˈθjon]', 'example': 'La contaminación es un problema grave.', 'part_of_speech': 'noun'},
                        {'word': 'reciclar', 'translation': 'перерабатывать', 'transcription': '[reθiˈklaɾ]', 'example': 'Debemos reciclar más.', 'part_of_speech': 'verb'},
                        {'word': 'bosque', 'translation': 'лес', 'transcription': '[ˈboske]', 'example': 'El bosque es hermoso.', 'part_of_speech': 'noun'}
                    ]
                }
            ],
            'B2': [
                {
                    'title': 'Negocios y finanzas',
                    'content': '''<h1>Lección 1: Negocios y finanzas</h1>
                    
                    <h2>💼 Vocabulario de negocios</h2>
                    <ul>
                        <li>negociación - переговоры</li>
                        <li>contrato - контракт</li>
                        <li>acuerdo - соглашение</li>
                        <li>propuesta - предложение</li>
                        <li>plazo - срок</li>
                        <li>presupuesto - бюджет</li>
                        <li>inversión - инвестиция</li>
                        <li>beneficio - прибыль</li>
                    </ul>''',
                    'words': [
                        {'word': 'negocio', 'translation': 'бизнес', 'transcription': '[neˈɣoθjo]', 'example': 'Trabaja en negocios internacionales.', 'part_of_speech': 'noun'},
                        {'word': 'contrato', 'translation': 'контракт', 'transcription': '[konˈtɾato]', 'example': 'Firmamos un contrato ayer.', 'part_of_speech': 'noun'},
                        {'word': 'negociación', 'translation': 'переговоры', 'transcription': '[neɣoθjaˈθjon]', 'example': 'La negociación fue exitosa.', 'part_of_speech': 'noun'},
                        {'word': 'plazo', 'translation': 'крайний срок', 'transcription': '[ˈplaθo]', 'example': 'El plazo es el viernes.', 'part_of_speech': 'noun'},
                        {'word': 'inversión', 'translation': 'инвестиция', 'transcription': '[imbeɾˈsjon]', 'example': 'Es una buena inversión.', 'part_of_speech': 'noun'}
                    ]
                }
                # Остальные уроки B2 для испанского аналогично английским
            ],
            'C1': [
                {
                    'title': 'Literatura española',
                    'content': '''<h1>Lección 1: Literatura española</h1>
                    
                    <h2>📖 Grandes autores</h2>
                    <ul>
                        <li>Miguel de Cervantes - Don Quijote</li>
                        <li>Federico García Lorca - поэт и драматург</li>
                        <li>Gabriel García Márquez - Cien años de soledad</li>
                        <li>Jorge Luis Borges - рассказы</li>
                    </ul>''',
                    'words': [
                        {'word': 'literatura', 'translation': 'литература', 'transcription': '[liteɾaˈtuɾa]', 'example': 'La literatura española es rica.', 'part_of_speech': 'noun'},
                        {'word': 'novela', 'translation': 'роман', 'transcription': '[noˈβela]', 'example': 'Leí una novela interesante.', 'part_of_speech': 'noun'},
                        {'word': 'poesía', 'translation': 'поэзия', 'transcription': '[poeˈsia]', 'example': 'Me gusta la poesía de Lorca.', 'part_of_speech': 'noun'},
                        {'word': 'autor', 'translation': 'автор', 'transcription': '[auˈtoɾ]', 'example': 'Mi autor favorito es Cervantes.', 'part_of_speech': 'noun'},
                        {'word': 'obra', 'translation': 'произведение', 'transcription': '[ˈoβɾa]', 'example': 'El Quijote es su obra maestra.', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_french_lessons(self, level):
        """Уроки для французского языка"""
        lessons = {
            'A1': [
                {
                    'title': 'Salutations et présentations',
                    'content': '''<h1>Leçon 1: Salutations et présentations</h1>
                    
                    <h2>📚 Objectifs de la leçon</h2>
                    <ul>
                        <li>Apprendre à saluer à différents moments de la journée</li>
                        <li>Se présenter et rencontrer d'autres personnes</li>
                        <li>Poser des questions de base sur soi-même</li>
                    </ul>
                    
                    <h2>👋 Salutations de base</h2>
                    <div class="phrase-box">
                        <p><strong>Bonjour</strong> - Здравствуйте / Добрый день</p>
                        <p><strong>Bonsoir</strong> - Добрый вечер</p>
                        <p><strong>Salut</strong> - Привет (неформально)</p>
                        <p><strong>Au revoir</strong> - До свидания</p>
                        <p><strong>Bonne nuit</strong> - Спокойной ночи</p>
                    </div>
                    
                    <h2>🗣️ Dialogue</h2>
                    <div class="dialogue">
                        <p><strong>Pierre:</strong> Bonjour ! Je m'appelle Pierre. Et toi ? Comment tu t'appelles ?</p>
                        <p><strong>Marie:</strong> Bonjour, Pierre ! Je m'appelle Marie. Enchantée.</p>
                        <p><strong>Pierre:</strong> Enchanté, Marie. Tu es française ?</p>
                        <p><strong>Marie:</strong> Oui, je suis de Paris. Et toi ?</p>
                        <p><strong>Pierre:</strong> Je suis de Lyon.</p>
                    </div>
                    
                    <h2>🔑 Phrases clés</h2>
                    <ul>
                        <li><strong>Comment tu t'appelles ?</strong> - Как тебя зовут?</li>
                        <li><strong>Je m'appelle...</strong> - Меня зовут...</li>
                        <li><strong>Enchanté(e)</strong> - Приятно познакомиться</li>
                        <li><strong>D'où viens-tu ?</strong> - Откуда ты?</li>
                        <li><strong>Je viens de...</strong> - Я из...</li>
                    </ul>
                    
                    <div class="tip">
                        <h3>💡 Совет по произношению:</h3>
                        <p>Во французском языке ударение всегда падает на последний слог. Буква "r" произносится гортанно.</p>
                    </div>''',
                    'words': [
                        {'word': 'bonjour', 'translation': 'здравствуйте', 'transcription': '[bɔ̃ʒuʁ]', 'example': 'Bonjour, comment allez-vous?', 'part_of_speech': 'interjection'},
                        {'word': 'au revoir', 'translation': 'до свидания', 'transcription': '[o ʁəvwaʁ]', 'example': 'Au revoir, à demain!', 'part_of_speech': 'interjection'},
                        {'word': 'merci', 'translation': 'спасибо', 'transcription': '[mɛʁsi]', 'example': 'Merci beaucoup pour votre aide.', 'part_of_speech': 'noun'},
                        {'word': 'nom', 'translation': 'имя', 'transcription': '[nɔ̃]', 'example': 'Mon nom est Dupont.', 'part_of_speech': 'noun'},
                        {'word': 'ami', 'translation': 'друг', 'transcription': '[ami]', 'example': 'C\'est mon ami.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'La famille',
                    'content': '''<h1>Leçon 2: La famille</h1>
                    
                    <h2>👨‍👩‍👧‍👦 Membres de la famille</h2>
                    <table class="table">
                        <tr><th>Français</th><th>Русский</th></tr>
                        <tr><td>mère</td><td>мама</td></tr>
                        <tr><td>père</td><td>папа</td></tr>
                        <tr><td>frère</td><td>брат</td></tr>
                        <tr><td>sœur</td><td>сестра</td></tr>
                        <tr><td>grand-mère</td><td>бабушка</td></tr>
                        <tr><td>grand-père</td><td>дедушка</td></tr>
                        <tr><td>oncle</td><td>дядя</td></tr>
                        <tr><td>tante</td><td>тетя</td></tr>
                    </table>''',
                    'words': [
                        {'word': 'famille', 'translation': 'семья', 'transcription': '[famij]', 'example': 'Ma famille est très unie.', 'part_of_speech': 'noun'},
                        {'word': 'mère', 'translation': 'мама', 'transcription': '[mɛʁ]', 'example': 'Ma mère est professeur.', 'part_of_speech': 'noun'},
                        {'word': 'père', 'translation': 'папа', 'transcription': '[pɛʁ]', 'example': 'Mon père travaille dans un bureau.', 'part_of_speech': 'noun'},
                        {'word': 'frère', 'translation': 'брат', 'transcription': '[fʁɛʁ]', 'example': 'J\'ai un frère aîné.', 'part_of_speech': 'noun'},
                        {'word': 'sœur', 'translation': 'сестра', 'transcription': '[sœʁ]', 'example': 'Ma sœur est plus jeune.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Nombres et âge',
                    'content': '''<h1>Leçon 3: Nombres et âge</h1>
                    
                    <h2>🔢 Nombres 1-20</h2>
                    <p>1 - un, 2 - deux, 3 - trois, 4 - quatre, 5 - cinq, 6 - six, 7 - sept, 8 - huit, 9 - neuf, 10 - dix</p>
                    <p>11 - onze, 12 - douze, 13 - treize, 14 - quatorze, 15 - quinze, 16 - seize, 17 - dix-sept, 18 - dix-huit, 19 - dix-neuf, 20 - vingt</p>''',
                    'words': [
                        {'word': 'un', 'translation': 'один', 'transcription': '[œ̃]', 'example': 'J\'ai un chat.', 'part_of_speech': 'numeral'},
                        {'word': 'deux', 'translation': 'два', 'transcription': '[dø]', 'example': 'Deux frères.', 'part_of_speech': 'numeral'},
                        {'word': 'trois', 'translation': 'три', 'transcription': '[tʁwa]', 'example': 'Trois pommes.', 'part_of_speech': 'numeral'},
                        {'word': 'âge', 'translation': 'возраст', 'transcription': '[ɑʒ]', 'example': 'Quel âge as-tu?', 'part_of_speech': 'noun'},
                        {'word': 'ans', 'translation': 'лет', 'transcription': '[ɑ̃]', 'example': 'J\'ai 25 ans.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Couleurs',
                    'content': '''<h1>Leçon 4: Couleurs</h1>
                    
                    <h2>🎨 Couleurs de base</h2>
                    <ul>
                        <li><span style="color: red;">rouge</span> - красный</li>
                        <li><span style="color: blue;">bleu</span> - синий</li>
                        <li><span style="color: green;">vert</span> - зеленый</li>
                        <li><span style="color: yellow;">jaune</span> - желтый</li>
                        <li><span style="color: black;">noir</span> - черный</li>
                        <li><span style="color: white;">blanc</span> - белый</li>
                        <li>orange - оранжевый</li>
                        <li>violet - фиолетовый</li>
                        <li>rose - розовый</li>
                        <li>marron - коричневый</li>
                    </ul>''',
                    'words': [
                        {'word': 'rouge', 'translation': 'красный', 'transcription': '[ʁuʒ]', 'example': 'La pomme est rouge.', 'part_of_speech': 'adjective'},
                        {'word': 'bleu', 'translation': 'синий', 'transcription': '[blø]', 'example': 'Le ciel est bleu.', 'part_of_speech': 'adjective'},
                        {'word': 'vert', 'translation': 'зеленый', 'transcription': '[vɛʁ]', 'example': 'L\'herbe est verte.', 'part_of_speech': 'adjective'},
                        {'word': 'jaune', 'translation': 'желтый', 'transcription': '[ʒon]', 'example': 'Le soleil est jaune.', 'part_of_speech': 'adjective'},
                        {'word': 'noir', 'translation': 'черный', 'transcription': '[nwaʁ]', 'example': 'Ma voiture est noire.', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': 'Nourriture et boissons',
                    'content': '''<h1>Leçon 5: Nourriture et boissons</h1>
                    
                    <h2>🍎 Vocabulaire alimentaire</h2>
                    <ul>
                        <li>pain - хлеб</li>
                        <li>beurre - масло</li>
                        <li>fromage - сыр</li>
                        <li>lait - молоко</li>
                        <li>œufs - яйца</li>
                        <li>viande - мясо</li>
                        <li>poisson - рыба</li>
                        <li>légumes - овощи</li>
                        <li>fruits - фрукты</li>
                    </ul>''',
                    'words': [
                        {'word': 'pain', 'translation': 'хлеб', 'transcription': '[pɛ̃]', 'example': 'Je mange du pain tous les jours.', 'part_of_speech': 'noun'},
                        {'word': 'eau', 'translation': 'вода', 'transcription': '[o]', 'example': 'Je bois de l\'eau.', 'part_of_speech': 'noun'},
                        {'word': 'café', 'translation': 'кофе', 'transcription': '[kafe]', 'example': 'Je prends un café le matin.', 'part_of_speech': 'noun'},
                        {'word': 'pomme', 'translation': 'яблоко', 'transcription': '[pɔm]', 'example': 'Une pomme par jour.', 'part_of_speech': 'noun'},
                        {'word': 'restaurant', 'translation': 'ресторан', 'transcription': '[ʁɛstoʁɑ̃]', 'example': 'Allons au restaurant.', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_german_lessons(self, level):
        """Уроки для немецкого языка"""
        lessons = {
            'A1': [
                {
                    'title': 'Begrüßungen und Vorstellungen',
                    'content': '''<h1>Lektion 1: Begrüßungen und Vorstellungen</h1>
                    
                    <h2>📚 Lernziele</h2>
                    <ul>
                        <li>Begrüßungen zu verschiedenen Tageszeiten lernen</li>
                        <li>Sich vorstellen und andere kennenlernen</li>
                        <li>Einfache Fragen über sich selbst stellen und beantworten</li>
                    </ul>
                    
                    <h2>👋 Grundlegende Begrüßungen</h2>
                    <div class="phrase-box">
                        <p><strong>Hallo</strong> - Привет</p>
                        <p><strong>Guten Morgen</strong> - Доброе утро</p>
                        <p><strong>Guten Tag</strong> - Добрый день</p>
                        <p><strong>Guten Abend</strong> - Добрый вечер</p>
                        <p><strong>Gute Nacht</strong> - Спокойной ночи</p>
                        <p><strong>Auf Wiedersehen</strong> - До свидания</p>
                        <p><strong>Tschüss</strong> - Пока (неформально)</p>
                    </div>
                    
                    <h2>🗣️ Dialog</h2>
                    <div class="dialogue">
                        <p><strong>Thomas:</strong> Hallo! Ich heiße Thomas. Und du? Wie heißt du?</p>
                        <p><strong>Anna:</strong> Hallo Thomas! Ich heiße Anna. Freut mich!</p>
                        <p><strong>Thomas:</strong> Freut mich auch, Anna. Woher kommst du?</p>
                        <p><strong>Anna:</strong> Ich komme aus Berlin. Und du?</p>
                        <p><strong>Thomas:</strong> Ich komme aus München.</p>
                    </div>
                    
                    <h2>🔑 Wichtige Sätze</h2>
                    <ul>
                        <li><strong>Wie heißt du?</strong> - Как тебя зовут?</li>
                        <li><strong>Ich heiße...</strong> - Меня зовут...</li>
                        <li><strong>Freut mich!</strong> - Приятно познакомиться</li>
                        <li><strong>Woher kommst du?</strong> - Откуда ты?</li>
                        <li><strong>Ich komme aus...</strong> - Я из...</li>
                    </ul>
                    
                    <div class="tip">
                        <h3>💡 Совет по произношению:</h3>
                        <p>В немецком все существительные пишутся с заглавной буквы. Буква "ch" может произноситься по-разному: после a, o, u как "х", после e, i, ö, ü как "хь".</p>
                    </div>''',
                    'words': [
                        {'word': 'Hallo', 'translation': 'привет', 'transcription': '[haˈloː]', 'example': 'Hallo, wie geht es dir?', 'part_of_speech': 'interjection'},
                        {'word': 'Tschüss', 'translation': 'пока', 'transcription': '[tʃʏs]', 'example': 'Tschüss, bis morgen!', 'part_of_speech': 'interjection'},
                        {'word': 'Danke', 'translation': 'спасибо', 'transcription': '[ˈdaŋkə]', 'example': 'Danke für deine Hilfe.', 'part_of_speech': 'noun'},
                        {'word': 'Name', 'translation': 'имя', 'transcription': '[ˈnaːmə]', 'example': 'Mein Name ist Schmidt.', 'part_of_speech': 'noun'},
                        {'word': 'Freund', 'translation': 'друг', 'transcription': '[fʁɔʏ̯nt]', 'example': 'Er ist mein Freund.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Die Familie',
                    'content': '''<h1>Lektion 2: Die Familie</h1>
                    
                    <h2>👨‍👩‍👧‍👦 Familienmitglieder</h2>
                    <table class="table">
                        <tr><th>Deutsch</th><th>Русский</th></tr>
                        <tr><td>Mutter</td><td>мама</td></tr>
                        <tr><td>Vater</td><td>папа</td></tr>
                        <tr><td>Bruder</td><td>брат</td></tr>
                        <tr><td>Schwester</td><td>сестра</td></tr>
                        <tr><td>Großmutter / Oma</td><td>бабушка</td></tr>
                        <tr><td>Großvater / Opa</td><td>дедушка</td></tr>
                        <tr><td>Onkel</td><td>дядя</td></tr>
                        <tr><td>Tante</td><td>тетя</td></tr>
                    </table>''',
                    'words': [
                        {'word': 'Familie', 'translation': 'семья', 'transcription': '[faˈmiːli̯ə]', 'example': 'Meine Familie ist groß.', 'part_of_speech': 'noun'},
                        {'word': 'Mutter', 'translation': 'мама', 'transcription': '[ˈmʊtɐ]', 'example': 'Meine Mutter ist Lehrerin.', 'part_of_speech': 'noun'},
                        {'word': 'Vater', 'translation': 'папа', 'transcription': '[ˈfaːtɐ]', 'example': 'Mein Vater arbeitet im Büro.', 'part_of_speech': 'noun'},
                        {'word': 'Bruder', 'translation': 'брат', 'transcription': '[ˈbʁuːdɐ]', 'example': 'Ich habe einen Bruder.', 'part_of_speech': 'noun'},
                        {'word': 'Schwester', 'translation': 'сестра', 'transcription': '[ˈʃvɛstɐ]', 'example': 'Meine Schwester ist jünger.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Zahlen und Alter',
                    'content': '''<h1>Lektion 3: Zahlen und Alter</h1>
                    
                    <h2>🔢 Zahlen 1-20</h2>
                    <p>1 - eins, 2 - zwei, 3 - drei, 4 - vier, 5 - fünf, 6 - sechs, 7 - sieben, 8 - acht, 9 - neun, 10 - zehn</p>
                    <p>11 - elf, 12 - zwölf, 13 - dreizehn, 14 - vierzehn, 15 - fünfzehn, 16 - sechzehn, 17 - siebzehn, 18 - achtzehn, 19 - neunzehn, 20 - zwanzig</p>''',
                    'words': [
                        {'word': 'eins', 'translation': 'один', 'transcription': '[aɪ̯ns]', 'example': 'Ich habe eine Katze.', 'part_of_speech': 'numeral'},
                        {'word': 'zwei', 'translation': 'два', 'transcription': '[t͡svaɪ̯]', 'example': 'Zwei Brüder.', 'part_of_speech': 'numeral'},
                        {'word': 'drei', 'translation': 'три', 'transcription': '[dʁaɪ̯]', 'example': 'Drei Äpfel.', 'part_of_speech': 'numeral'},
                        {'word': 'Alter', 'translation': 'возраст', 'transcription': '[ˈaltɐ]', 'example': 'Wie alt bist du?', 'part_of_speech': 'noun'},
                        {'word': 'Jahre', 'translation': 'лет', 'transcription': '[ˈjaːʁə]', 'example': 'Ich bin 25 Jahre alt.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Farben',
                    'content': '''<h1>Lektion 4: Farben</h1>
                    
                    <h2>🎨 Grundfarben</h2>
                    <ul>
                        <li><span style="color: red;">rot</span> - красный</li>
                        <li><span style="color: blue;">blau</span> - синий</li>
                        <li><span style="color: green;">grün</span> - зеленый</li>
                        <li><span style="color: yellow;">gelb</span> - желтый</li>
                        <li><span style="color: black;">schwarz</span> - черный</li>
                        <li><span style="color: white;">weiß</span> - белый</li>
                        <li>orange - оранжевый</li>
                        <li>lila - фиолетовый</li>
                        <li>pink - розовый</li>
                        <li>braun - коричневый</li>
                    </ul>''',
                    'words': [
                        {'word': 'rot', 'translation': 'красный', 'transcription': '[ʁoːt]', 'example': 'Der Apfel ist rot.', 'part_of_speech': 'adjective'},
                        {'word': 'blau', 'translation': 'синий', 'transcription': '[blaʊ̯]', 'example': 'Der Himmel ist blau.', 'part_of_speech': 'adjective'},
                        {'word': 'grün', 'translation': 'зеленый', 'transcription': '[ɡʁyːn]', 'example': 'Das Gras ist grün.', 'part_of_speech': 'adjective'},
                        {'word': 'gelb', 'translation': 'желтый', 'transcription': '[ɡɛlp]', 'example': 'Die Sonne ist gelb.', 'part_of_speech': 'adjective'},
                        {'word': 'schwarz', 'translation': 'черный', 'transcription': '[ʃvaʁt͡s]', 'example': 'Mein Auto ist schwarz.', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': 'Essen und Trinken',
                    'content': '''<h1>Lektion 5: Essen und Trinken</h1>
                    
                    <h2>🍎 Lebensmittel</h2>
                    <ul>
                        <li>Brot - хлеб</li>
                        <li>Butter - масло</li>
                        <li>Käse - сыр</li>
                        <li>Milch - молоко</li>
                        <li>Eier - яйца</li>
                        <li>Fleisch - мясо</li>
                        <li>Fisch - рыба</li>
                        <li>Gemüse - овощи</li>
                        <li>Obst - фрукты</li>
                    </ul>''',
                    'words': [
                        {'word': 'Brot', 'translation': 'хлеб', 'transcription': '[bʁoːt]', 'example': 'Ich esse Brot jeden Tag.', 'part_of_speech': 'noun'},
                        {'word': 'Wasser', 'translation': 'вода', 'transcription': '[ˈvasɐ]', 'example': 'Ich trinke Wasser.', 'part_of_speech': 'noun'},
                        {'word': 'Kaffee', 'translation': 'кофе', 'transcription': '[ˈkafe]', 'example': 'Ich trinke Kaffee am Morgen.', 'part_of_speech': 'noun'},
                        {'word': 'Apfel', 'translation': 'яблоко', 'transcription': '[ˈap͡fl̩]', 'example': 'Ein Apfel am Tag.', 'part_of_speech': 'noun'},
                        {'word': 'Restaurant', 'translation': 'ресторан', 'transcription': '[ʁɛstoˈʁɑ̃]', 'example': 'Gehen wir ins Restaurant.', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_italian_lessons(self, level):
        """Уроки для итальянского языка"""
        lessons = {
            'A1': [
                {
                    'title': 'Saluti e presentazioni',
                    'content': '''<h1>Lezione 1: Saluti e presentazioni</h1>
                    
                    <h2>📚 Obiettivi della lezione</h2>
                    <ul>
                        <li>Imparare a salutare in diversi momenti della giornata</li>
                        <li>Presentarsi e conoscere altre persone</li>
                        <li>Fare e rispondere a domande di base su di sé</li>
                    </ul>
                    
                    <h2>👋 Saluti di base</h2>
                    <div class="phrase-box">
                        <p><strong>Ciao</strong> - Привет / Пока</p>
                        <p><strong>Buongiorno</strong> - Доброе утро / Добрый день</p>
                        <p><strong>Buonasera</strong> - Добрый вечер</p>
                        <p><strong>Buonanotte</strong> - Спокойной ночи</p>
                        <p><strong>Arrivederci</strong> - До свидания</p>
                    </div>
                    
                    <h2>🗣️ Dialogo</h2>
                    <div class="dialogue">
                        <p><strong>Marco:</strong> Ciao! Mi chiamo Marco. E tu? Come ti chiami?</p>
                        <p><strong>Giulia:</strong> Ciao Marco! Mi chiamo Giulia. Piacere!</p>
                        <p><strong>Marco:</strong> Piacere, Giulia. Di dove sei?</p>
                        <p><strong>Giulia:</strong> Sono di Roma. E tu?</p>
                        <p><strong>Marco:</strong> Sono di Milano.</p>
                    </div>
                    
                    <h2>🔑 Frasi chiave</h2>
                    <ul>
                        <li><strong>Come ti chiami?</strong> - Как тебя зовут?</li>
                        <li><strong>Mi chiamo...</strong> - Меня зовут...</li>
                        <li><strong>Piacere!</strong> - Приятно познакомиться</li>
                        <li><strong>Di dove sei?</strong> - Откуда ты?</li>
                        <li><strong>Sono di...</strong> - Я из...</li>
                    </ul>
                    
                    <div class="tip">
                        <h3>💡 Совет по произношению:</h3>
                        <p>В итальянском все буквы произносятся четко. Двойные согласные произносятся дольше. "C" перед e и i читается как "ч", перед a, o, u - как "к".</p>
                    </div>''',
                    'words': [
                        {'word': 'ciao', 'translation': 'привет/пока', 'transcription': '[ˈtʃaːo]', 'example': 'Ciao, come stai?', 'part_of_speech': 'interjection'},
                        {'word': 'arrivederci', 'translation': 'до свидания', 'transcription': '[arriveˈdertʃi]', 'example': 'Arrivederci, a domani!', 'part_of_speech': 'interjection'},
                        {'word': 'grazie', 'translation': 'спасибо', 'transcription': '[ˈɡrattsje]', 'example': 'Grazie mille per il tuo aiuto.', 'part_of_speech': 'noun'},
                        {'word': 'nome', 'translation': 'имя', 'transcription': '[ˈnoːme]', 'example': 'Il mio nome è Rossi.', 'part_of_speech': 'noun'},
                        {'word': 'amico', 'translation': 'друг', 'transcription': '[aˈmiːko]', 'example': 'Lui è il mio amico.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'La famiglia',
                    'content': '''<h1>Lezione 2: La famiglia</h1>
                    
                    <h2>👨‍👩‍👧‍👦 Membri della famiglia</h2>
                    <table class="table">
                        <tr><th>Italiano</th><th>Русский</th></tr>
                        <tr><td>madre / mamma</td><td>мама</td></tr>
                        <tr><td>padre / papà</td><td>папа</td></tr>
                        <tr><td>fratello</td><td>брат</td></tr>
                        <tr><td>sorella</td><td>сестра</td></tr>
                        <tr><td>nonna</td><td>бабушка</td></tr>
                        <tr><td>nonno</td><td>дедушка</td></tr>
                        <tr><td>zio</td><td>дядя</td></tr>
                        <tr><td>zia</td><td>тетя</td></tr>
                    </table>''',
                    'words': [
                        {'word': 'famiglia', 'translation': 'семья', 'transcription': '[faˈmiʎʎa]', 'example': 'La mia famiglia è grande.', 'part_of_speech': 'noun'},
                        {'word': 'madre', 'translation': 'мама', 'transcription': '[ˈmaːdre]', 'example': 'Mia madre è insegnante.', 'part_of_speech': 'noun'},
                        {'word': 'padre', 'translation': 'папа', 'transcription': '[ˈpaːdre]', 'example': 'Mio padre lavora in ufficio.', 'part_of_speech': 'noun'},
                        {'word': 'fratello', 'translation': 'брат', 'transcription': '[fraˈtɛllo]', 'example': 'Ho un fratello maggiore.', 'part_of_speech': 'noun'},
                        {'word': 'sorella', 'translation': 'сестра', 'transcription': '[soˈrɛlla]', 'example': 'Mia sorella è più giovane.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Numeri ed età',
                    'content': '''<h1>Lezione 3: Numeri ed età</h1>
                    
                    <h2>🔢 Numeri 1-20</h2>
                    <p>1 - uno, 2 - due, 3 - tre, 4 - quattro, 5 - cinque, 6 - sei, 7 - sette, 8 - otto, 9 - nove, 10 - dieci</p>
                    <p>11 - undici, 12 - dodici, 13 - tredici, 14 - quattordici, 15 - quindici, 16 - sedici, 17 - diciassette, 18 - diciotto, 19 - diciannove, 20 - venti</p>''',
                    'words': [
                        {'word': 'uno', 'translation': 'один', 'transcription': '[ˈuːno]', 'example': 'Ho un gatto.', 'part_of_speech': 'numeral'},
                        {'word': 'due', 'translation': 'два', 'transcription': '[ˈduːe]', 'example': 'Due fratelli.', 'part_of_speech': 'numeral'},
                        {'word': 'tre', 'translation': 'три', 'transcription': '[tre]', 'example': 'Tre mele.', 'part_of_speech': 'numeral'},
                        {'word': 'età', 'translation': 'возраст', 'transcription': '[eˈta]', 'example': 'Quanti anni hai?', 'part_of_speech': 'noun'},
                        {'word': 'anni', 'translation': 'лет', 'transcription': '[ˈanni]', 'example': 'Ho 25 anni.', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': 'Colori',
                    'content': '''<h1>Lezione 4: Colori</h1>
                    
                    <h2>🎨 Colori base</h2>
                    <ul>
                        <li><span style="color: red;">rosso</span> - красный</li>
                        <li><span style="color: blue;">blu</span> - синий</li>
                        <li><span style="color: green;">verde</span> - зеленый</li>
                        <li><span style="color: yellow;">giallo</span> - желтый</li>
                        <li><span style="color: black;">nero</span> - черный</li>
                        <li><span style="color: white;">bianco</span> - белый</li>
                        <li>arancione - оранжевый</li>
                        <li>viola - фиолетовый</li>
                        <li>rosa - розовый</li>
                        <li>marrone - коричневый</li>
                    </ul>''',
                    'words': [
                        {'word': 'rosso', 'translation': 'красный', 'transcription': '[ˈrosso]', 'example': 'La mela è rossa.', 'part_of_speech': 'adjective'},
                        {'word': 'blu', 'translation': 'синий', 'transcription': '[blu]', 'example': 'Il cielo è blu.', 'part_of_speech': 'adjective'},
                        {'word': 'verde', 'translation': 'зеленый', 'transcription': '[ˈverde]', 'example': 'L\'erba è verde.', 'part_of_speech': 'adjective'},
                        {'word': 'giallo', 'translation': 'желтый', 'transcription': '[ˈdʒallo]', 'example': 'Il sole è giallo.', 'part_of_speech': 'adjective'},
                        {'word': 'nero', 'translation': 'черный', 'transcription': '[ˈneːro]', 'example': 'La mia macchina è nera.', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': 'Cibo e bevande',
                    'content': '''<h1>Lezione 5: Cibo e bevande</h1>
                    
                    <h2>🍎 Vocabolario del cibo</h2>
                    <ul>
                        <li>pane - хлеб</li>
                        <li>burro - масло</li>
                        <li>formaggio - сыр</li>
                        <li>latte - молоко</li>
                        <li>uova - яйца</li>
                        <li>carne - мясо</li>
                        <li>pesce - рыба</li>
                        <li>verdura - овощи</li>
                        <li>frutta - фрукты</li>
                    </ul>''',
                    'words': [
                        {'word': 'pane', 'translation': 'хлеб', 'transcription': '[ˈpaːne]', 'example': 'Mangio pane ogni giorno.', 'part_of_speech': 'noun'},
                        {'word': 'acqua', 'translation': 'вода', 'transcription': '[ˈakkwa]', 'example': 'Bevo acqua.', 'part_of_speech': 'noun'},
                        {'word': 'caffè', 'translation': 'кофе', 'transcription': '[kafˈfɛ]', 'example': 'Prendo un caffè al mattino.', 'part_of_speech': 'noun'},
                        {'word': 'mela', 'translation': 'яблоко', 'transcription': '[ˈmeːla]', 'example': 'Una mela al giorno.', 'part_of_speech': 'noun'},
                        {'word': 'ristorante', 'translation': 'ресторан', 'transcription': '[ristoˈrante]', 'example': 'Andiamo al ristorante.', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_japanese_lessons(self, level):
        """Уроки для японского языка"""
        lessons = {
            'A1': [
                {
                    'title': '挨拶 (Aisatsu) - Приветствия',
                    'content': '''<h1>第1課: 挨拶 - Приветствия</h1>
                    
                    <h2>📚 レッスンの目標 - Цели урока</h2>
                    <ul>
                        <li>Основные приветствия на японском</li>
                        <li>Представление себя</li>
                        <li>Вежливые выражения</li>
                    </ul>
                    
                    <h2>👋 基本的な挨拶 - Основные приветствия</h2>
                    <div class="phrase-box">
                        <p><strong>おはようございます</strong> (Ohayō gozaimasu) - Доброе утро</p>
                        <p><strong>こんにちは</strong> (Konnichiwa) - Добрый день</p>
                        <p><strong>こんばんは</strong> (Konbanwa) - Добрый вечер</p>
                        <p><strong>さようなら</strong> (Sayōnara) - До свидания</p>
                        <p><strong>ありがとうございます</strong> (Arigatō gozaimasu) - Спасибо</p>
                        <p><strong>すみません</strong> (Sumimasen) - Извините</p>
                    </div>
                    
                    <h2>🗣️ 会話 - Диалог</h2>
                    <div class="dialogue">
                        <p><strong>田中:</strong> はじめまして。田中です。よろしくお願いします。</p>
                        <p><strong>鈴木:</strong> はじめまして。鈴木です。こちらこそよろしくお願いします。</p>
                        <p><strong>Tanaka:</strong> Hajimemashite. Tanaka desu. Yoroshiku onegaishimasu.</p>
                        <p><strong>Suzuki:</strong> Hajimemashite. Suzuki desu. Kochira koso yoroshiku onegaishimasu.</p>
                    </div>
                    
                    <h2>🔑 重要なフレーズ - Ключевые фразы</h2>
                    <ul>
                        <li><strong>はじめまして</strong> (Hajimemashite) - Приятно познакомиться</li>
                        <li><strong>私は[имя]です</strong> (Watashi wa [name] desu) - Я [имя]</li>
                        <li><strong>よろしくお願いします</strong> (Yoroshiku onegaishimasu) - Прошу любить и жаловать</li>
                    </ul>
                    
                    <div class="tip">
                        <h3>💡 Совет по произношению:</h3>
                        <p>В японском языке ударение музыкальное (тональное). Долгие гласные произносятся в два раза дольше. "は" читается как "ва" в частицах.</p>
                    </div>''',
                    'words': [
                        {'word': 'こんにちは', 'translation': 'здравствуйте', 'transcription': '[konnitiha]', 'example': 'こんにちは、お元気ですか？', 'part_of_speech': 'interjection'},
                        {'word': 'さようなら', 'translation': 'до свидания', 'transcription': '[sajoːnara]', 'example': 'さようなら、また明日！', 'part_of_speech': 'interjection'},
                        {'word': 'ありがとう', 'translation': 'спасибо', 'transcription': '[arigatoː]', 'example': 'ありがとうございます。', 'part_of_speech': 'noun'},
                        {'word': '名前', 'translation': 'имя', 'transcription': '[namae]', 'example': '私の名前は田中です。', 'part_of_speech': 'noun'},
                        {'word': '友達', 'translation': 'друг', 'transcription': '[tomodachi]', 'example': '彼は私の友達です。', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': '家族 (Kazoku) - Семья',
                    'content': '''<h1>第2課: 家族 - Семья</h1>
                    
                    <h2>👨‍👩‍👧‍👦 家族のメンバー - Члены семьи</h2>
                    <table class="table">
                        <tr><th>日本語</th><th>Русский</th></tr>
                        <tr><td>母 (haha) / お母さん (okāsan)</td><td>мама</td></tr>
                        <tr><td>父 (chichi) / お父さん (otōsan)</td><td>папа</td></tr>
                        <tr><td>兄 (ani) / お兄さん (oniisan)</td><td>старший брат</td></tr>
                        <tr><td>弟 (otōto)</td><td>младший брат</td></tr>
                        <tr><td>姉 (ane) / お姉さん (onēsan)</td><td>старшая сестра</td></tr>
                        <tr><td>妹 (imōto)</td><td>младшая сестра</td></tr>
                        <tr><td>祖母 (sobo) / お祖母さん (obāsan)</td><td>бабушка</td></tr>
                        <tr><td>祖父 (sofu) / お祖父さん (ojīsan)</td><td>дедушка</td></tr>
                    </table>''',
                    'words': [
                        {'word': '家族', 'translation': 'семья', 'transcription': '[kazoku]', 'example': '私の家族は5人です。', 'part_of_speech': 'noun'},
                        {'word': '母', 'translation': 'мама', 'transcription': '[haha]', 'example': '母は医者です。', 'part_of_speech': 'noun'},
                        {'word': '父', 'translation': 'папа', 'transcription': '[chichi]', 'example': '父は会社員です。', 'part_of_speech': 'noun'},
                        {'word': '兄', 'translation': 'брат', 'transcription': '[ani]', 'example': '兄がいます。', 'part_of_speech': 'noun'},
                        {'word': '妹', 'translation': 'сестра', 'transcription': '[imōto]', 'example': '妹は学生です。', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': '数字 (Sūji) - Числа',
                    'content': '''<h1>第3課: 数字 - Числа</h1>
                    
                    <h2>🔢 数字1-10</h2>
                    <p>1 - 一 (ichi), 2 - 二 (ni), 3 - 三 (san), 4 - 四 (shi/yon), 5 - 五 (go), 6 - 六 (roku), 7 - 七 (shichi/nana), 8 - 八 (hachi), 9 - 九 (kyū/ku), 10 - 十 (jū)</p>
                    
                    <h2>🎂 年齢 - Возраст</h2>
                    <p><strong>何歳ですか？</strong> (Nan-sai desu ka?) - Сколько вам лет?</p>
                    <p><strong>〜歳です</strong> (〜sai desu) - Мне ... лет</p>''',
                    'words': [
                        {'word': '一', 'translation': 'один', 'transcription': '[ichi]', 'example': '猫が一匹います。', 'part_of_speech': 'numeral'},
                        {'word': '二', 'translation': 'два', 'transcription': '[ni]', 'example': '兄弟が二人います。', 'part_of_speech': 'numeral'},
                        {'word': '三', 'translation': 'три', 'transcription': '[san]', 'example': 'リンゴを三個食べました。', 'part_of_speech': 'numeral'},
                        {'word': '歳', 'translation': 'лет', 'transcription': '[sai]', 'example': '25歳です。', 'part_of_speech': 'noun'},
                        {'word': '年', 'translation': 'год', 'transcription': '[toshi]', 'example': '私は25年です。', 'part_of_speech': 'noun'}
                    ]
                },
                {
                    'title': '色 (Iro) - Цвета',
                    'content': '''<h1>第4課: 色 - Цвета</h1>
                    
                    <h2>🎨 基本的な色 - Основные цвета</h2>
                    <ul>
                        <li><span style="color: red;">赤 (aka)</span> - красный</li>
                        <li><span style="color: blue;">青 (ao)</span> - синий</li>
                        <li><span style="color: green;">緑 (midori)</span> - зеленый</li>
                        <li><span style="color: yellow;">黄色 (kiiro)</span> - желтый</li>
                        <li><span style="color: black;">黒 (kuro)</span> - черный</li>
                        <li><span style="color: white;">白 (shiro)</span> - белый</li>
                        <li>オレンジ (orenji) - оранжевый</li>
                        <li>紫 (murasaki) - фиолетовый</li>
                        <li>ピンク (pinku) - розовый</li>
                        <li>茶色 (chairo) - коричневый</li>
                    </ul>''',
                    'words': [
                        {'word': '赤', 'translation': 'красный', 'transcription': '[aka]', 'example': 'リンゴは赤いです。', 'part_of_speech': 'adjective'},
                        {'word': '青', 'translation': 'синий', 'transcription': '[ao]', 'example': '空は青いです。', 'part_of_speech': 'adjective'},
                        {'word': '緑', 'translation': 'зеленый', 'transcription': '[midori]', 'example': '草は緑です。', 'part_of_speech': 'adjective'},
                        {'word': '黄色', 'translation': 'желтый', 'transcription': '[kiiro]', 'example': '太陽は黄色いです。', 'part_of_speech': 'adjective'},
                        {'word': '黒', 'translation': 'черный', 'transcription': '[kuro]', 'example': '私の車は黒いです。', 'part_of_speech': 'adjective'}
                    ]
                },
                {
                    'title': '食べ物と飲み物 (Tabemono to Nomimono) - Еда и напитки',
                    'content': '''<h1>第5課: 食べ物と飲み物 - Еда и напитки</h1>
                    
                    <h2>🍎 食べ物 - Еда</h2>
                    <ul>
                        <li>パン (pan) - хлеб</li>
                        <li>ご飯 (gohan) - рис</li>
                        <li>味噌汁 (misoshiru) - суп мисо</li>
                        <li>寿司 (sushi) - суши</li>
                        <li>刺身 (sashimi) - сашими</li>
                        <li>天ぷら (tempura) - темпура</li>
                    </ul>
                    
                    <h2>☕ 飲み物 - Напитки</h2>
                    <ul>
                        <li>水 (mizu) - вода</li>
                        <li>お茶 (ocha) - чай</li>
                        <li>コーヒー (kōhī) - кофе</li>
                        <li>ジュース (jūsu) - сок</li>
                        <li>酒 (sake) - сакэ</li>
                    </ul>''',
                    'words': [
                        {'word': 'パン', 'translation': 'хлеб', 'transcription': '[pan]', 'example': '毎日パンを食べます。', 'part_of_speech': 'noun'},
                        {'word': '水', 'translation': 'вода', 'transcription': '[mizu]', 'example': '水を飲みます。', 'part_of_speech': 'noun'},
                        {'word': 'コーヒー', 'translation': 'кофе', 'transcription': '[kōhī]', 'example': '朝コーヒーを飲みます。', 'part_of_speech': 'noun'},
                        {'word': '寿司', 'translation': 'суши', 'transcription': '[sushi]', 'example': '寿司が大好きです。', 'part_of_speech': 'noun'},
                        {'word': 'レストラン', 'translation': 'ресторан', 'transcription': '[resutoran]', 'example': 'レストランに行きましょう。', 'part_of_speech': 'noun'}
                    ]
                }
            ]
        }
        return lessons.get(level, lessons['A1'])

    def get_general_lessons(self, language_name, level):
        """Общие уроки для других языков (если не найдены специфичные)"""
        return [
            {
                'title': f'Greetings and Introductions',
                'content': f'<h1>Lesson 1: Greetings and Introductions</h1><p>Learn basic greetings in {language_name}.</p>',
                'words': [
                    {'word': 'hello', 'translation': f'hello in {language_name}', 'example': 'Hello!', 'part_of_speech': 'interjection'},
                    {'word': 'goodbye', 'translation': f'goodbye in {language_name}', 'example': 'Goodbye!', 'part_of_speech': 'interjection'},
                    {'word': 'thank you', 'translation': f'thank you in {language_name}', 'example': 'Thank you!', 'part_of_speech': 'noun'},
                    {'word': 'name', 'translation': f'name in {language_name}', 'example': 'My name is...', 'part_of_speech': 'noun'},
                    {'word': 'friend', 'translation': f'friend in {language_name}', 'example': 'He is my friend.', 'part_of_speech': 'noun'}
                ]
            },
            {
                'title': f'Family',
                'content': f'<h1>Lesson 2: Family</h1><p>Learn family members in {language_name}.</p>',
                'words': [
                    {'word': 'family', 'translation': f'family in {language_name}', 'example': 'My family is big.', 'part_of_speech': 'noun'},
                    {'word': 'mother', 'translation': f'mother in {language_name}', 'example': 'My mother is a teacher.', 'part_of_speech': 'noun'},
                    {'word': 'father', 'translation': f'father in {language_name}', 'example': 'My father works.', 'part_of_speech': 'noun'},
                    {'word': 'brother', 'translation': f'brother in {language_name}', 'example': 'I have a brother.', 'part_of_speech': 'noun'},
                    {'word': 'sister', 'translation': f'sister in {language_name}', 'example': 'My sister is young.', 'part_of_speech': 'noun'}
                ]
            },
            {
                'title': f'Numbers',
                'content': f'<h1>Lesson 3: Numbers</h1><p>Learn numbers in {language_name}.</p>',
                'words': [
                    {'word': 'one', 'translation': f'one in {language_name}', 'example': 'One apple.', 'part_of_speech': 'numeral'},
                    {'word': 'two', 'translation': f'two in {language_name}', 'example': 'Two books.', 'part_of_speech': 'numeral'},
                    {'word': 'three', 'translation': f'three in {language_name}', 'example': 'Three cats.', 'part_of_speech': 'numeral'},
                    {'word': 'age', 'translation': f'age in {language_name}', 'example': 'How old are you?', 'part_of_speech': 'noun'},
                    {'word': 'years', 'translation': f'years in {language_name}', 'example': 'I am 25 years old.', 'part_of_speech': 'noun'}
                ]
            },
            {
                'title': f'Colors',
                'content': f'<h1>Lesson 4: Colors</h1><p>Learn colors in {language_name}.</p>',
                'words': [
                    {'word': 'red', 'translation': f'red in {language_name}', 'example': 'The apple is red.', 'part_of_speech': 'adjective'},
                    {'word': 'blue', 'translation': f'blue in {language_name}', 'example': 'The sky is blue.', 'part_of_speech': 'adjective'},
                    {'word': 'green', 'translation': f'green in {language_name}', 'example': 'The grass is green.', 'part_of_speech': 'adjective'},
                    {'word': 'yellow', 'translation': f'yellow in {language_name}', 'example': 'The sun is yellow.', 'part_of_speech': 'adjective'},
                    {'word': 'black', 'translation': f'black in {language_name}', 'example': 'My car is black.', 'part_of_speech': 'adjective'}
                ]
            },
            {
                'title': f'Food and Drinks',
                'content': f'<h1>Lesson 5: Food and Drinks</h1><p>Learn food vocabulary in {language_name}.</p>',
                'words': [
                    {'word': 'bread', 'translation': f'bread in {language_name}', 'example': 'I eat bread.', 'part_of_speech': 'noun'},
                    {'word': 'water', 'translation': f'water in {language_name}', 'example': 'Drink water.', 'part_of_speech': 'noun'},
                    {'word': 'coffee', 'translation': f'coffee in {language_name}', 'example': 'I drink coffee.', 'part_of_speech': 'noun'},
                    {'word': 'apple', 'translation': f'apple in {language_name}', 'example': 'An apple a day.', 'part_of_speech': 'noun'},
                    {'word': 'restaurant', 'translation': f'restaurant in {language_name}', 'example': 'Go to restaurant.', 'part_of_speech': 'noun'}
                ]
            }
        ]

    def create_comprehensive_test_for_lesson(self, lesson):
        """Создает полноценный тест для урока с 10 вопросами"""
        test = Test.objects.create(
            lesson=lesson,
            title=f'Тест: {lesson.title}'
        )
        
        words = list(lesson.words.all())
        
        # Создаем 10 разнообразных вопросов
        questions_created = 0
        
        # Вопрос 1: Выбор правильного перевода
        if words and questions_created < 10:
            word = random.choice(words)
            question = Question.objects.create(
                test=test,
                text=f'Как переводится слово "{word.word}"?'
            )
            # Правильный ответ
            Answer.objects.create(question=question, text=word.translation, is_correct=True)
            # Неправильные ответы
            wrong_options = self.generate_wrong_translations(word.translation, words)
            for wrong in wrong_options[:4]:
                Answer.objects.create(question=question, text=wrong, is_correct=False)
            questions_created += 1
        
        # Вопрос 2: Выбор слова по переводу
        if len(words) > 1 and questions_created < 10:
            word = random.choice([w for w in words if w != word])
            question = Question.objects.create(
                test=test,
                text=f'Какое слово соответствует переводу "{word.translation}"?'
            )
            Answer.objects.create(question=question, text=word.word, is_correct=True)
            wrong_words = self.generate_wrong_words(word.word, [w.word for w in words])
            for wrong in wrong_words[:4]:
                Answer.objects.create(question=question, text=wrong, is_correct=False)
            questions_created += 1
        
        # Вопрос 3: Заполнение пропуска в предложении
        if len(words) > 2 and questions_created < 10:
            word = random.choice(words)
            if word.example and len(word.example) > 10:
                # Создаем предложение с пропуском
                example_words = word.example.split()
                if len(example_words) > 3:
                    # Заменяем случайное слово кроме первого и последнего
                    replace_idx = random.randint(1, len(example_words)-2)
                    example_words[replace_idx] = '__________'
                    question_text = ' '.join(example_words)
                    
                    question = Question.objects.create(
                        test=test,
                        text=f'Заполните пропуск: "{question_text}"'
                    )
                    Answer.objects.create(question=question, text=word.word, is_correct=True)
                    wrong_words = self.generate_wrong_words(word.word, [w.word for w in words])
                    for wrong in wrong_words[:4]:
                        Answer.objects.create(question=question, text=wrong, is_correct=False)
                    questions_created += 1
        
        # Добавляем дополнительные вопросы чтобы было 10
        while questions_created < 10 and words:
            word = random.choice(words)
            question_type = random.choice(['translation', 'word_choice', 'example'])
            
            if question_type == 'translation':
                question = Question.objects.create(
                    test=test,
                    text=f'Выберите правильный перевод для слова "{word.word}":'
                )
                Answer.objects.create(question=question, text=word.translation, is_correct=True)
                wrong_options = self.generate_wrong_translations(word.translation, words)
                for wrong in wrong_options[:4]:
                    Answer.objects.create(question=question, text=wrong, is_correct=False)
            
            elif question_type == 'word_choice':
                question = Question.objects.create(
                    test=test,
                    text=f'Какое слово означает "{word.translation}"?'
                )
                Answer.objects.create(question=question, text=word.word, is_correct=True)
                wrong_words = self.generate_wrong_words(word.word, [w.word for w in words])
                for wrong in wrong_words[:4]:
                    Answer.objects.create(question=question, text=wrong, is_correct=False)
            
            else:
                if word.example:
                    question = Question.objects.create(
                        test=test,
                        text=f'В каком предложении правильно используется слово "{word.word}"?'
                    )
                    Answer.objects.create(question=question, text=word.example, is_correct=True)
                    
                    # Генерируем неправильные примеры
                    wrong_examples = []
                    for w in words:
                        if w != word and w.example:
                            wrong_examples.append(w.example)
                    
                    while len(wrong_examples) < 4:
                        wrong_examples.append(self.generate_wrong_example(word.word))
                    
                    for wrong in wrong_examples[:4]:
                        Answer.objects.create(question=question, text=wrong, is_correct=False)
            
            questions_created += 1
        
        return test

    def generate_wrong_translations(self, correct_translation, words):
        """Генерирует неправильные варианты перевода"""
        wrong_options = []
        
        # Берем переводы других слов из урока
        other_translations = [w.translation for w in words if w.translation != correct_translation]
        if other_translations:
            wrong_options.extend(random.sample(other_translations, min(3, len(other_translations))))
        
        # Добавляем общие неправильные варианты
        common_wrong = ['привет', 'пока', 'да', 'нет', 'хорошо', 'плохо']
        wrong_options.extend(random.sample(common_wrong, min(2, len(common_wrong))))
        
        # Уникализируем и ограничиваем
        wrong_options = list(set(wrong_options))
        random.shuffle(wrong_options)
        
        return wrong_options[:5]

    def generate_wrong_words(self, correct_word, all_words):
        """Генерирует неправильные варианты слов"""
        wrong_words = []
        
        # Берем другие слова из урока
        other_words = [w for w in all_words if w != correct_word]
        if other_words:
            wrong_words.extend(random.sample(other_words, min(3, len(other_words))))
        
        # Добавляем похожие по написанию слова
        similar_words = [f'{correct_word}1', f'{correct_word}2', f'{correct_word}3']
        wrong_words.extend(similar_words)
        
        # Уникализируем и перемешиваем
        wrong_words = list(set(wrong_words))
        random.shuffle(wrong_words)
        
        return wrong_words[:5]

    def generate_wrong_example(self, word):
        """Генерирует неправильный пример использования слова"""
        wrong_examples = [
            f"I {word} to school every day.",
            f"My {word} is very big.",
            f"Can you {word} me?",
            f"The {word} is interesting.",
            f"I don't like to {word}."
        ]
        return random.choice(wrong_examples)

    def print_statistics(self):
        """Выводит статистику созданных данных"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('СТАТИСТИКА СОЗДАННЫХ ДАННЫХ:')
        self.stdout.write('=' * 60)
        
        stats = [
            ('Языки', Language.objects.count()),
            ('Курсы', Course.objects.count()),
            ('Уроки', Lesson.objects.count()),
            ('Слова', Word.objects.count()),
            ('Тесты', Test.objects.count()),
            ('Вопросы', Question.objects.count()),
            ('Ответы', Answer.objects.count())
        ]
        
        for name, count in stats:
            self.stdout.write(f'  {name:15} {count:5} шт.')
        
        # Дополнительная статистика
        self.stdout.write('\nДетализация по языкам:')
        for language in Language.objects.all():
            course_count = language.courses.count()
            lesson_count = sum(course.lessons.count() for course in language.courses.all())
            word_count = sum(lesson.words.count() for course in language.courses.all() for lesson in course.lessons.all())
            self.stdout.write(f'  {language.name:15} {course_count:2} курсов, {lesson_count:3} уроков, {word_count:4} слов')