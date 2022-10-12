import datetime

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django_currentuser.db.models import CurrentUserField
from excel_response import ExcelResponse

from base.models import Branch, ServingCompanyBranch
from django_group_by import GroupByMixin
from reference_books.models import TypeDocument, PaymentMethods


class credited_with_paidQuerySet(QuerySet, GroupByMixin):
    pass


class credited_with_paid(models.Model):  # начислено и оплачено
    objects = credited_with_paidQuerySet.as_manager()
    object = models.IntegerField(verbose_name=u'Объект', blank=True, null=True)
    dct = models.IntegerField(verbose_name=u'Документ', blank=True, null=True)
    type_dct = models.ForeignKey(TypeDocument, models.SET_NULL, verbose_name=u'Тип документ',
                                 blank=True, null=True)
    branch = models.ForeignKey(Branch, verbose_name=u'Клиент', on_delete=models.CASCADE)
    scompany = models.ForeignKey(ServingCompanyBranch, verbose_name=u'Сервисная компания', on_delete=models.CASCADE)
    date_event = models.DateField(u'Дата начисления', blank=True, null=True)
    payment_methods = models.ForeignKey(PaymentMethods, models.SET_NULL, verbose_name='Способ оплаты',
                                        blank=True, null=True)
    accural_methods = models.CharField(u'Способ начисления', max_length=10, blank=True, null=True)
    summ = models.DecimalField(u'Сумма', max_digits=9, decimal_places=2, help_text='Оплата - со знаком "-"')

    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_acp')
    Update_user = CurrentUserField(related_name='update_by_acp')

    class Meta:
        verbose_name = u'Начисление/Оплата '
        verbose_name_plural = u'Расчёты с клиентами '
        permissions = (
            ('cwp_list_view', u'БухРасчёты.Просмотр списка'),
            ('cwp_item_view', u'БухРасчёты.Просмотр записи'),
            ('cwp_item_add', u'БухРасчёты.Добавить запись'),
            ('cwp_item_edit', u'БухРасчёты.Изменить запись'),
            ('cwp_saldo_view', u'БухРасчёты.Просмотр сальдо'),
            ('cwp_actsverki_view', u'БухРасчёты.Акт сверки'),
        )


class start_balance(models.Model):
    branch = models.ForeignKey(Branch, verbose_name=u'Клиент', on_delete=models.CASCADE)
    scompany = models.ForeignKey(ServingCompanyBranch, verbose_name=u'Сервисная компания', on_delete=models.CASCADE)
    summ = models.DecimalField(u'Сумма', max_digits=15, decimal_places=2, help_text=u'Переплата - со знаком "-"')
    date_saldo = models.DateField(u'Дата начала расчета')
    city = models.CharField(max_length=20)

    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_asb')
    Update_user = CurrentUserField(related_name='update_by_asb')

    def __str__(self):
        return self.branch.Client.NameClient_short

    class Meta:
        verbose_name = u'Сальдо'
        verbose_name_plural = u'Начальное сальдо'
        permissions = (
            ('sb_item_view', u'НачСальдо.Просмотр записи'),
            ('sb_item_edit', u'НачСальдо.Изменить запись'),
        )


class AccountingTemplates(models.Model):  # Шаблоны документов
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    slug = models.SlugField(u'Ключ категории')
    TextTemplate = RichTextField(u'Текст шаблона')

    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_at')
    Update_user = CurrentUserField(related_name='update_by_at')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон '
        verbose_name_plural = u'Шаблоны документов '


class saldobranch(models.Model):
    scompany_id = models.IntegerField()
    client_name = models.CharField(max_length=300)
    branch_name = models.CharField(max_length=300)
    phone_sms = models.CharField(max_length=20)
    saldo = models.DecimalField(max_digits=10, decimal_places=2)
    type_client = models.CharField(max_length=20)

    class Meta:
        managed = False


class saldotoday(models.Model):
    scompany_id = models.IntegerField()
    saldo_today = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False


class temp_export_object_to1S_object(models.Model):
    address = models.CharField(max_length=300)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = u'Объект '
        verbose_name_plural = u'Список объектов для выгрузки в 1С '


class temp_export_object_to1S_client(models.Model):
    inn = models.IntegerField()
    name_client = models.CharField(max_length=300)
    object = models.ManyToManyField(temp_export_object_to1S_object)
    edo = models.BooleanField(default=False)
    contract = models.CharField(max_length=100)

    def __str__(self):
        return self.name_client

    class Meta:
        verbose_name = u'Клиент '
        verbose_name_plural = u'Список клиентов для выгрузки в 1С '


class temp_export_bankpayments_from1C(models.Model):
    date_entry = models.DateField()
    client_name = models.CharField(max_length=300)
    client_inn = models.CharField(max_length=20)
    client_kpp = models.CharField(max_length=20, null=True)
    summ = models.DecimalField(max_digits=10, decimal_places=2)
    contract_number = models.CharField(max_length=100, null=True)
    contract_date = models.DateField(null=True)
    scompany_inn = models.CharField(max_length=20)
    scompany_kpp = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.client_name

    class Meta:
        verbose_name = u'Платёж '
        verbose_name_plural = u'Платежи банковские из 1С '


