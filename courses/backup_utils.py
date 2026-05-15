# courses/backup_utils.py
import os
import json
import zipfile
from datetime import datetime
from django.conf import settings
from django.core import serializers
from django.apps import apps
from django.db import connection

def get_backup_dir():
    """Получить директорию для резервных копий"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def create_database_backup():
    """Создать резервную копию базы данных"""
    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Создаем файл резервной копии данных
    backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
    
    # Модели для бэкапа
    models_to_backup = [
        'Language', 'Course', 'Lesson', 'Word', 'Test', 
        'Question', 'Answer', 'UserProfile', 'UserWord', 
        'Progress', 'TestResult', 'ModeratorStudent', 'ModeratorNote',
        'ChatRoom', 'ChatMessage', 'LevelTest', 'LevelTestQuestion', 
        'LevelTestAnswer', 'UserLevelTestResult'
    ]
    
    backup_data = {}
    
    for model_name in models_to_backup:
        try:
            model = apps.get_model('courses', model_name)
            data = serializers.serialize('json', model.objects.all())
            backup_data[model_name] = json.loads(data)
            print(f"✓ Бэкап модели {model_name}: {model.objects.count()} записей")
        except Exception as e:
            print(f"✗ Ошибка при бэкапе {model_name}: {e}")
            backup_data[model_name] = []
    
    # Сохраняем в файл
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    # Создаем zip архив
    zip_file = os.path.join(backup_dir, f'db_backup_{timestamp}.zip')
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(backup_file, os.path.basename(backup_file))
    
    # Удаляем временный JSON файл
    os.remove(backup_file)
    
    return zip_file, timestamp

def get_backup_list():
    """Получить список всех резервных копий"""
    backup_dir = get_backup_dir()
    backups = []
    
    for file in os.listdir(backup_dir):
        if file.endswith('.zip') and file.startswith('db_backup_'):
            file_path = os.path.join(backup_dir, file)
            file_size = os.path.getsize(file_path)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            backups.append({
                'name': file,
                'path': file_path,
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'created': file_time,
                'created_str': file_time.strftime('%d.%m.%Y %H:%M:%S')
            })
    
    # Сортируем по дате (новые сверху)
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def restore_database(backup_file):
    """Восстановить базу данных из резервной копии"""
    try:
        with zipfile.ZipFile(backup_file, 'r') as zf:
            # Извлекаем JSON файл
            json_name = zf.namelist()[0]
            zf.extractall(get_backup_dir())
            json_path = os.path.join(get_backup_dir(), json_name)
        
        # Загружаем данные
        with open(json_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Очищаем существующие данные
        models_to_clear = [
            'UserLevelTestResult', 'LevelTestAnswer', 'LevelTestQuestion',
            'LevelTest', 'ChatMessage', 'ChatRoom', 'ModeratorNote',
            'ModeratorStudent', 'TestResult', 'Progress', 'UserWord',
            'Answer', 'Question', 'Test', 'Word', 'Lesson', 'Course', 'Language'
        ]
        
        for model_name in models_to_clear:
            try:
                model = apps.get_model('courses', model_name)
                model.objects.all().delete()
                print(f"✓ Очищена модель {model_name}")
            except Exception as e:
                print(f"✗ Ошибка при очистке {model_name}: {e}")
        
        # Восстанавливаем данные
        for model_name, data in backup_data.items():
            if data:
                try:
                    model = apps.get_model('courses', model_name)
                    for obj_data in data:
                        # Удаляем id и created_at для правильного восстановления
                        if 'pk' in obj_data:
                            del obj_data['pk']
                        if 'fields' in obj_data and 'created_at' in obj_data['fields']:
                            del obj_data['fields']['created_at']
                        if 'fields' in obj_data and 'updated_at' in obj_data['fields']:
                            del obj_data['fields']['updated_at']
                        
                        # Создаем объект
                        new_obj = model(**obj_data['fields'])
                        new_obj.save()
                    print(f"✓ Восстановлена модель {model_name}: {len(data)} записей")
                except Exception as e:
                    print(f"✗ Ошибка при восстановлении {model_name}: {e}")
        
        # Удаляем временный JSON файл
        os.remove(json_path)
        
        return True, "База данных успешно восстановлена"
    except Exception as e:
        return False, f"Ошибка при восстановлении: {str(e)}"

def delete_backup(backup_name):
    """Удалить файл резервной копии"""
    backup_dir = get_backup_dir()
    file_path = os.path.join(backup_dir, backup_name)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True, f"Файл {backup_name} удален"
    return False, "Файл не найден"