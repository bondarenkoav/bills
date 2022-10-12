from django.contrib import admin
from tasks.models import user_task, type_notification


class UserTasksAdmin(admin.ModelAdmin):
    list_display = ['title', 'limitation', 'DateTime_add', 'DateTime_update','done']
    filter = ['DateTime_add','Create_user','done']

admin.site.register(user_task,UserTasksAdmin)
admin.site.register(type_notification)