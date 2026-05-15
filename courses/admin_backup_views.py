# courses/admin_backup_views.py
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from .backup_utils import (
    create_database_backup, get_backup_list, restore_database, delete_backup
)
import os

@staff_member_required
def admin_backup(request):
    """Страница управления резервным копированием"""
    backups = get_backup_list()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            backup_file, timestamp = create_database_backup()
            messages.success(request, f'Резервная копия создана: db_backup_{timestamp}.zip')
            return redirect('admin_backup')
        
        elif action == 'restore':
            backup_name = request.POST.get('backup_name')
            backup_path = os.path.join(os.path.dirname(backup_name), backup_name)
            success, message = restore_database(backup_path)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('admin_backup')
        
        elif action == 'delete':
            backup_name = request.POST.get('backup_name')
            success, message = delete_backup(backup_name)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('admin_backup')
        
        elif action == 'download':
            backup_name = request.POST.get('backup_name')
            backup_dir = os.path.dirname(os.path.dirname(__file__))
            file_path = os.path.join(backup_dir, 'backups', backup_name)
            if os.path.exists(file_path):
                response = FileResponse(open(file_path, 'rb'), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{backup_name}"'
                return response
            else:
                messages.error(request, 'Файл не найден')
                return redirect('admin_backup')
    
    context = {
        'backups': backups,
        'total_backups': len(backups),
        'total_size': sum(b['size'] for b in backups),
        'total_size_mb': round(sum(b['size'] for b in backups) / 1024 / 1024, 2)
    }
    return render(request, 'courses/admin/backup.html', context)