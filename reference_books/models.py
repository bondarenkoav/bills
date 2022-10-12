from django.db import models


# Список обслуживающих организаций
class City(models.Model):
    CityName = models.CharField(u'Город обслуживания', max_length=30)
    slug = models.SlugField(u'Ключ')

    def __str__(self):
        return self.CityName

    class Meta:
        ordering = ['CityName']
        verbose_name = u'Город обслуживания'
        verbose_name_plural = u'Города обслуживания'


# Должностные полномочия
class PowersOfficeActs(models.Model):
    NameActs = models.CharField(u'Действует на основании', max_length=50)

    def __str__(self):
        return self.NameActs

    class Meta:
        ordering = ['NameActs']
        verbose_name = u'Полномочие '
        verbose_name_plural = u'Полномочия '


# Типы клиентов: ИП, Физлицо, Юрлицо
class TypesClient(models.Model):
    ShortTypeClient = models.CharField(u'Абревиатура', max_length=30)
    slug = models.SlugField(u'Алиас', unique=True)
    DescTypeClient = models.TextField(u'Подробное описание')
    head_text = models.TextField(u'Заголовок', help_text=u'Заголовка в договоре или дополнительном соглашении',
                                 blank=True, null=True)
    details_text = models.TextField(u'Реквизиты', help_text=u'Реквизиты в договоре или допсоглашении', blank=True,
                                    null=True)
    signature_text = models.TextField(u'Подпись', help_text=u'Подпись в договорах, допсоглашениях, актах', blank=True,
                                      null=True)

    def __str__(self):
        return self.ShortTypeClient

    class Meta:
        ordering = ['DescTypeClient']
        verbose_name = u'Тип контрагентов '
        verbose_name_plural = u'Типы контрагентов '


# Типы установленного оборудования: ТК, ОС, ПС, ОПС, Видео, СКУД
class TypeEquipmentInstalled(models.Model):
    ShortType = models.CharField(u'Абревиатура', max_length=30)
    DescType = models.TextField(u'Подробное описание')
    slug = models.SlugField(u'Алиас', unique=True)

    def __str__(self):
        return self.ShortType

    class Meta:
        ordering = ['DescType']
        verbose_name = u'Система ТСО '
        verbose_name_plural = u'Вид обслуживаемой системы ТСО '


# Список оборудования: передатчик, антенна, ...
class ListEquipment(models.Model):
    Name = models.CharField(u'Наименование', max_length=50)

    def __str__(self):
        return self.Name

    class Meta:
        ordering = ['Name']
        verbose_name = u'Оборудование '
        verbose_name_plural = u'Список оборудования (номенклатура)'


# Формы оплаты: банк, касса, взаимозачёт
class PaymentMethods(models.Model):
    ShortName = models.CharField(u'Абревиатура', max_length=30)
    slug = models.SlugField(u'Алиас')
    NameClassBootstrap = models.CharField(u'Класс окраски статуса объекта', max_length=30)
    DescriptionName = models.TextField(u'Подробное описание')

    def __str__(self):
        return self.ShortName

    class Meta:
        ordering = ['ShortName']
        verbose_name = u'Форма оплаты услуг '
        verbose_name_plural = u'Формы оплаты услуг '


# Тип объекта
class TypeObject(models.Model):
    ShortName = models.CharField(u'Абревиатура', max_length=10)
    DescName = models.CharField(u'Наименование', max_length=30)
    slug = models.SlugField()

    def __str__(self):
        return self.ShortName

    class Meta:
        ordering = ['ShortName']
        verbose_name = u'Тип объекта '
        verbose_name_plural = u'Типы объектов '


# Организационная форма предприятия
class OKOPF(models.Model):
    CodOKOPF = models.CharField(u'Организационно-правовая форма', max_length=10)
    ShortName = models.CharField(u'Сокращенное наименование формы', max_length=30)
    DescName = models.CharField(u'Полное наименование формы', max_length=100)

    def __str__(self):
        return self.ShortName

    class Meta:
        ordering = ['CodOKOPF']
        verbose_name = u'Организационная форма предприятия'
        verbose_name_plural = u'Организационные формы предприятий'


# Список должностей
class ListPosts(models.Model):
    NamePost = models.CharField(u'Должность', max_length=100)
    PrefixPost = models.CharField(u'Префикс обращения', max_length=100, blank=True)
    PostfixPost = models.CharField(u'Постфикс обращения', max_length=100, blank=True)

    def __str__(self):
        return self.NamePost

    class Meta:
        ordering = ['NamePost']
        verbose_name = u'Должность ответственного лица '
        verbose_name_plural = u'Должности ответственных лиц '


# мужской и женский пол
class Sex(models.Model):
    Sex = models.CharField(max_length=10)

    def __str__(self):
        return self.Sex

    class Meta:
        verbose_name = u'Пол '
        verbose_name_plural = u'Список полов '


class ListMonth(models.Model):
    Month = models.CharField(max_length=30)
    name_short = models.CharField(max_length=30)

    def __str__(self):
        return self.name_short

    class Meta:
        verbose_name = u'Месяц '
        verbose_name_plural = u'Список месяцев '


# Тип выставления счетов: общий, по договорам, по объектам
class FormsSchet(models.Model):
    ShortNameSchet = models.CharField(u'Абревиатура', max_length=30)
    DescShortNameSchet = models.TextField(u'Подробное описание')
    slug = models.SlugField(u'Ключ')

    def __str__(self):
        return self.ShortNameSchet

    class Meta:
        verbose_name = u'Тип выставления счетов '
        verbose_name_plural = u'Типы выставления счетов '


output_accounts = (
    ('split_lines', u'Разделять строки'),
    ('one_line', u'Одной строкой'),
)


class OutputToAccounts(models.Model):
    name = models.CharField(verbose_name='Выводить в счета', choices=output_accounts, max_length=100)
    slug = models.SlugField()

    def __str__(self):
        return self.name


# Приложение (Техническая охрана, Физическая охрана, Инкассация, Монтаж оборудования, Техническое обслуживание)
class App(models.Model):
    Name = models.CharField(u'Наименование', max_length=50)
    slug = models.SlugField(u'Ключ параметра', unique=True)

    def __str__(self):
        return self.slug

    class Meta:
        verbose_name = u'Приложение '
        verbose_name_plural = u'Приложения '


type_documents = (
    ('contract', u'Договор'),
    ('act', u'Акт'),
)


# Типы досументов (Договора техохраны, Договора физохраны, Договора монтажа, Договора ТО, Акты и их шаблоны)
class TypeDocument(models.Model):
    type = models.CharField(verbose_name='Тип', choices=type_documents, max_length=100)
    app = models.ForeignKey(App, verbose_name='Раздел', on_delete=models.CASCADE)
    Name = models.CharField(u'Наименование', max_length=50)
    ShortName = models.CharField(u'Наименование', max_length=15)
    slug = models.SlugField(u'Ключ параметра', unique=True)
    icon = models.CharField(u'Иконка', max_length=50)

    def __str__(self):
        return self.Name

    class Meta:
        verbose_name = u'Тип создаваемого документа '
        verbose_name_plural = u'Типы создаваемых документов '


# Виды работ (Замена передатчика, Монтаж СМК,..... )
class TypeWork(models.Model):
    Name = models.CharField(u'Наименование', max_length=150)

    def __str__(self):
        return self.Name

    class Meta:
        ordering = ['Name']
        verbose_name = u'Вид работ '
        verbose_name_plural = u'Виды производимых работ '


class StatusSecurity(models.Model):
    ShortName = models.CharField(u'Краткое описание', max_length=30)
    Status = models.BooleanField(u'Статус охраны')
    slug = models.SlugField(u'Алиас')
    NameClassBootstrap = models.CharField(u'Класс окраски статуса объекта', max_length=30)
    DescName = models.TextField(u'Подробное описание')

    def __str__(self):
        return self.ShortName

    class Meta:
        verbose_name = u'Статус охраняемого объекта '
        verbose_name_plural = u'Статус охраняемых объектов '


class typeinvoices(models.Model):
    name = models.CharField(u'Краткое описание', max_length=30)
    slug = models.SlugField()

    def __str__(self):
        return self.name


# Категории объектов
class CategoryObjects(models.Model):
    name = models.CharField(u'Наименование', max_length=30)
    shortname = models.CharField(u'Аббревиатура', max_length=10)
    slug = models.SlugField()

    def __str__(self):
        return self.name


class OpSoS_name(models.Model):
    Name = models.CharField(u'Наименование', max_length=100, unique=True)

    def __str__(self):
        return self.Name

    class Meta:
        verbose_name = u'Сотовый оператор'
        verbose_name_plural = u'Список сотовых операторов '


class OpSoS_rate(models.Model):
    OpSoSName = models.ForeignKey(OpSoS_name, verbose_name=u'Сотовый оператор', on_delete=models.CASCADE)
    Name = models.CharField(u'Наименование', max_length=250, unique=True)
    Price = models.DecimalField(u'Абонентская плата', max_digits=6, decimal_places=2, default=0)
    Descript = models.TextField(u'Описание тарифа', blank=True)

    def __str__(self):
        return str(self.OpSoSName) + ' - ' + self.Name

    class Meta:
        verbose_name = u'Тариф '
