import os
from django.contrib.auth.models import User
from django.db import models
from django_currentuser.db.models import CurrentUserField

from base.models import Branch, ServingCompanyBranch, TypeDocument, CoWorkers
from reference_books.models import TypeObject, PaymentMethods, StatusSecurity, TypeEquipmentInstalled, ListEquipment, \
    TypeWork, City, OutputToAccounts, ListMonth
from ckeditor.fields import RichTextField
from slugify import slugify


class MaintenanceTemplateDocuments(models.Model):  # Шаблоны документов
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон документа '
        verbose_name_plural = u'Шаблоны документов '


class MaintenanceTemplateSubContract(models.Model):  # Шаблоны документов
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


class MaintenancePereodicAccrual(models.Model):
    NamePeriodic = models.CharField(u'Наименование', max_length=100)
    slug = models.SlugField(u'Алиас', max_length=10, unique=True)

    def __str__(self):
        return self.NamePeriodic

    class Meta:
        verbose_name = u'Периодичность '
        verbose_name_plural = u'Периодичность начислений '


class MaintenancePereodicService(models.Model):
    NamePeriodic = models.CharField(u'Наименование', max_length=100)
    slug = models.SlugField(u'Алиас', max_length=10, unique=True)

    def __str__(self):
        return self.NamePeriodic

    class Meta:
        verbose_name = u'Периодичность '
        verbose_name_plural = u'Периодичность обслуживания '


class MaintenanceServiceContract(models.Model):  # Договора охраны
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    NumContractInternal = models.CharField(u'Номер внутренний', max_length=30)
    NumContractBranch = models.CharField(u'Номер клиентский', max_length=30, blank=True)
    DateConclusion = models.DateField(u'Дата заключения')
    DateTermination = models.DateField(u'Дата расторжения', null=True, blank=True)
    TemplateDocuments = models.ForeignKey(MaintenanceTemplateDocuments, models.SET_NULL,
                                          null=True, verbose_name='Тип бланка договора')
    PaymentDate = models.IntegerField(u'Срок оплаты, дней', default=0,
                                      help_text='0 - предоплата или количество дней отсрочки')
    PereodicAccrual = models.ForeignKey(MaintenancePereodicAccrual, models.SET_NULL,
                                        null=True, verbose_name='Периодичность начислений')
    PereodicAccrualMonth = models.ManyToManyField(ListMonth, verbose_name=u'Периодичность начислений по месяцам',
                                                  help_text=u'Выбор нескольких позиций c нажатой кнопкой Ctrl', blank=True)
    PereodicService = models.ForeignKey(MaintenancePereodicService, models.SET_NULL,
                                        null=True, verbose_name='Периодичность обслуживаний')
    PushToAccounts = models.ForeignKey(OutputToAccounts, models.SET_NULL,
                                       null=True, verbose_name='Выводить в счета')
    NameOfService = models.TextField(u'Наименование услуги', blank=True)
    Notes = models.TextField(u'Комментарии', blank=True, null=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_mntsc')
    Update_user = CurrentUserField(related_name='update_by_mntsc')

    def __str__(self):
        return self.NumContractInternal

    class Meta:
        verbose_name = u'Договор '
        verbose_name_plural = u'Договора ТО '
        permissions = (
            ('contract_list_view', u'ТОДоговор.Просмотр списка'),
            ('contract_item_view', u'ТОДоговор.Просмотр записи'),
            ('contract_item_add', u'ТОДоговор.Добавить запись'),
            ('contract_item_edit', u'ТОДоговор.Изменить запись'),
        )


class MaintenanceServiceObject(models.Model):
    MaintenanceServiceContract = models.ForeignKey(MaintenanceServiceContract,
                                                   verbose_name='Договор', on_delete=models.CASCADE)
    TypeObject = models.ForeignKey(TypeObject, models.SET_NULL, null=True, verbose_name='Тип объекта')
    NameObject = models.CharField(u'Описание', max_length=300)
    AddressObject = models.CharField(u'Адрес', max_length=500)
    CityObject = models.ForeignKey(City, models.SET_NULL, verbose_name='Город/Нас.пункт', null=True, blank=True)
    Coordinates = models.CharField(u'Координаты', max_length=50, blank=True)
    PaymentMethods = models.ForeignKey(PaymentMethods, models.SET_NULL, null=True, verbose_name='Форма оплаты')
    Price = models.DecimalField(u'Стоимость обслуж-я', max_digits=10, decimal_places=2)
    DateStart = models.DateField(u'Начало обслуж-я')
    DateEnd = models.DateField(u'Конец обслуж-я', null=True, blank=True)
    TypeEquipInstalled = models.ManyToManyField(TypeEquipmentInstalled,
                                                verbose_name='Вид обслуживаемой системы ТСО', blank=True)
    NameOfService = models.TextField(u'Наименование услуги', blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_mntso')
    Update_user = CurrentUserField(related_name='update_by_mntso')

    def __str__(self):
        return self.NameObject + ' (' + self.AddressObject + ')'

    class Meta:
        verbose_name = u'Объект '
        verbose_name_plural = u'Объекты ТО '
        permissions = (
            ('object_list_view', u'ТООбъект.Просмотр списка'),
            ('object_item_view', u'ТООбъект.Просмотр записи'),
            ('object_item_add', u'ТООбъект.Добавить запись'),
            ('object_item_edit', u'ТООбъект.Изменить запись'),
        )


class MaintenanceServiceAct(models.Model):
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    Object = models.ForeignKey(MaintenanceServiceObject, models.SET_NULL, verbose_name='Объект', blank=True, null=True)
    DateWork = models.DateField(u'Дата выполнения работ')
    CoWorker = models.ForeignKey(CoWorkers, models.SET_NULL, null=True, verbose_name='Исполнитель')
    Descriptions = models.TextField(u'Примечание', blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_mntsa')
    Update_user = CurrentUserField(related_name='update_by_mntsa')

    def __str__(self):
        return self.Object.NameObject + ' (' + self.Object.AddressObject + ')'

    class Meta:
        verbose_name = u'Акт '
        verbose_name_plural = u'Акт проведения ТО '


class MaintenanceServiceSubContract(models.Model):
    NumSubContract = models.IntegerField(u'Номер допсоглашения')
    MaintenanceServiceContract = models.ForeignKey(MaintenanceServiceContract,
                                                   verbose_name='Договора', on_delete=models.CASCADE)
    MaintenanceServiceObject = models.ManyToManyField(MaintenanceServiceObject, verbose_name='Объект(ы)', blank=True)
    DateSubContract = models.DateField(u'Дата составления', null=True, blank=True)
    Template = models.ForeignKey(MaintenanceTemplateSubContract, models.SET_NULL,
                                 null=True, verbose_name='Шаблон соглашения')

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_mntssc')
    Update_user = CurrentUserField(related_name='update_by_mntssc')

    def __str__(self):
        return self.Template.NameTemplate + ' от ' + str(self.DateSubContract)

    class Meta:
        verbose_name = u'Допсоглашение '
        verbose_name_plural = u'Дополнительные соглашения '


def contract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "contract_%s_%s.%s" % (
    slugify(instance.MaintenanceServiceContract.NumContractInternal, max_length=10, word_boundary=True, separator="_"),
    instance.MaintenanceServiceContract.DateConclusion.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/maintenance_service/contract/', filename)


class MaintenanceServiceContract_scan(models.Model):
    MaintenanceServiceContract = models.ForeignKey(MaintenanceServiceContract, on_delete=models.CASCADE,
                                                   verbose_name='Договор', )
    ScanFile = models.FileField(u'Файл', upload_to=contract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)


def subcontract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "subcontract_%s_%s.%s" % (
    slugify(instance.MaintenanceServiceSubContract.NumSubContract, max_length=10, word_boundary=True, separator="_"),
    instance.MaintenanceServiceSubContract.DateSubContract.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/maintenance_service/subcontract/', filename)


class MaintenanceServiceSubContract_scan(models.Model):
    MaintenanceServiceSubContract = models.ForeignKey(MaintenanceServiceSubContract, on_delete=models.CASCADE,
                                                      verbose_name='Дополнительное соглашение')
    ScanFile = models.FileField(u'Файл', upload_to=subcontract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)
