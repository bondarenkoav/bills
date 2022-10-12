# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from base.models import SectionsApp


class notification(models.Model):
    section = models.ForeignKey(SectionsApp, verbose_name='Раздел', on_delete=models.CASCADE)
    note = models.TextField(u'Сообщения')
    responsible = models.ForeignKey(User, verbose_name='Получатель', on_delete=models.CASCADE)
    limitation = models.DateTimeField(u'Срок исполнения', blank=True, null=True)
    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    read = models.BooleanField(u'Прочитано', default=False)

    def __str__(self):
        return self.section.name

    class Meta:
        verbose_name = u'Уведомление '
        verbose_name_plural = u'Список уведомлений '
