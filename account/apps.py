__author__ = 'bondarenkoav'

from django.apps import AppConfig

class AccountAppConfig(AppConfig):
    name = "account" # Здесь указываем исходное имя приложения
    verbose_name = "Профили пользователей" # А здесь, имя которое необходимо отобразить в админке