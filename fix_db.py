# fix_db.py
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

django.setup()

from django.db import connection

def delete_problem_tables():
    """Удаляем только проблемные таблицы"""
    with connection.cursor() as cursor:
        tables_to_drop = [
            'courses_leveltest',
            'courses_leveltestquestion', 
            'courses_leveltestanswer',
            'courses_userleveltestresult'
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                print(f'✓ Таблица {table} удалена')
            except Exception as e:
                print(f'✗ Ошибка при удалении {table}: {e}')
    
    print("\nГотово! Таблицы удалены.")

if __name__ == '__main__':
    delete_problem_tables()