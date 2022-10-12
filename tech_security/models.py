import os

from django.db import models
from django_currentuser.db.models import CurrentUserField
from slugify import slugify
from ckeditor.fields import RichTextField

from base.models import Branch, ServingCompanyBranch, TypeDocument, Event, TypeSubContract
from reference_books.models import TypeObject, PaymentMethods, StatusSecurity, TypeEquipmentInstalled, ListEquipment, \
    ListMonth, City, CategoryObjects, OpSoS_rate


class TechTemplateDocuments(models.Model):  # Шаблоны договоров
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    CategoryObjects = models.ForeignKey(CategoryObjects, verbose_name=u'Категория недвижимости',
                                        on_delete=models.CASCADE)
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.CategoryObjects.shortname + ' - ' + self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон '
        verbose_name_plural = u'Шаблоны договоров '


class TechTemplateSubContract(models.Model):  # Шаблоны допсоглашений
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


class TechTemplateOtherDocuments(models.Model):  # Шаблоны других документов
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    slug = models.SlugField('Ключ категории')
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон '
        verbose_name_plural = u'Шаблоны других документов '


class PricePerMonth(models.Model):
    Month = models.ForeignKey(ListMonth, verbose_name='Месяц', on_delete=models.CASCADE)

    def __str__(self):
        return self.Month

    class Meta:
        verbose_name = u'Сумма '
        verbose_name_plural = u'Дифференцированная стоимость услуг '


class TechSecurityContract(models.Model):  # Договора охраны
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    ServingCompany = models.ForeignKey(ServingCompanyBranch, verbose_name='Исполнитель', on_delete=models.CASCADE)
    NumContractInternal = models.CharField(u'Номер внутренний', max_length=30)
    NumContractBranch = models.CharField(u'Номер клиентский', max_length=30, blank=True)
    DateConclusion = models.DateField(u'Дата заключения')
    DateTermination = models.DateField(u'Дата расторжения', null=True, blank=True)
    TemplateDocuments = models.ForeignKey(TechTemplateDocuments, models.SET_NULL,
                                          null=True, verbose_name='Тип бланка договора')
    PaymentDate = models.IntegerField(u'Срок оплаты, дней', default=0,
                                      help_text='0 - предоплата или количество дней отсрочки')
    PaymentAfter = models.BooleanField(u'Постоплата', default=False)
    ResponsibilityCost = models.IntegerField(u'Материальная ответственность', default=0,
                                             help_text='0 - без материальной ответственности или сумма')
    NameOfService = models.TextField(u'Наименование услуги', blank=True)
    TextContract = RichTextField(u'Текст договора', blank=True, null=True)
    Notes = models.TextField(u'Комментарии', blank=True, null=True)
    NotDirect = models.BooleanField(u'Не прямой договор', default=False)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_techsc')
    Update_user = CurrentUserField(related_name='update_by_techsc')

    def __str__(self):
        return self.NumContractInternal

    class Meta:
        verbose_name = u'Договор техохраны'
        verbose_name_plural = u'Договоры технической охраны '
        permissions = (
            ('contract_list_view', u'ТехОхрДоговор.Просмотр списка'),
            ('contract_item_view', u'ТехОхрДоговор.Просмотр записи'),
            ('contract_item_add', u'ТехОхрДоговор.Добавить запись'),
            ('contract_item_edit', u'ТехОхрДоговор.Изменить запись'),
        )


class TechSecurityObject(models.Model):
    TechSecurityContract = models.ForeignKey(TechSecurityContract, verbose_name='№ Договора', on_delete=models.CASCADE)
    NumObjectPCN = models.CharField(u'Номер объекта ПЦН', max_length=50, default='б/н')
    TypeObject = models.ForeignKey(TypeObject, models.SET_NULL, null=True, verbose_name='Тип объекта')
    NameObject = models.CharField(u'Описание', max_length=300)
    AddressObject = models.CharField(u'Адрес', max_length=500)
    CityObject = models.ForeignKey(City, models.SET_NULL, verbose_name='Город/Нас.пункт', null=True, blank=True)
    Coordinates = models.CharField(u'Координаты', max_length=50, null=True, blank=True)
    PaymentMethods = models.ForeignKey(PaymentMethods, models.SET_NULL, null=True, verbose_name='Форма оплаты')
    ChgPriceDifferent = models.BooleanField(u'Дифференцированная стоимость', default=False)
    PriceNoDifferent = models.DecimalField(u'Стоимость постоянная', max_digits=10, decimal_places=2, default=0)
    StatusSecurity = models.ForeignKey(StatusSecurity, models.SET_NULL, null=True, verbose_name='Состояние', default=False)
    max_time_arrival = models.IntegerField(u'Время прибытия', default=5)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_techso')
    Update_user = CurrentUserField(related_name='update_by_techso')

    def __str__(self):
        return self.NumObjectPCN + ' (' + self.AddressObject + ')'

    class Meta:
        verbose_name = u'Объект '
        verbose_name_plural = u'Объекты технической охраны '
        permissions = (
            ('object_list_view', u'ТехОхрОбъект.Просмотр списка'),
            ('object_item_view', u'ТехОхрОбъект.Просмотр записи'),
            ('object_item_add', u'ТехОхрОбъект.Добавить запись'),
            ('object_item_edit', u'ТехОхрОбъект.Изменить запись'),
        )


class TechSecurityObjectPriceDifferent(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект', on_delete=models.CASCADE)
    ListMonth = models.ForeignKey(ListMonth, verbose_name=u'Месяц', on_delete=models.CASCADE)
    Price = models.DecimalField(u'Стоимость', max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.TechSecurityObject.NumObjectPCN + ' (' + ListMonth.Month + ')'

    class Meta:
        verbose_name = u'Стоимость за месяц '
        verbose_name_plural = u'Дифференцированная стоимость услуг '


class TechSecurityObjectTypeEquipInstalled(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект', on_delete=models.CASCADE)
    TypeEquipInstalled = models.TextField(u'Оборудование', null=True, blank=True)

    def __str__(self):
        return self.TechSecurityObject.NumObjectPCN

    class Meta:
        verbose_name = u'Тип оборудования '
        verbose_name_plural = u'Установленное оборудование '


class TechSecurityObjectOpSoSCard(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект', on_delete=models.CASCADE)
    OpSoSRate = models.ForeignKey(OpSoS_rate, verbose_name='Тариф', max_length=100, on_delete=models.CASCADE)
    SimICC = models.CharField(u'ID сим-карты', max_length=25)
    SimNumber = models.CharField(u'Номер сим-карты', max_length=20)

    def __str__(self):
        return self.SimNumber.__str__()

    class Meta:
        verbose_name = u'SIM '
        verbose_name_plural = u'Связь объекта '


class TechSecurityObjectRent(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект', on_delete=models.CASCADE)
    Question_ForRent = models.BooleanField(u'Объект в аренде', default=False)
    OwnersPremises_Name = models.CharField(u'ФИО соб-ка помещения', max_length=100, blank=True)
    OwnersPremises_Phone = models.CharField(u'Телефон соб-ка помещения', max_length=30, blank=True)
    DateEndContractRent = models.DateField(u'Договор аренды до', null=True, blank=True)

    def __str__(self):
        return self.OwnersPremises_Name

    class Meta:
        verbose_name = u'Аренда '
        verbose_name_plural = u'Арендованные объекты '


class TechSecurityObjectPeriodSecurity(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект договора', on_delete=models.CASCADE)
    DateStart = models.DateField(u'Дата начала')
    DateEnd = models.DateField(u'Дата окончания', null=True, blank=True)
    PeriodPrice = models.DecimalField(u'Абонентская плата', max_digits=10, decimal_places=2)
    event_code = models.ForeignKey(Event, models.SET_NULL, null=True, verbose_name='Событие')
    add_date = models.DateTimeField(u'Дата и время внесения записи', auto_now_add=True)

    def __str__(self):
        return self.TechSecurityObject.NumObjectPCN

    class Meta:
        verbose_name = u'Период '
        verbose_name_plural = u'Периоды охраны объектов '


class ListRentedEquipment(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект договора', on_delete=models.CASCADE)
    NameEquipment = models.ForeignKey(ListEquipment, verbose_name='Оборудование', on_delete=models.CASCADE)
    NumEquipment = models.CharField(u'Номер оборудования', max_length=50)
    DateIssue = models.DateField(u'Дата выдачи', null=True, blank=True)
    DateReturn = models.DateField(u'Дата возврата', null=True, blank=True)

    def __str__(self):
        return self.NameEquipment.Name

    class Meta:
        verbose_name = u'Оборудование '
        verbose_name_plural = u'Список арендованного оборудования '


class TechSecuritySubContract(models.Model):
    NumSubContract = models.IntegerField(u'Номер допсоглашения')
    TechSecurityContract = models.ForeignKey(TechSecurityContract, verbose_name='Договора', on_delete=models.CASCADE)
    TechSecurityObject = models.ManyToManyField(TechSecurityObject, verbose_name='Объект(ы)', blank=True)
    DateSubContract = models.DateField(u'Дата составления', null=True, blank=True)
    Template = models.ForeignKey(TechTemplateSubContract, models.SET_NULL, null=True, verbose_name='Шаблон соглашения')

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_techssc')
    Update_user = CurrentUserField(related_name='update_by_techssc')

    def __str__(self):
        return self.Template.NameTemplate + ' от ' + str(self.DateSubContract)

    class Meta:
        verbose_name = u'Допсоглашение '
        verbose_name_plural = u'Дополнительные соглашения '
        permissions = (
            ('subcontract_list_view', u'ТехОхрДопДоговор.Просмотр списка'),
            ('subcontract_item_view', u'ТехОхрДопДоговор.Просмотр записи'),
            ('subcontract_item_add', u'ТехОхрДопДоговор.Добавить запись'),
            ('subcontract_item_edit', u'ТехОхрДопДоговор.Изменить запись'),
        )


def contract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "contract_%s_%s.%s" % (
        slugify(instance.TechSecurityContract.NumContractInternal, max_length=10, word_boundary=True, separator="_"),
        instance.TechSecurityContract.DateConclusion.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/tech_security/contract/', filename)


class TechSecurityContract_scan(models.Model):
    TechSecurityContract = models.ForeignKey(TechSecurityContract, verbose_name='Договор', on_delete=models.CASCADE)
    ScanFile = models.FileField(u'Файл', upload_to=contract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)


def subcontract_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "subcontract_%s_%s.%s" % (
        slugify(instance.TechSecuritySubContract.NumSubContract, max_length=10, word_boundary=True, separator="_"),
        instance.TechSecuritySubContract.DateSubContract.strftime("%Y%m%d"), ext)
    return os.path.join('scandoc/tech_security/subcontract/', filename)


class TechSecuritySubContract_scan(models.Model):
    TechSecuritySubContract = models.ForeignKey(TechSecuritySubContract, verbose_name='Дополнительное соглашение',
                                                on_delete=models.CASCADE)
    ScanFile = models.FileField(u'Файл', upload_to=subcontract_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)


def object_file_rename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "object_%s.%s" % (
        slugify(instance.TechSecurityObject.AddressObject, max_length=20, word_boundary=True, separator="_"), ext)
    return os.path.join('scandoc/tech_security/object/', filename)


class TechSecurityObject_scan(models.Model):
    TechSecurityObject = models.ForeignKey(TechSecurityObject, verbose_name='Объект', on_delete=models.CASCADE)
    ScanFile = models.FileField(u'Файл', upload_to=object_file_rename)
    upload_date = models.DateTimeField(auto_now_add=True)
