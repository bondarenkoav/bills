__author__ = 'bondarenkoav'


from django.db import models
from datetime import timedelta, datetime


class azStatus(models.Model):
    slug = models.SlugField()

    class Meta:
        managed = False
        db_table = "reference_books_status"


class azServiceCompanies(models.Model):
    slug = models.SlugField()

    class Meta:
        managed = False
        db_table = "reference_books_servicecompanies"


class azUsers(models.Model):
    username = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "auth_user"


class azGroup(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "auth_group"


class azTypeRequest(models.Model):
    slug = models.SlugField(u'Ключ статуса')

    class Meta:
        managed = False
        db_table = "reference_books_typerequest"


class azTypeDocument(models.Model):
    slug = models.SlugField(u'Ключ статуса')

    class Meta:
        managed = False
        db_table = "reference_books_typedocument"


class eproposals(models.Model):
    TypeRequest_id = models.IntegerField()
    TypeDocument_id = models.IntegerField()
    NumObject = models.CharField(max_length=10)
    AddressObject = models.CharField(max_length=100)
    Client_words = models.CharField(max_length=100)
    ServiceCompany_id = models.IntegerField()
    FaultAppearance = models.TextField()
    Status_id = models.IntegerField()
    DescriptionWorks = models.TextField(blank=True)
    Required_act = models.BooleanField(default=False)
    Written_act = models.BooleanField(default=False)
    DateTime_schedule = models.DateField()

    Create_user_id = models.IntegerField()
    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    class Meta:
        managed = False
        db_table = "exploitation_eproposals"


class user_task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(u'Описание задачи')
    author_id = models.IntegerField()
    group_executor_id = models.IntegerField()
    client = models.CharField(max_length=100)
    Date_limit = models.DateField()
    high_importance = models.BooleanField(default=True)
    read = models.BooleanField(default=False)

    Create_user_id = models.IntegerField()
    DateTime_add = models.DateTimeField(u'Дата и время добавления', auto_now_add=True)
    DateTime_update = models.DateTimeField(u'Дата и время обновления', auto_now=True)

    class Meta:
        managed = False
        db_table = "tasks_user_task"


def add_request_return_equipment(scompany, name_client, num_object, address_object, date_deactivationSecur, curr_user):
    num_request = 0
    term = datetime.now().date() + timedelta(days=10)
    text = 'Заявка на возврат оборудования от контрагента %s с объекта № %s по адресу %s, принадлежащее %s. ' \
           'Объект снят с охраны %s. Срок до %s.' % (name_client, num_object, address_object, scompany.NameBranch,
                                                     str(date_deactivationSecur.strftime("%d.%m.%Y")),
                                                     str(term.strftime("%d.%m.%Y")))
    try:
        azAuthor_id = azUsers.objects.using('zayavki').get(username=curr_user).id
    except:
        azAuthor_id = azUsers.objects.using('zayavki').get(username='system').id
    try:
        azStatus_id = azStatus.objects.using('zayavki').get(slug='open').id
        azSCompany_id = azServiceCompanies.objects.using('zayavki').get(slug=scompany.integrity_slug).id
        azTypeRequest_id = azTypeRequest.objects.using('zayavki').get(slug='exploitation').id
        azTypeDocument_id = azTypeDocument.objects.using('zayavki').get(slug='return_eq').id

        p = eproposals.objects.using('zayavki').\
            create(TypeRequest_id=azTypeRequest_id, TypeDocument_id=azTypeDocument_id,
                   ServiceCompany_id=azSCompany_id, Client_words=name_client,
                   NumObject=num_object, AddressObject=address_object,
                   FaultAppearance=text, Status_id=azStatus_id, DateTime_schedule=datetime.now().date(),
                   Required_act=False, Written_act=False, DescriptionWorks='', Create_user_id=azAuthor_id)
        num_request = p.pk
    except Exception:
        pass
    try:
        limit = datetime.now().date() + timedelta(days=5)
        azGroup_id = azGroup.objects.using('zayavki').get(name='Администрация Орск').id
        text = 'Поступила заявка №%d на возврат оборудования (Раздел: Монтаж/Демонтаж) от контрагента %s с ' \
               'объекта № %s по адресу %s, принадлежащее %s. Срок до %s (10 дней).' % ((num_request if num_request else 0),
                                                                                       name_client, num_object,
                                                                                       address_object, scompany.NameBranch,
                                                                                       str(term.strftime("%d.%m.%Y")),)
        user_task.objects.using('zayavki').create(title='Заявка на возврат оборудования', description=text,
                                                  author_id=azAuthor_id, group_executor_id=azGroup_id,
                                                  client=name_client, Date_limit=limit)
    except Exception:
        pass

