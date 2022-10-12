__author__ = 'bondarenkoav'

import datetime

from trade.models import invoice
from django import forms
from django.forms import ModelForm
from .models import BuildServiceContract, BuildServiceObject, BuildServiceAct, BuildTemplateSubContract, \
    BuildServiceSubContract, BuildServiceContract_scan, BuildServiceSubContract_scan
from base.models import Branch, CoWorkers
from base.views import get_scompany_foruser
from tech_security.models import TechSecurityObject, TechSecurityContract


class form_contract_build_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_contract_build_service, self).__init__(*args, **kwargs)
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
        model = BuildServiceContract
        fields = ['ServingCompany', 'NumContractInternal', 'NumContractBranch', 'DateConclusion', 'DateTermination',
                  'TemplateDocuments', 'PaymentDate', 'Notes', 'NameOfService']


class form_object_build_service(ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_object_build_service, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            pass
        else:
            self.fields['DateEnd'].required = False
            self.fields['DateEnd'].widget.attrs['disabled'] = 'disabled'

    AddressObject = forms.CharField(label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))
    DateStart = forms.DateField(label='Дата начала', input_formats=('%Y-%m-%d',),
                                widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    DateEnd = forms.DateField(required=False, label='Дата окончания', input_formats=('%Y-%m-%d',),
                              widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = BuildServiceObject
        fields = ['TypeObject', 'NameObject', 'AddressObject', 'Coordinates', 'PaymentMethods',
                  'Price', 'DateStart', 'DateEnd', 'TypeEquipInstalled']


class form_act_build_service(ModelForm):

    def __init__(self, *args, **kwargs):
        self.branch_id = kwargs.pop('branch', None)
        # self.user = kwargs.pop('user', None)
        super(form_act_build_service, self).__init__(*args, **kwargs)
        scompany = get_scompany_foruser()
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['ServingCompany'].required = False
            self.fields['ServingCompany'].widget.attrs['disabled'] = 'disabled'
            self.fields['Object'].required = False
            self.fields['Object'].widget.attrs['disabled'] = 'disabled'
            self.fields['CoWorker'].queryset = CoWorkers.objects.filter(ServingCompanyBranch__in=scompany)
            self.fields['CoWorker'].widget.attrs['size'] = 7

            branch_invoices = invoice.objects.filter(Branch=self.branch_id, parent__isnull=True).order_by('date_add')
            if branch_invoices.count() > 0:
                list_invoices = branch_invoices.filter(number_document=instance.id)
                self.fields['parent_invoice'].queryset = branch_invoices
                if list_invoices.count() > 0:
                    self.fields['parent_invoice'].initial = list_invoices.first()
            else:
                self.fields['parent_invoice'].queryset = branch_invoices.none()
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
            self.fields['parent_invoice'].queryset = invoice.objects.filter(
                Branch=self.branch_id, parent__isnull=True, number_document__isnull=True)

    Price = forms.CharField(label='Стоимость работ')
    AddressObject = forms.CharField(required=False, label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))
    DateWork = forms.DateField(required=True, label='Дата выполнения', input_formats=('%Y-%m-%d',),
                               widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    TypeWork_descript = forms.CharField(required=False, label='Дополнительно',
                                        widget=forms.widgets.Textarea(attrs={'rows': 3}))
    parent_invoice = forms.ModelChoiceField(required=False, label=u'Исходная накладная',
                                            queryset=invoice.objects.all(), widget=forms.Select())
    Descriptions = forms.CharField(required=False, label='Примечание',
                                   widget=forms.widgets.Textarea(attrs={'rows': 3}))

    class Meta:
        model = BuildServiceAct
        fields = ['ServingCompany', 'Object', 'AddressObject', 'DateWork', 'TypeWork', 'TypeWork_descript',
                  'Price', 'CoWorker', 'Descriptions']


class form_subcontract(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.contract_id = kwargs.pop('contract', None)
        super(form_subcontract, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        build_contract = BuildServiceContract.objects.get(id=self.contract_id)
        numsubcontract = BuildServiceSubContract.objects.filter(BuildServiceContract=build_contract).count()

        if instance and instance.id:
            change_object = BuildTemplateSubContract.objects.get(id=instance.Template.id).ChangeObjects
            if change_object is False:
                self.fields['BuildServiceObject'].required = False
                self.fields['BuildServiceObject'].widget.attrs['disabled'] = 'disabled'
            self.fields['Template'].required = False
            self.fields['Template'].widget.attrs['disabled'] = 'disabled'
            self.fields['BuildServiceObject'].queryset = BuildServiceObject.objects.filter(
                BuildServiceContract=instance.BuildServiceContract)
            self.fields['BuildServiceObject'].widget.attrs['size'] = 10
            self.fields['DateSubContract'].required = False
        else:
            self.fields['NumSubContract'].initial = numsubcontract + 1
            self.fields['BuildServiceObject'].queryset = BuildServiceObject.objects.filter(
                BuildServiceContract=self.contract_id)
            self.fields['BuildServiceObject'].widget.attrs['size'] = 10

    DateSubContract = forms.DateField(required=False, label='Дата допсоглашения', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = BuildServiceSubContract
        fields = ['NumSubContract', 'DateSubContract', 'BuildServiceObject', 'Template']


class form_BuildServiceContract_scan(forms.ModelForm):
    # ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = BuildServiceContract_scan
        fields = ['ScanFile']


class form_BuildServiceSubContract_scan(forms.ModelForm):
    # ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = BuildServiceSubContract_scan
        fields = ['ScanFile']
