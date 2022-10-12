import os
from django.contrib.auth.models import User
from django.db import models
from django_currentuser.db.models import CurrentUserField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
import time
# from base.views import path_and_rename
from bills.settings import MEDIA_URL
from reference_books.models import ListPosts, PowersOfficeActs, TypeDocument, TypesClient, FormsSchet, City


# --------------------- Словари --------------------------------------------------
class Menu(MPTTModel):
    name = models.CharField('Название', max_length=50)  # , unique=True)
    slug = models.SlugField('Ключ категории')
    fa_class = models.CharField('Иконка FontAwesome',
                                help_text='Класс FontAwesome для вывода иконок, типа: fa-search, без указания размера',
                                max_length=50, blank=True)
    parent = TreeForeignKey('self', blank=True, null=True, verbose_name="Родитель", related_name='child', db_index=True,
                            on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'Ветка меню '
        verbose_name_plural = u'Дерево меню '

    class MPTTMeta:
        level_attr = 'mptt_level'


class SystemConstant(models.Model):
    ConstantsNameRu = models.CharField(u'Наименование константы', max_length=50)
    slug = models.SlugField(u'Алиас', unique=True)
    ConstantsValue = models.CharField(u'Значение константы', max_length=100)

    def __str__(self):
        return self.ConstantsNameRu

    class Meta:
        verbose_name = u'Константа '
        verbose_name_plural = u'Константы '


class SectionsApp(models.Model):
    name = models.CharField('Название', max_length=50)
    slug = models.SlugField('Ключ категории')
    choice = models.BooleanField('Возможность выбора', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'Раздел '
        verbose_name_plural = u'Разделы программы '


# Добавление объекта(ов), снятите объекта(ов), смена мат.ответственности, изменение абонплаты
class TypeSubContract(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('Ключ категории')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'Тип '
        verbose_name_plural = u'Типы дополнительных соглашений '


class GroupClient(models.Model):  # Объединение клиентов в группы
    NameGroupClient = models.CharField(u'Наименование группы', max_length=100)
    Founder_FIO = models.CharField(u'ФИО учредителя', max_length=50)
    Address_residence = models.CharField(u'Адрес учредителя', max_length=300, blank=True)
    Address_email = models.EmailField(u'Адрес эл.почты', blank=True)
    Phone_mobile = models.CharField(u'Сотовый телефон', max_length=20, blank=True)
    Phone_city = models.CharField(u'Городской телефон', max_length=20, blank=True)
    Phone_fax = models.CharField(u'Факс', max_length=20, blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_bgc')
    Update_user = CurrentUserField(related_name='update_by_bgc')

    def __str__(self):
        return self.NameGroupClient

    class Meta:
        verbose_name = u'Группа клиентов '
        verbose_name_plural = u'Группы клиентов '


class ServingCompany(models.Model):  # Список обслуживающих организаций
    OKOPF = models.CharField(u'Организационно-правовая форма', max_length=10)
    NameCompany_full = models.CharField(u'Полное наименование', max_length=100)
    NameCompany_short = models.CharField(u'Краткое наименование', max_length=100, blank=True)
    Management_post = models.CharField(u'Должность руководителя', max_length=100, blank=True)
    Management_name = models.CharField(u'ФИО руководителя', max_length=50, blank=True)
    Address_reg = models.CharField(u'Адрес', max_length=300)
    INN = models.CharField(u'ИНН', max_length=12, blank=True)
    OGRN = models.CharField(u'ОГРН', max_length=20, blank=True)
    OKPO = models.CharField(u'ОКПО', max_length=20, blank=True)
    OKVED = models.CharField(u'ОКВЭД', max_length=20, blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_bsc')
    Update_user = CurrentUserField(related_name='update_by_bsc')

    def __str__(self):
        return self.NameCompany_short

    class Meta:
        verbose_name = u'Обслуживающая организация '
        verbose_name_plural = u'Обслуживающие организации '


class ServingCompanyBranch(models.Model):  # Создание подразделений Обслуживающей организации
    ServingCompany = models.ForeignKey(ServingCompany, verbose_name=u'Головное предприятие',
                                       help_text='Создаётся администратором', on_delete=models.CASCADE)
    City = models.ForeignKey(City, models.SET_NULL, verbose_name=u'Город', null=True)
    NameBranch = models.CharField(u'Полное наименование', max_length=200, blank=True)

    Management_post = models.ForeignKey(ListPosts, models.SET_NULL, verbose_name='Должность', null=True)
    Management_name = models.CharField(u'ФИО руководителя', max_length=80, blank=True)

    PowersOffice_name = models.ForeignKey(PowersOfficeActs, models.SET_NULL, null=True,
                                          verbose_name=u'Действует на основании')
    PowersOffice_number = models.CharField(u'Номер документа основания', max_length=300, blank=True)

    Address_post = models.CharField(u'Почтовый адрес', max_length=300)
    Address_email = models.EmailField(u'Адрес эл.почты', blank=True)
    KPP = models.CharField(u'КПП', max_length=30, blank=True)

    Phone_city = models.CharField(u'Номер гор. телефона', max_length=20, blank=True)
    Phone_PCN = models.CharField(u'Номер телефона ПЦН', max_length=20, blank=True)
    Phone_fax = models.CharField(u'Номер факса', max_length=20, blank=True)
    Phone_mobile = models.CharField(u'Номер моб. телефона', max_length=20, blank=True)

    Bank_BIK = models.CharField(u'БИК банка', max_length=100, blank=True)
    Bank_Details = models.TextField(u'Реквизиты банка', blank=True)
    Bank_RaschetSchet = models.CharField(u'Расчетный счет', max_length=30, blank=True)

    RHI_number = models.CharField(u'Серия и номер РХИ', max_length=50, blank=True,
                                  help_text='Блок РХИ заполняется при необходимости')
    RHI_dateissue = models.DateField(u'Дата выдачи РХИ', blank=True, null=True),
    RHI_dateend = models.DateField(u'Дата окончания РХИ', blank=True, null=True)
    RHI_issuedby = models.CharField(u'Кем выдано РХИ', max_length=50, blank=True)

    head_text = models.TextField(u'Заголовок', help_text=u'Заголовка в договоре или дополнительном соглашении',
                                 blank=True, null=True)
    details_text = models.TextField(u'Реквизиты', help_text=u'Реквизиты в договоре или допсоглашении', blank=True,
                                    null=True)
    signature_text = models.TextField(u'Подпись', help_text=u'Подпись в договорах, допсоглашениях, актах', blank=True,
                                      null=True)

    integrity_slug = models.SlugField(u'Алиас из АРМ "Заявки"', max_length=20, blank=True, unique=False)
    file_expansion_to1S = models.CharField(u'Расширение файла выгрузки в 1С', max_length=10, blank=True)
    catalog_expansion_to1S = models.CharField(u'Наименование каталога для выгрузки в 1С', max_length=30, blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_bscb')
    Update_user = CurrentUserField(related_name='update_by_bscb')

    def __str__(self):
        return self.NameBranch

    class Meta:
        verbose_name = u'Подразделение обслуживающей организации '
        verbose_name_plural = u'Подразделения обслуживающих организаций '


class ServingCompany_settingsDocuments(models.Model):  # Управление параметрами
    ServingCompanyBranch = models.ForeignKey(ServingCompanyBranch, verbose_name='Организация исполнитель',
                                             on_delete=models.CASCADE)
    Name_setting = models.CharField(u'Наименование параметра', max_length=50)
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    current_num = models.IntegerField(u'Номер последнего документа')
    prefix_num = models.CharField(u'Префикс номера документа', max_length=20, blank=True, null=True)
    postfix_num = models.CharField(u'Постфикс номера документа', max_length=20, blank=True, null=True)

    def __str__(self):
        return self.Name_setting

    class Meta:
        verbose_name = u'Параметр '
        verbose_name_plural = u'Управление параметрами договоров '


class ServingCompany_policerecipients(models.Model):  # Должностные лица полиции ЛРР
    ServingCompanyBranch = models.ForeignKey(ServingCompanyBranch, verbose_name='Организация исполнитель',
                                             on_delete=models.CASCADE)
    PoliceName = models.CharField(u'Наименование отдела ЛРР', max_length=200,
                                  help_text='Кому полностью в дательном падеже без фамилии')
    NameRecipient = models.CharField(u'Фамилия и иницалы', max_length=80, help_text='Пример: А.К. Рубанович')
    DescTypeClient = models.TextField(u'Подробное описание')

    def __str__(self):
        return self.PoliceName

    class Meta:
        verbose_name = u'Получатель '
        verbose_name_plural = u'Должностные лица ЛРР '


class ServingCompany_specialtools(models.Model):  # Список спецсредств
    ServingCompanyBranch = models.ForeignKey(ServingCompanyBranch, verbose_name='Организация исполнитель',
                                             on_delete=models.CASCADE)
    SecureTools = models.CharField(u'Наименование спецсредства', max_length=50)
    count = models.IntegerField(u'Количество')

    def __str__(self):
        return self.SecureTools

    class Meta:
        verbose_name = u'Параметр '
        verbose_name_plural = u'Список спецсредств хранимых и используемых организацией '


class CoWorkers(models.Model):
    Person_FIO = models.CharField(u'Фамилия Имя Отчество', max_length=100)
    ListPosts = models.ForeignKey(ListPosts, models.SET_NULL, null=True, verbose_name='Должность')
    ServingCompanyBranch = models.ForeignKey(ServingCompanyBranch, models.SET_NULL, null=True,
                                             verbose_name='Место работы')
    StatusWorking = models.BooleanField(u'Работает', default=True)

    def __str__(self):
        return self.Person_FIO

    class Meta:
        verbose_name = u'Сотрудник '
        verbose_name_plural = u'Сотрудники '
        ordering = ['Person_FIO']


class Client(models.Model):  # Базовая таблица клиентов
    TypeClient = models.ForeignKey(TypesClient, verbose_name='Тип клиента', on_delete=models.CASCADE)
    OKOPF = models.CharField(u'Организационно-правовая форма', max_length=10, blank=True)
    GroupClient = models.ForeignKey(GroupClient, models.SET_NULL, verbose_name='Группа клиента', null=True, blank=True)
    NameClient_full = models.CharField(u'Полное наименование', max_length=300)
    NameClient_short = models.CharField(u'Краткое наименование', max_length=300, blank=True)
    Management_post = models.CharField(u'Должность руководителя', max_length=100, blank=True)
    Management_name = models.CharField(u'ФИО руководителя', max_length=50, blank=True)
    Address_reg = models.CharField(u'Адрес', max_length=300)
    INN = models.CharField(u'ИНН', max_length=12, blank=True)
    OGRN = models.CharField(u'ОГРН', max_length=20, blank=True)
    OKPO = models.CharField(u'ОКПО', max_length=20, blank=True)
    OKVED = models.CharField(u'ОКВЭД', max_length=20, blank=True)
    PassportSerNum = models.CharField(u'Серия и номер паспорта', max_length=12, null=True, blank=True)
    DatePassport = models.DateField(u'Дата выдачи паспорта', null=True, blank=True)
    IssuedByPassport = models.TextField(u'Кем выдан пасспорт', null=True, blank=True)
    Alien = models.BooleanField(u'Не является гражданином РФ', default=False, blank=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_client')
    Update_user = CurrentUserField(related_name='update_by_client')

    def __str__(self):
        return self.NameClient_short

    class Meta:
        verbose_name = u'Контрагент '
        verbose_name_plural = u'Контрагенты '


class Branch(models.Model):  # Создание подразделений Организации(Клиента) для ввода
    Client = models.ForeignKey(Client, verbose_name='Клиент', on_delete=models.CASCADE)
    NameBranch = models.CharField(u'Полное наименование', max_length=200, blank=True, null=True)
    Management_post = models.ForeignKey(ListPosts, models.SET_NULL, verbose_name='Должность', blank=True, null=True)
    Management_name = models.CharField(u'ФИО руководителя', max_length=80, blank=True, null=True)
    Management_data = models.TextField(u'В лице', blank=True, null=True)
    PowersOffice_name = models.ForeignKey(PowersOfficeActs, models.SET_NULL, verbose_name='Действует на основании',
                                          blank=True, null=True)
    PowersOffice_number = models.CharField(u'Номер документа основания', max_length=300, blank=True, null=True)
    PowersOffice_date = models.DateField(u'Срок действия доверенности', null=True, blank=True)
    Address_reg = models.CharField(u'Юридический адрес', max_length=300, blank=True, null=True)
    Address_post = models.CharField(u'Почтовый адрес', max_length=300, blank=True, null=True)
    Address_email = models.EmailField(u'Адрес эл.почты', blank=True, null=True)
    KPP = models.CharField(u'КПП', max_length=30, blank=True, null=True)
    Phone_city = models.CharField(u'Номер гор. телефона', max_length=20, blank=True, null=True)
    Phone_fax = models.CharField(u'Номер факса', max_length=20, blank=True, null=True)
    Phone_mobile = models.CharField(u'Номер моб. телефона', max_length=20, blank=True, null=True)
    Phone_SMS = models.CharField(u'Номер для СМС-сообщения', max_length=20, blank=True, null=True)
    Bank_BIK = models.CharField(u'БИК банка', max_length=30, blank=True)
    Bank_Details = models.TextField(u'Реквизиты банка', blank=True, null=True)
    Bank_RaschetSchet = models.CharField(u'Расчетный счет', max_length=30, blank=True, null=True)
    FormsSchet = models.ForeignKey(FormsSchet, default=FormsSchet.objects.get(slug='form_contract').id,
                                   on_delete=models.SET_DEFAULT, verbose_name='Вид формирования счетов')
    EDO = models.BooleanField(u'Электронный документооборот', default=False)
    Accruals_roundoff = models.BooleanField(u'Округлять копейки', default=True)
    Additional_info = models.TextField(u'Дополнительная информация', blank=True, null=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_branch')
    Update_user = CurrentUserField(related_name='update_by_branch')

    def __str__(self):
        if self.NameBranch:
            return self.NameBranch
        else:
            return self.Client.NameClient_full

    class Meta:
        verbose_name = u'Подразделение контрагента '
        verbose_name_plural = u'Подразделения контрагентов '


class Contacts(models.Model):  # Контакты клиентов
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    Person_FIO = models.CharField(u'Фамилия Имя Отчество', max_length=300)
    Person_post = models.CharField(u'Должность', max_length=100, blank=True, null=True)
    Phone_mobile = models.CharField(u'Мобильный телефон', max_length=20, blank=True, null=True)
    Phone_city = models.CharField(u'Городской телефон', max_length=20, blank=True, null=True)
    Phone_city_extra = models.CharField(u'Добавочный', max_length=6, blank=True, null=True)
    Email = models.EmailField(u'Эл.адрес', blank=True, null=True)

    datetime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    datetime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    Create_user = CurrentUserField(on_update=False, related_name='created_by_bcc')
    Update_user = CurrentUserField(related_name='update_by_bcc')

    def __str__(self):
        return self.Person_FIO

    class Meta:
        ordering = ['Person_FIO']
        verbose_name = u'Контакт '
        verbose_name_plural = u'Контакты контрагентов'


class UserNote(models.Model):  # Личные записи
    Branch = models.ForeignKey(Branch, verbose_name='Филиал', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    Title = models.CharField(u'Заголовок', max_length=50, blank=True, null=True)
    Note = models.TextField(u'Запись', blank=True, null=True)

    def __str__(self):
        return self.Note

    class Meta:
        verbose_name = u'Запись '
        verbose_name_plural = u'Личные записи'


class ScannedDocuments(models.Model):  # Сканы документов
    NameDocument = models.CharField(u'Наименование документа', max_length=100)
    Branch = models.ForeignKey(Branch, verbose_name='Клиент', on_delete=models.CASCADE)
    App = models.ForeignKey(SectionsApp,  models.SET_NULL, null=True, verbose_name='Раздел приложения')
    TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа', on_delete=models.CASCADE)
    Document_id = models.IntegerField(u'ID документа')
    ScanPath = models.FileField(upload_to='scandoc/%Y/%m/%d', null=True, blank=True)

    def __str__(self):
        return self.NameDocument

    class Meta:
        verbose_name = u'Скан документа '
        verbose_name_plural = u'Сканы документов '


class Event(models.Model):
    Name = models.CharField(u'Наименование события', max_length=200, unique=True)
    slug = models.SlugField(u'Алиас', max_length=100, unique=True)
    template = models.TextField(u'Шаблон', blank=True, null=True, help_text='Заполнять не обязательно')
    forfilter = models.BooleanField(u'Фильтр', default=False, blank=True)

    def __str__(self):
        return self.Name

    class Meta:
        verbose_name = u'Событие '
        verbose_name_plural = u'События '


class logging(models.Model):
    application = models.SlugField(u'Приложение', max_length=30, blank=True)
    app = models.ForeignKey(SectionsApp, models.SET_NULL, null=True, verbose_name='Приложение')
    scompany = models.ForeignKey(ServingCompanyBranch, verbose_name=u'Сервисная компания', on_delete=models.SET_NULL, null=True)
    type_dct = models.ForeignKey(TypeDocument, models.SET_NULL, verbose_name='Тип документа', blank=True, null=True)
    branch_id = models.IntegerField(u'Идентификатор клиента', blank=True, null=True)
    contract_id = models.IntegerField(u'Идентификатор договора', blank=True, null=True)
    object_id = models.IntegerField(u'Идентификатор объекта', blank=True, null=True)
    event_code = models.ForeignKey(Event, verbose_name='Событие', on_delete=models.CASCADE)
    event_date = models.DateField(u'Дата события', blank=True, null=True)
    old_value = models.CharField(u'Старое значение', max_length=300, blank=True, null=True)
    add_date = models.DateTimeField(u'Дата и время записи', auto_now_add=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)

    def __str__(self):
        return self.application

    class Meta:
        verbose_name = u'Событие '
        verbose_name_plural = u'Журнал событий '


class logging_sms(models.Model):  # Логи СМС-отправки
    client = models.ForeignKey(Branch, verbose_name=u'Получатель', on_delete=models.CASCADE)
    scompany = models.ForeignKey(ServingCompanyBranch, verbose_name=u'Кредитор', on_delete=models.CASCADE)
    phone = models.CharField(u'Номер', max_length=10)
    summ_debt = models.DecimalField(u'Сумма долга', max_digits=10, decimal_places=2)
    sms_id = models.IntegerField(u'ID отправленного СМС-сообщения', null=True, blank=True)
    price_sms = models.DecimalField(u'Стоимость отправки', max_digits=10, decimal_places=2, null=True, blank=True)
    time_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    status_sms = models.IntegerField(u'Статус СМС-сообщения', null=True, blank=True)
    time_upd = models.DateTimeField(u'Дата и время обновления', auto_now=True)
    error_code = models.IntegerField(u'Код ошибки отправки', null=True, blank=True)

    def __str__(self):
        return self.client.NameBranch + '(' + self.phone + ')'

    class Meta:
        verbose_name = u'СМС-сообщение '
        verbose_name_plural = u'Логи СМС-сообщений '


class action_planned(models.Model):
    application = models.SlugField(u'Приложение', max_length=30)
    branch_id = models.IntegerField(u'Идентификатор клиента', blank=True, null=True)
    contract_id = models.IntegerField(u'Идентификатор договора', blank=True, null=True)
    object_id = models.IntegerField(u'Идентификатор объекта', blank=True, null=True)
    scompany_id = models.IntegerField(u'Идентификатор обслуживающей компании', blank=True, null=True)
    event_date = models.DateField(u'Дата события')
    add_date = models.DateTimeField(u'Дата/время добавления', auto_now_add=True)
    event_code = models.ForeignKey(Event, verbose_name='Событие', on_delete=models.CASCADE)
    event_value = models.CharField(u'Значение события', max_length=100, blank=True, null=True)
    complete = models.BooleanField(u'Задание выполнено', default=False)
    no_complete = models.CharField(u'Причина невыполнения', max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)

    def __str__(self):
        return self.event_value

    class Meta:
        verbose_name = u'Задача '
        verbose_name_plural = u'Запланированные события '


class chat_log(models.Model):
    message = models.TextField(u'Сообщение')
    add_date = models.DateTimeField(u'Дата/время добавления', auto_now_add=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = u'Сообщение '
        verbose_name_plural = u'Архив сообщений публичного чата '


class allviews_forsearch(models.Model):
    TypeClient_slug = models.CharField(max_length=50)
    TypeClient_name = models.CharField(max_length=100)
    NameClient_full = models.CharField(max_length=300)
    NameClient_short = models.CharField(max_length=100)
    NameBranch = models.CharField(max_length=300)
    INN = models.CharField(max_length=15)
    scompany_id = models.IntegerField()
    Contract_internal = models.CharField(max_length=30)
    Contract_external = models.CharField(max_length=30)
    Object = models.CharField(max_length=100)
    Object_address = models.CharField(max_length=300)
    Object_status = models.CharField(max_length=30)
    Object_status_color = models.CharField(max_length=30)
    Object_typepay = models.CharField(max_length=30)
    Object_typepay_color = models.CharField(max_length=30)

    class Meta:
        managed = False


class allviews_forsearch_addfields(models.Model):
    Contract_internal = models.CharField(max_length=30)
    Object_address = models.CharField(max_length=300)

    class Meta:
        managed = False


class allcontract_filter_term(models.Model):
    NumContractInternal = models.CharField(max_length=30)
    NumContractBranch = models.CharField(max_length=30)
    DateConclusion = models.DateField()
    DateTermination = models.DateField()
    ServingCompanyBranchName = models.CharField(max_length=300)
    ClientBranchName = models.CharField(max_length=300)
    TypeDocumentName = models.CharField(max_length=100)

    class Meta:
        managed = False


class alldocuments_fulldata(models.Model):
    Branch_id = models.CharField(max_length=10)
    NameClient_full = models.CharField(max_length=300)
    NameBranch = models.CharField(max_length=300)
    NumDocument = models.CharField(max_length=30)
    DateConclusion = models.DateField()
    TypeDocument_id = models.CharField(max_length=10)
    TypeDocumentName = models.CharField(max_length=100)
    ServingCompany_id = models.IntegerField()

    def __str__(self):
        return self.TypeDocumentName + ' №' + self.NumDocument + ' от ' + self.DateConclusion.strftime("%d.%m.%Y")

    class Meta:
        managed = False


class allobjects(models.Model):
    object_num = models.CharField(max_length=10)
    object_name = models.CharField(max_length=10)
    object_address = models.CharField(max_length=300)
    city_id = models.SmallIntegerField()
    object_cost = models.DecimalField(max_digits=10, decimal_places=2)
    contract_id = models.IntegerField()
    branch_id = models.IntegerField()
    scompany_id = models.IntegerField()
    typedct_id = models.SmallIntegerField()

    def __str__(self):
        return self.object_address

    class Meta:
        managed = False
