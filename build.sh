#!/usr/bin/env bash
# Создание скрипта сборки для Render

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate