import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum, FloatField

from base.models import CoWorkers
from base.views import get_scompany_foruser
from django import forms
from django.forms import ModelForm
from .models import ReplaceServiceContract, ReplaceServiceObject, ReplaceServiceAct

__author__ = 'bondarenkoav'


class form_contract_replace_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_contract_replace_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['ServingCompany'].required = False
            self.fields['ServingCompany'].widget.attrs['disabled'] = 'disabled'
            self.fields['TemplateDocuments'].required = False
        else:
            self.fields['NumContractInternal'].required = False
            self.fields['NumContractInternal'].widget.attrs['disabled'] = 'disabled'
            self.fields['NumContractInternal'].help_text = 'Внимание: Номер будет назначен после сохранения'
            self.fields['DateTermination'].required = False
            self.fields['DateTermination'].widget.attrs['disabled'] = 'disabled'
        self.fields['NumContractInternal'].label = 'внутренний'
        self.fields['NumContractBranch'].label = 'клиентский'

    DateConclusion = forms.DateField(label='заключения', input_formats=('%Y-%m-%d',),
                                     widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    DateTermination = forms.DateField(required=False, label='расторжения', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    NameOfService = forms.CharField(required=False, label='Наименование услуги',
                                    widget=forms.widgets.Textarea(attrs={'rows': 1}))
    Notes = forms.CharField(required=False, label='Комментарий', widget=forms.widgets.Textarea(attrs={'rows': 1}))

    class Meta:
        model = ReplaceServiceContract
        fields = ['ServingCompany', 'NumContractInternal', 'NumContractBranch', 'DateConclusion', 'DateTermination',
                  'TemplateDocuments', 'AmountLimit', 'DoNotIncludeInCalculations', 'Notes', 'NameOfService']


class form_object_replace_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_object_replace_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            pass
        else:
            pass

    AddressObject = forms.CharField(label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))

    class Meta:
        model = ReplaceServiceObject
        fields = ['TypeObject', 'NameObject', 'AddressObject', 'CityObject', 'ActiveObject']


class form_act_replace_service(ModelForm):

    def __init__(self, *args, **kwargs):
        self.contract_id = kwargs.pop('contract_id', None)
        super(form_act_replace_service, self).__init__(*args, **kwargs)
        scompany = get_scompany_foruser()
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['CoWorker'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=scompany)
            self.fields['CoWorker'].widget.attrs['size'] = 7
        else:
            if scompany.count() == 1:
                self.fields['ServingCompany'].initial = scompany.first().id
            self.fields['CoWorkers'].widget.attrs['size'] = 7
            self.fields['DateWork'].inintial = datetime.datetime.now().date()
            self.fields['Object'].queryset = ReplaceServiceObject.objects.\
                filter(ReplaceServiceContract__in=self.contract_id)

        self.fields['CoWorkers'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=scompany,
                                                                     StatusWorking=True)

    # Price = forms.CharField(label='Стоимость работ')
    DateWork = forms.DateField(required=True, label='Дата выполнения', input_formats=('%Y-%m-%d',),
                               widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    TypeWork_descript = forms.CharField(required=False, label='Дополнительно',
                                        widget=forms.widgets.Textarea(attrs={'rows': 3}))
    Descriptions = forms.CharField(required=False, label='Примечание',
                                   widget=forms.widgets.Textarea(attrs={'rows': 3}))
    Object = forms.ModelChoiceField(label=u'Объект',
                                    queryset=ReplaceServiceObject.objects.all(), widget=forms.Select())

    class Meta:
        model = ReplaceServiceAct
        fields = ['Object', 'DateWork', 'TypeWork', 'TypeWork_descript', 'Price', 'CoWorkers', 'Descriptions']

    def clean(self):
        cleaned_data = super(form_act_replace_service, self).clean()
        price = cleaned_data['Price']

        if not self.errors:
            contract_data = ReplaceServiceContract.objects.get(id=self.contract_id)
            amountlimit = contract_data.AmountLimit
            if amountlimit > 0:
                if price > amountlimit:
                    raise ValidationError(u'Сумма акта превышает предельную сумму по договору')
                summ_acts = ReplaceServiceAct.objects.filter(ReplaceServiceContract=contract_data).\
                    aggregate(summ=Sum('Price', output_field=FloatField()))
                if amountlimit < summ_acts + price:
                    raise ValidationError(u'Сумма ранних и добавляемого актов, превышает предельную сумму по договору')

        return cleaned_data
