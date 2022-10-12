__author__ = 'bondarenkoav'

from django.apps import AppConfig

class ReferenceBooksAppConfig(AppConfig):
    name = "reference_books" # Здесь указываем исходное имя приложения
    verbose_name = "Справочники" # А здесь, имя которое необходимо отобразить в админке