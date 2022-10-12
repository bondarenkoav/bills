__author__ = 'bondarenkoav'


from django import forms
from django.forms import ModelForm
from .models import ReplaceServiceContract, ReplaceServiceObject, \
    ReplaceServiceAct


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

    DateConclusion = forms.DateField(label='Дата заключения', input_formats=('%Y-%m-%d',),
                                     widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    DateTermination = forms.DateField(required=False, label='Дата расторжения', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    NameOfService = forms.CharField(required=False, label='Наименование услуги',
                                    widget=forms.widgets.Textarea(attrs={'rows': 1}))
    Notes = forms.CharField(required=False, label='Комментарий', widget=forms.widgets.Textarea(attrs={'rows': 3}))

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
            self.fields['DateEnd'].required = False
            self.fields['DateEnd'].widget.attrs['disabled'] = 'disabled'

    AddressObject = forms.CharField(label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))

    class Meta:
        model = ReplaceServiceObject
        fields = ['TypeObject', 'NameObject', 'AddressObject', 'CityObject', 'ActiveObject']


class form_act_replace_service(ModelForm):

    def __init__(self, *args, **kwargs):
        self.branch_id = kwargs.pop('branch', None)
        # self.user = kwargs.pop('user', None)
        super(form_act_replace_service, self).__init__(*args, **kwargs)
        scompany = get_scompany_foruser()
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['CoWorker'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=scompany)
            self.fields['CoWorker'].widget.attrs['size'] = 7

        else:
            if scompany.count() == 1:
                self.fields['ServingCompany'].initial = scompany.first().id
            self.fields['CoWorker'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=scompany,
                                                                        StatusWorking=True)
            self.fields['CoWorker'].widget.attrs['size'] = 7
            self.fields['DateWork'].inintial = datetime.date.today
            self.fields['Object'].queryset = TechSecurityObject.objects.filter(
                TechSecurityContract__in=TechSecurityContract.objects.filter(
                    Branch=Branch.objects.get(id=self.branch_id)))

    Price = forms.CharField(label='Стоимость работ')
    AddressObject = forms.CharField(required=False, label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))
    DateWork = forms.DateField(required=True, label='Дата выполнения', input_formats=('%Y-%m-%d',),
                               widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    TypeWork_descript = forms.CharField(required=False, label='Дополнительно',
                                        widget=forms.widgets.Textarea(attrs={'rows': 3}))
    Descriptions = forms.CharField(required=False, label='Примечание',
                                   widget=forms.widgets.Textarea(attrs={'rows': 3}))

    class Meta:
        model = ReplaceServiceAct
        fields = ['DateWork', 'TypeWork', 'TypeWork_descript', 'Price', 'CoWorkers', 'Descriptions']
