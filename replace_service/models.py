from ckeditor.fields import RichTextField
from django.db import models

from django_currentuser.db.models import CurrentUserField

from base.models import Branch, ServingCompanyBranch, TypeDocument, CoWorkers
from reference_books.models import TypeObject, City, TypeWork


class ReplaceTemplateDocuments(models.Model):  # Шаблоны документов
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон документа '
        verbose_name_plural = u'Шаблоны документов '


class ReplaceServiceContract(models.Model):  # Договора замены
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    NumContractInternal = models.CharField(u'Номер внутренний', max_length=30)
    NumContractBranch = models.CharField(u'Номер клиентский', max_length=30, blank=True)
    DateConclusion = models.DateField(u'Дата заключения')
    DateTermination = models.DateField(u'Дата расторжения', null=True, blank=True)
    TemplateDocuments = models.ForeignKey(ReplaceTemplateDocuments, models.SET_NULL, null=True,
                                          verbose_name='Тип бланка договора')
    PaymentDate = models.IntegerField(u'Срок оплаты, дней', default=0,
                                      help_text='0 - предоплата или количество дней отсрочки')
    NameOfService = models.TextField(u'Наименование услуги', blank=True)
    ReturnedSigned = models.BooleanField(u'Договор подписан', help_text="Договор возвращен подписанным контрагентом",
                                         default=False)
    AmountLimit = models.DecimalField(u'Предельная сумма договора', max_digits=10, decimal_places=2, default=0)
    DoNotIncludeInCalculations = models.BooleanField(u'Не выводить в расчеты', default=False)
    Notes = models.TextField(u'Комментарии', blank=True, null=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_rsc')
    Update_user = CurrentUserField(related_name='update_by_rsc')

    def __str__(self):
        return self.NumContractInternal

    class Meta:
        verbose_name = u'Договор '
        verbose_name_plural = u'Договора замен по актам '
        permissions = (
            ('contract_list_view', u'ЗаменыДоговор.Просмотр списка'),
            ('contract_item_view', u'ЗаменыДоговор.Просмотр записи'),
            ('contract_item_add', u'ЗаменыДоговор.Добавить запись'),
            ('contract_item_edit', u'ЗаменыДоговор.Изменить запись'),
        )


class ReplaceServiceObject(models.Model):
    ReplaceServiceContract = models.ForeignKey(ReplaceServiceContract, verbose_name='Договор', on_delete=models.CASCADE)
    TypeObject = models.ForeignKey(TypeObject, models.SET_NULL, null=True, verbose_name='Тип объекта')
    NameObject = models.CharField(u'Описание', max_length=300)
    AddressObject = models.CharField(u'Адрес', max_length=500)
    CityObject = models.ForeignKey(City, models.SET_NULL, verbose_name='Город/Нас.пункт', null=True, blank=True)
    ActiveObject = models.BooleanField(u'Активный объект', default=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_rso')
    Update_user = CurrentUserField(related_name='update_by_rso')

    def __str__(self):
        return self.NameObject + ' (' + self.AddressObject + ')'

    class Meta:
        verbose_name = u'Объект '
        verbose_name_plural = u'Объекты договора замены'
        permissions = (
            ('object_list_view', u'ЗаменыОбъект.Просмотр списка'),
            ('object_item_view', u'ЗаменыОбъект.Просмотр записи'),
            ('object_item_add', u'ЗаменыОбъект.Добавить запись'),
            ('object_item_edit', u'ЗаменыОбъект.Изменить запись'),
        )


class ReplaceServiceAct(models.Model):
    ReplaceServiceObject = models.ForeignKey(ReplaceServiceObject, models.SET_NULL, verbose_name='Объект', blank=True, null=True)
    ReplaceServiceContract = models.ForeignKey(ReplaceServiceContract, verbose_name='Договор', on_delete=models.CASCADE)
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    DateWork = models.DateField(u'Дата выполнения работ')
    TypeWork = models.ManyToManyField(TypeWork, verbose_name='Вид работ', blank=True)
    TypeWork_descript = models.TextField(u'Дополнение к видам работ', blank=True)
    Price = models.DecimalField(u'Стоимость работ', max_digits=10, decimal_places=2, default=0)
    CoWorkers = models.ManyToManyField(CoWorkers, verbose_name='Исполнители', blank=True)
    Descriptions = models.TextField(u'Примечание', blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_rsa')
    Update_user = CurrentUserField(related_name='update_by_rsa')

    def __str__(self):
        return self.ReplaceServiceObject.NameObject + ' - ' + self.ReplaceServiceObject.AddressObject

    class Meta:
        verbose_name = u'Акт '
        verbose_name_plural = u'Акт замены по договору '
        permissions = (
            ('act_list_view', u'ЗаменыАкт.Просмотр списка'),
            ('act_item_view', u'ЗаменыАкт.Просмотр записи'),
            ('act_item_add', u'ЗаменыАкт.Добавить запись'),
            ('act_item_edit', u'ЗаменыАкт.Изменить запись'),
        )
