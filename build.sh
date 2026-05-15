#!/usr/bin/env bash
# build.sh - скрипт сборки для Render

echo "Начинаем сборку проекта..."

# Установка зависимостей
echo "Установка зависимостей..."
pip install -r requirements.txt

# Сбор статики
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

# Применение миграций
echo "Применение миграций базы данных..."
python manage.py migrate

echo "Сборка завершена успешно!"