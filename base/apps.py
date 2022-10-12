__author__ = 'bondarenkoav'

from django.apps import AppConfig

class BaseAppConfig(AppConfig):
    name = "base" # Здесь указываем исходное имя приложения
    verbose_name = "Базовое приложение" # А здесь, имя которое необходимо отобразить в админке