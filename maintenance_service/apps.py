__author__ = 'bondarenkoav'

from django.apps import AppConfig

class MaintenanceServiceAppConfig(AppConfig):
    name = "maintenance_service" # Здесь указываем исходное имя приложения
    verbose_name = "Техническое обслуживание" # А здесь, имя которое необходимо отобразить в админке