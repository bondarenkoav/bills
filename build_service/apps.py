__author__ = 'bondarenkoav'

from django.apps import AppConfig

class BuildServiceAppConfig(AppConfig):
    name = "build_service" # Здесь указываем исходное имя приложения
    verbose_name = "Монтаж" # А здесь, имя которое необходимо отобразить в админке