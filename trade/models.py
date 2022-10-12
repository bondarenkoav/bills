from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from base.models import Branch, TypeDocument, ServingCompanyBranch, CoWorkers
from reference_books.models import ListEquipment, typeinvoices


class invoice(MPTTModel):
    ServingCompany = models.ForeignKey(ServingCompanyBranch, models.SET_NULL, verbose_name='Склад', blank=True, null=True)
    Branch = models.ForeignKey(Branch, models.SET_NULL, verbose_name='Филиал', null=True, blank=True)
    number = models.CharField(u'Номер накладной', max_length=15)
    date_invoice = models.DateField(u'Дата накладной')
    type_invoice = models.ForeignKey(typeinvoices, verbose_name=u'Тип накладной', on_delete=models.CASCADE)
    price = models.DecimalField(u'Сумма', max_digits=10, decimal_places=2, default=0)
    type_document = models.ForeignKey(TypeDocument, models.SET_NULL, verbose_name='Тип закрывающего документа',
                                      null=True, blank=True)
    number_document = models.IntegerField(u'Номер закрывающего документа', null=True, blank=True)
    CoWorker = models.ForeignKey(CoWorkers, models.SET_NULL, verbose_name='МОЛ', null=True, blank=True)
    ListEquipment = models.ManyToManyField(ListEquipment, verbose_name='Оборудование', blank=True)
    parent = TreeForeignKey('self', blank=True, null=True, verbose_name="Исходная накладная",
                            related_name='child', db_index=True, on_delete=models.CASCADE)

    date_add = models.DateTimeField(u'Дата и время создания', auto_now_add=True)
    date_update = models.DateTimeField(u'Дата и время изменения', auto_now=True)

    def __str__(self):
        return '№' + self.number + ' от ' + self.date_invoice.strftime("%d.%m.%Y")

    class Meta:
        verbose_name = u'Накладная '
        verbose_name_plural = u'Накладные '


class import_invoices(models.Model):
    INN = models.CharField(max_length=20, blank=True, null=True)
    Client = models.CharField(max_length=300, null=True, blank=True)
    Contract1S = models.CharField(max_length=50, null=True, blank=True)
    type_invoice = models.CharField(max_length=50, null=True, blank=True)
    number_invoice = models.CharField(max_length=50, null=True, blank=True)
    parent_invoice = models.CharField(max_length=250, blank=True, null=True)
    parent_num_invoice = models.CharField(max_length=50, blank=True, null=True)
    parent_date_invoice = models.DateField(blank=True, null=True)
    date_invoice = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ServingCompany_inn = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    Branch = models.ForeignKey(Branch, models.SET_NULL, verbose_name='Филиал', null=True, blank=True)

    date_add = models.DateTimeField()

    def __str__(self):
        return self.number_invoice

    class Meta:
        verbose_name = u'Накладная '
        verbose_name_plural = u'Импортированные накладные из 1С '
