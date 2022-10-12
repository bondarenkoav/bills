from ckeditor.fields import RichTextField
from django.db import models
from django.db.models import QuerySet
from django_group_by import GroupByMixin
from base.models import TypeDocument


class allactive_securityobjectsQuerySet(QuerySet, GroupByMixin):
    pass


class allactive_securityobjects(models.Model):
    objects = allactive_securityobjectsQuerySet.as_manager()
    name_client = models.CharField(max_length=300)
    name_branch = models.CharField(max_length=300)
    branch_id = models.IntegerField()
    contract_id = models.IntegerField()
    scompany_id = models.IntegerField()
    type_document_id = models.IntegerField()
    address_object = models.CharField(max_length=300)
    city_id = models.IntegerField()
    name_object = models.CharField(max_length=100)
    numcontract_internal = models.CharField(max_length=50)
    numcontract_external = models.CharField(max_length=50)
    date_conclusion = models.DateField()
    typeclient_slug = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.IntegerField()
    edo = models.BooleanField()
    inn = models.CharField(max_length=15)

    class Meta:
        managed = False


class allactive_maintenanceobjectsQuerySet(QuerySet, GroupByMixin):
    pass


class allactive_maintenanceobjects(models.Model):
    objects = allactive_maintenanceobjectsQuerySet.as_manager()
    name_client = models.CharField(max_length=300)
    name_branch = models.CharField(max_length=300)
    branch_id = models.IntegerField()
    scompany_id = models.IntegerField()
    type_document_id = models.IntegerField()
    address_object = models.CharField(max_length=300)
    city_id = models.IntegerField()
    name_object = models.CharField(max_length=100)
    date_start = models.DateField()
    date_end = models.DateField()
    numcontract_internal = models.CharField(max_length=50)
    numcontract_external = models.CharField(max_length=50)
    date_conclusion = models.DateField()
    typeclient_slug = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.IntegerField()
    edo = models.BooleanField()
    inn = models.CharField(max_length=15)

    class Meta:
        managed = False


class onoffobject_log(models.Model):
    application = models.CharField(max_length=50)
    contract_id = models.IntegerField()
    object_id = models.IntegerField()
    event_date = models.DateField()
    NameBranch = models.CharField(max_length=300)
    slug = models.SlugField()
    Name = models.CharField(max_length=50)

    class Meta:
        managed = False


class all_activecontract_fulldata(models.Model):
    Branch_id = models.IntegerField()
    TypeDocument_id = models.IntegerField()
    NameClient_full = models.CharField(max_length=300)
    NameBranch = models.CharField(max_length=300)
    NumContract = models.CharField(max_length=50)
    DateConclusion = models.DateField()
    Name = models.CharField(max_length=50)

    class Meta:
        managed = False


class all_buildobjects(models.Model):
    # object_id это поле id
    branch_id = models.IntegerField()
    branch_name = models.CharField(max_length=300)
    contract_id = models.IntegerField()
    contract_internal = models.CharField(max_length=50)
    contract_branch = models.CharField(max_length=50)
    date_conclusion = models.DateField()
    date_termination = models.DateField()
    scompany_id = models.IntegerField()
    typedocument_name = models.CharField(max_length=50)
    typedocument_slug = models.CharField(max_length=50)
    object_name = models.CharField(max_length=100)
    object_address = models.CharField(max_length=300)
    payment_id = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date_start = models.DateField()
    date_end = models.DateField()

    class Meta:
        managed = False


class clients_active_securityobjects(models.Model):
    scompany_id = models.IntegerField()

    class Meta:
        managed = False


class CDTemplateDocuments(models.Model):  # Шаблоны документов
    # TypeDocument = models.ForeignKey(TypeDocument, verbose_name='Тип документа')
    NameTemplate = models.CharField(u'Наименование шаблона', max_length=100)
    slug = models.SlugField(u'Ключ')
    TextTemplate = RichTextField(u'Текст шаблона')

    def __str__(self):
        return self.NameTemplate

    class Meta:
        verbose_name = u'Шаблон '
        verbose_name_plural = u'Шаблоны документов '
