# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models


class type_notification(models.Model):  # СМС на телефон, письмо на ящик, внутрисистемное уведомление, не уведомлять
    name = models.CharField(u'Тип уведомления', max_length=30, unique=True)
    slug = models.SlugField(u'Ключ', unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'Тип '
        verbose_name_plural = u'Типы уведомлений '


class user_task(models.Model):
    title = models.CharField(u'Заголовок задачи', max_length=100)
    description = models.TextField(u'Описание задачи')
    responsible = models.ManyToManyField(User, verbose_name='Исполнитель')
    limitation = models.DateTimeField(u'Срок исполнения')
    high_importance = models.BooleanField(u'Высокая важность', default=False)
    notification = models.ForeignKey(type_notification, models.SET_NULL, null=True,
                                     verbose_name='Уведомить о действиях над задачей')
    Create_user = models.IntegerField(u'Автор')
    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)
    read = models.BooleanField(u'Просмотренно исполнителем', default=False)
    done = models.BooleanField(u'Задача выполнена', default=False)
    done_description = models.TextField(u'Описание выполнения', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = u'Задача '
        verbose_name_plural = u'Список задач '