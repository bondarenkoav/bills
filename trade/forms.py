from datetime import timedelta, datetime
from django.forms import ModelForm, DateField, DateInput, NumberInput
from django import forms

from base.views import get_scompany_foruser
from .models import invoice
from base.models import CoWorkers, ServingCompanyBranch, alldocuments_fulldata, Branch
from reference_books.models import typeinvoices

__author__ = 'bondarenkoav'


class form_invoice(ModelForm):

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        self.document = kwargs.pop('document', None)
        super(form_invoice, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        user_scompany_data = get_scompany_foruser()

        if user_scompany_data.count() == 1:
            self.fields['ServingCompany'].initial = user_scompany_data.first().id

        self.fields['CoWorker'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=user_scompany_data)

        if instance and instance.id:
            self.fields['parent'].queryset = invoice.objects.filter(Branch=self.branch, parent__isnull=True,
                                                                    type_invoice=typeinvoices.objects.get(slug='consumption')).exclude(id=instance.id)
        else:
            self.fields['parent'].queryset = invoice.objects.filter(Branch=Branch.objects.get(id=self.branch),
                                                                    parent__isnull=True)

    date_invoice = forms.DateField(label=u'Дата ', input_formats=('%Y-%m-%d',), initial=timedelta(days=-1),
                                   widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    #price = forms.CharField(widget=NumberInput())

    class Meta:
        model = invoice
        fields = ['ServingCompany', 'type_invoice', 'number', 'date_invoice', 'parent', 'price', 'ListEquipment', 'CoWorker']


class form_invoices_period(forms.Form):

    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class':'selector'}))
    filter_start_date = DateField(required=True, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                  initial=datetime.today() - timedelta(days=1),
                                  widget=DateInput(format='%Y-%m-%d', attrs={'type':'date'}))
    filter_end_date = DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                widget=DateInput(format='%Y-%m-%d', attrs={'type':'date'}))
