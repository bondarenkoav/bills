__author__ = 'bondarenkoav'

from django.apps import AppConfig

class AccountingAppConfig(AppConfig):
    name = "accounting" # Здесь указываем исходное имя приложения
    verbose_name = "Бухгалтерия" # А здесь, имя которое необходимо отобразить в админке