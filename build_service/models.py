import os
from django.contrib.auth.models import User
from django.db import models
from django_currentuser.db.models import CurrentUserField

from base.models import Branch, ServingCompanyBranch, TypeDocument, CoWorkers
from reference_books.models import TypeObject, PaymentMethods, StatusSecurity, TypeEquipmentInstalled, ListEquipment, \
    TypeWork, City
from ckeditor.fields import RichTextField
from tech_security.models import TechSecurityObject
from trade.models import invoice
from slugify import slugify


class BuildTemplateDocuments(models.Model):  # Шаблоны документов
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон документа '
        verbose_name_plural = u'Шаблоны документов '


class BuildTemplateSubContract(models.Model):  # Шаблоны документов
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    slug = models.SlugField('Ключ категории')
    TextTemplate = RichTextField(u'Текст шаблона')
    ChangeObjects = models.BooleanField(u'Выбор объектов', default=True,
                                        help_text='при расторжении договора список объетов не выводить')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон '
        verbose_name_plural = u'Шаблоны доп.соглашений '


class BuildServiceContract(models.Model):  # Договора охраны
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    NumContractInternal = models.CharField(u'Номер внутренний', max_length=30)
    NumContractBranch = models.CharField(u'Номер клиентский', max_length=30, blank=True)
    DateConclusion = models.DateField(u'Дата заключения')
    DateTermination = models.DateField(u'Дата расторжения', null=True, blank=True)
    TemplateDocuments = models.ForeignKey(BuildTemplateDocuments, models.SET_NULL, null=True,
                                          verbose_name='Тип бланка договора')
    PaymentDate = models.IntegerField(u'Срок оплаты, дней', default=0,
                                      help_text='0 - предоплата или количество дней отсрочки')
    NameOfService = models.TextField(u'Наименование услуги', blank=True)
    ReturnedSigned = models.BooleanField(u'Договор подписан', help_text="Договор возвращен подписанным контрагентом",
                                         default=False)
    Notes = models.TextField(u'Комментарии', blank=True, null=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_buildsc')
    Update_user = CurrentUserField(related_name='update_by_buildsc')

    def __str__(self):
        return self.NumContractInternal

    class Meta:
        verbose_name = u'Договор '
        verbose_name_plural = u'Договора монтажа оборудования '
        permissions = (
            ('contract_list_view', u'МонтажДоговор.Просмотр списка'),
            ('contract_item_view', u'МонтажДоговор.Просмотр записи'),
            ('contract_item_add', u'МонтажДоговор.Добавить запись'),
            ('contract_item_edit', u'МонтажДоговор.Изменить запись'),
        )


class BuildServiceObject(models.Model):
    BuildServiceContract = models.ForeignKey(BuildServiceContract, verbose_name='Договор', on_delete=models.CASCADE)
    TypeObject = models.ForeignKey(TypeObject, models.SET_NULL, null=True, verbose_name='Тип объекта')
    NameObject = models.CharField(u'Описание', max_length=300)
    AddressObject = models.CharField(u'Адрес', max_length=500)
    CityObject = models.ForeignKey(City, models.SET_NULL, verbose_name='Город/Нас.пункт', null=True, blank=True)
    Coordinates = models.CharField(u'Координаты', max_length=50, blank=True)
    PaymentMethods = models.ForeignKey(PaymentMethods, models.SET_NULL, null=True, verbose_name='Форма оплаты')
    Price = models.DecimalField(u'Стоимость монтажа', max_digits=10, decimal_places=2)
    DateStart = models.DateField(u'Начало монтажа')
    DateEnd = models.DateField(u'Конец монтажа ', null=True, blank=True)
    TypeEquipInstalled = models.ManyToManyField(TypeEquipmentInstalled, verbose_name='Тип установленного оборудования',
                                                blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_buildso')
    Update_user = CurrentUserField(related_name='update_by_buildso')

    class Meta:
        verbose_name = u'Объект '
        verbose_name_plural = u'Объекты монтажа оборудования '
        permissions = (
            ('object_list_view', u'МонтажОбъект.Просмотр списка'),
            ('object_item_view', u'МонтажОбъект.Просмотр записи'),
            ('object_item_add', u'МонтажОбъект.Добавить запись'),
            ('object_item_edit', u'МонтажОбъект.Изменить запись'),
        )


class BuildServiceAct(models.Model):
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    Object = models.ForeignKey(TechSecurityObject, models.SET_NULL, verbose_name='Объект', blank=True, null=True)
    AddressObject = models.CharField(u'Адрес', max_length=500, blank=True)
    DateWork = models.DateField(u'Дата выполнения работ')
    TypeWork = models.ManyToManyField(TypeWork, verbose_name='Вид работ', blank=True)
    TypeWork_descript = models.TextField(u'Дополнение к видам работ', blank=True)
    Price = models.DecimalField(u'Стоимость работ', max_digits=10, decimal_places=2)
    CoWorker = models.ManyToManyField(CoWorkers, verbose_name='Исполнитель', blank=True)
    Descriptions = models.TextField(u'Примечание', blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_buildsa')
    Update_user = CurrentUserField(related_name='update_by_buildsa')

    def __str__(self):
        return u'Акт доустановки №' + str(self.pk)

    class Meta:
        verbose_name = u'Акт '
        verbose_name_plural = u'Акт домонтажа оборудования '
        permissions = (
            ('act_list_view', u'МонтажАкт.Просмотр списка'),
            ('act_item_view', u'МонтажАкт.Просмотр записи'),
            ('act_item_add', u'МонтажАкт.Добавить запись'),
            ('act_item_edit', u'МонтажАкт.Изменить запись'),
        )


class BuildServiceSubContract(models.Model):
    NumSubContract = models.IntegerField(u'Номер допсоглашения')
    BuildServiceContract = models.ForeignKey(BuildServiceContract, verbose_name='Договора', on_delete=models.CASCADE)
    BuildServiceObject = models.ManyToManyField(BuildServiceObject, verbose_name='Объект(ы)', blank=True)
    DateSubContract = models.DateField(u'Дата составления', null=True, blank=True)
    Template = models.ForeignKey(BuildTemplateSubContract, models.SET_NULL, null=True, verbose_name='Шаблон соглашения')

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_buildssc')
    Update_user = CurrentUserField(related_name='update_by_buildssc')

    def __str__(self):
        return self.Template.NameTemplate + ' от ' + str(self.DateSubContract)

    class Meta:
        verbose_name = u'Допсоглашение '
        verbose_name_plural = u'Дополнительные соглашения '
        permissions = (
            ('subcontract_list_view', u'МонтажДопДоговор.Просмотр списка'),
            ('subcontract_item_view', u'МонтажДопДоговор.Просмотр записи'),
            ('subcontract_item_add', u'МонтажДопДоговор.Добавить запись'),
            ('subcontract_item_edit', u'МонтажДопДоговор.Изменить запись'),
        )


def contract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "contract_%s_%s.%s" % (
    slugify(instance.BuildServiceContract.NumContractInternal, max_length=10, word_boundary=True, separator="_"),
    instance.BuildServiceContract.DateConclusion.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/build_service/contract/', filename)


class BuildServiceContract_scan(models.Model):
    BuildServiceContract = models.ForeignKey(BuildServiceContract, verbose_name='Договор', on_delete=models.CASCADE)
    ScanFile = models.FileField(u'Файл', upload_to=contract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)


def subcontract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "subcontract_%s_%s.%s" % (
    slugify(instance.BuildServiceSubContract.NumSubContract, max_length=10, word_boundary=True, separator="_"),
    instance.BuildServiceSubContract.DateSubContract.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/build_service/subcontract/', filename)


class BuildServiceSubContract_scan(models.Model):
    BuildServiceSubContract = models.ForeignKey(BuildServiceSubContract, verbose_name='Дополнительное соглашение',
                                                on_delete=models.CASCADE)
    ScanFile = models.FileField(u'Файл', upload_to=subcontract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)
