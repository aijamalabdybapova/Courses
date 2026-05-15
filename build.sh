#!/usr/bin/env bash
echo " Начинаем сборку проекта..."

# Установка зависимостей
echo " Установка зависимостей..."
pip install -r requirements.txt

# Сбор статики
echo " Сбор статических файлов..."
python manage.py collectstatic --noinput

# Применение миграций
echo " Применение миграций базы данных..."
python manage.py migrate

# Загрузка ВСЕХ данных (сначала full_dump, потом users_dump как резерв)
if [ -f "full_dump.json" ]; then
    echo " Загрузка ВСЕХ данных из full_dump.json..."
    python manage.py loaddata full_dump.json
    echo " Все данные (пользователи, курсы, уроки, тесты, чаты) загружены!"
elif [ -f "users_dump.json" ]; then
    echo " full_dump.json не найден, загружаем только пользователей..."
    python manage.py loaddata users_dump.json
else
    echo " Файлы с данными не найдены, создаем только структуру БД"
fi

echo " Сборка завершена!"