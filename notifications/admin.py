from django.contrib import admin
from .models import notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['section', 'note', 'responsible', 'limitation', 'DateTime_add','read']
    filter = ['responsible','read','DateTime_add']

admin.site.register(notification,NotificationAdmin)