import datetime
from django import forms
from django.forms import ModelForm

from .models import MaintenanceServiceContract, MaintenanceServiceObject, MaintenanceServiceAct, \
    MaintenanceServiceSubContract, MaintenanceTemplateSubContract, MaintenanceServiceContract_scan, \
    MaintenanceServiceSubContract_scan
from base.models import Branch, alldocuments_fulldata
from reference_books.models import ListMonth, TypeEquipmentInstalled, TypeDocument

__author__ = 'bondarenkoav'


class form_contract_maintenance_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_contract_maintenance_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['PushToAccounts'].required = True
            self.fields['ServingCompany'].required = False
            self.fields['ServingCompany'].widget.attrs['disabled'] = 'disabled'
            self.fields['TemplateDocuments'].required = False
        else:
            self.fields['PushToAccounts'].required = False
            self.fields['PushToAccounts'].widget.attrs['disabled'] = 'disabled'
            self.fields['NumContractInternal'].required = False
            self.fields['NumContractInternal'].widget.attrs['disabled'] = 'disabled'
            self.fields['NumContractInternal'].help_text = 'Внимание: Номер будет назначен после сохранения'
            self.fields['DateTermination'].required = False
            self.fields['DateTermination'].widget.attrs['disabled'] = 'disabled'
            self.fields['DateTermination'].widget.attrs['class'] = 'form-control'

    DateConclusion = forms.DateField(label='Дата заключения', input_formats=('%Y-%m-%d', ),
                                     widget=forms.DateInput(format='%Y-%m-%d', attrs={'type':'date'}))
    DateTermination = forms.DateField(required=False, label='Дата расторжения', input_formats=('%Y-%m-%d', ),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    NameOfService = forms.CharField(required=False, label='Наименование услуги',
                                    widget=forms.widgets.Textarea(attrs={'rows': 1}))
    PereodicAccrualMonth = forms.ModelMultipleChoiceField(label=u'Периодичность начислений',
                                                          queryset=ListMonth.objects.all().order_by('id'),
                                                          widget=forms.CheckboxSelectMultiple(
                                                              attrs={'style': 'margin-left: .20rem;'}))
    Notes = forms.CharField(required=False, label='Комментарий', widget=forms.widgets.Textarea(attrs={'rows': 3}))

    class Meta:
        model = MaintenanceServiceContract
        fields = ['ServingCompany', 'NumContractInternal', 'NumContractBranch', 'DateConclusion', 'DateTermination',
                  'TemplateDocuments', 'PaymentDate', 'PereodicAccrualMonth', 'PereodicService', 'PushToAccounts',
                  'NameOfService', 'Notes']


class form_object_maintenance_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_object_maintenance_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            pass
        else:
            self.fields['DateStart'].inintial = datetime.date.today
        self.fields['CityObject'].required = True

    AddressObject = forms.CharField(label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id':'id_AddressObject'}))
    DateStart = forms.DateField(label='Дата начала', input_formats=('%Y-%m-%d', ),
                                      widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    DateEnd = forms.DateField(required=False, label='Дата окончания', input_formats=('%Y-%m-%d', ),
                              widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    TypeEquipInstalled = forms.ModelMultipleChoiceField(label=u'Вид обслуживания системы ТСО',
                                                        queryset=TypeEquipmentInstalled.objects.all(),
                                                        widget=forms.CheckboxSelectMultiple(
                                                            attrs={'style': 'margin-left: .20rem;'}))

    class Meta:
        model = MaintenanceServiceObject
        fields = ['TypeObject', 'NameObject', 'CityObject', 'AddressObject', 'Coordinates', 'PaymentMethods', 'Price',
                  'DateStart', 'DateEnd', 'TypeEquipInstalled']


class form_act_maintenance_service(ModelForm):

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop('branch', None)
        super(form_act_maintenance_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        branch = Branch.objects.get(id=self.branch)
        list_contracts = MaintenanceServiceContract.objects.filter(Branch=branch)

        if instance and instance.id:
            self.fields['ServingCompany'].required = False
            self.fields['ServingCompany'].widget.attrs['disabled'] = 'disabled'
            self.fields['Object'].queryset = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract__in=list_contracts)
        else:
            self.fields['DateWork'].inintial  = datetime.date.today
            self.fields['Object'].queryset = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract__in=list_contracts)

    DateWork = forms.DateField(label='Дата выполнения', input_formats=('%Y-%m-%d', ),
                               widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    Descriptions = forms.CharField(required=False, label='Примечание',widget=forms.widgets.Textarea(attrs={'rows': 4}))

    class Meta:
        model = MaintenanceServiceAct
        fields = ['ServingCompany', 'Object', 'DateWork', 'CoWorker', 'Descriptions']


class form_subcontract(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.contract_id = kwargs.pop('contract', None)
        super(form_subcontract, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        numsubcontract = MaintenanceServiceSubContract.objects.filter(MaintenanceServiceContract=MaintenanceServiceContract.objects.get(id=self.contract_id)).count()

        if instance and instance.id:
            change_object = MaintenanceTemplateSubContract.objects.get(id=instance.Template.id).ChangeObjects
            if change_object is False:
                self.fields['MaintenanceServiceObject'].required = False
                self.fields['MaintenanceServiceObject'].widget.attrs['disabled'] = 'disabled'
            self.fields['Template'].required = False
            self.fields['Template'].widget.attrs['disabled'] = 'disabled'
            self.fields['MaintenanceServiceObject'].queryset = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=instance.MaintenanceServiceContract)
            self.fields['MaintenanceServiceObject'].widget.attrs['size'] = 10
            self.fields['DateSubContract'].required = False
        else:
            self.fields['NumSubContract'].initial = numsubcontract+1
            self.fields['MaintenanceServiceObject'].queryset = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=self.contract_id)
            self.fields['MaintenanceServiceObject'].widget.attrs['size'] = 10

    DateSubContract = forms.DateField(label='Дата допсоглашения', input_formats=('%Y-%m-%d', ),
                                      widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))

    class Meta:
        model = MaintenanceServiceSubContract
        fields = ['NumSubContract', 'DateSubContract', 'MaintenanceServiceObject', 'Template']


class form_MaintenanceServiceContract_scan(forms.ModelForm):
    #ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = MaintenanceServiceContract_scan
        fields = ['ScanFile']


class form_MaintenanceServiceSubContract_scan(forms.ModelForm):
    #ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = MaintenanceServiceSubContract_scan
        fields = ['ScanFile']


class form_copy_objects(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_copy_objects, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        self.fields['to_contract'].queryset = alldocuments_fulldata.objects.filter(
            Branch_id=instance.Branch.id,
            TypeDocument_id__in=TypeDocument.objects.filter(
                slug__in=['tech_security_contract', 'maintenance_service_contract']))

    to_contract = forms.ModelChoiceField(label=u'Куда копировать *',
                                         queryset=alldocuments_fulldata.objects.all(), widget=forms.Select())
    copy_price = forms.BooleanField(label=u'Копировать стоимость ТО объектов',
                                    widget=forms.CheckboxInput(attrs={'checked': 'checked'}))

    class Meta:
        model = MaintenanceServiceContract
        fields = ['to_contract']
