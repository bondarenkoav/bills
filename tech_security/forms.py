from datetime import datetime, timedelta, date
from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory, formset_factory

from base.models import alldocuments_fulldata, SystemConstant
from reference_books.models import TypeDocument, StatusSecurity
from .models import TechSecurityContract, TechSecurityObject, TechSecurityObjectRent, \
    TechSecurityObjectTypeEquipInstalled, TechSecuritySubContract, TechTemplateSubContract, TechSecurityContract_scan, \
    TechSecurityObject_scan, TechSecuritySubContract_scan, TechSecurityObjectPriceDifferent, TechSecurityObjectOpSoSCard

__author__ = 'bondarenkoav'


class form_contract(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_contract, self).__init__(*args, **kwargs)
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
        self.fields['PaymentDate'].label = 'срок'

    DateConclusion = forms.DateField(label='заключения', input_formats=('%Y-%m-%d',),
                                     widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    DateTermination = forms.DateField(required=False, label='расторжения', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    NameOfService = forms.CharField(required=False, label='Наименование услуги',
                                    widget=forms.widgets.Textarea(attrs={'rows': 1}))
    Notes = forms.CharField(required=False, label='Комментарий', widget=forms.widgets.Textarea(attrs={'rows': 1}))

    class Meta:
        model = TechSecurityContract
        fields = ['ServingCompany', 'NumContractInternal', 'NumContractBranch', 'DateConclusion', 'DateTermination',
                  'TemplateDocuments', 'PaymentDate', 'PaymentAfter', 'Notes', 'NameOfService', 'NotDirect']


class form_object_base(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(form_object_base, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

        if instance and instance.id:
            self.fields['DateEvent'].required = True
            date_term = instance.TechSecurityContract.DateTermination
            if date_term is None or date_term <= datetime.today().date():
                self.fields['ChgPriceDifferent'].widget.attrs['disabled'] = 'disabled'
            if instance.ChgPriceDifferent:
                self.fields['PriceNoDifferent'].required = False
                self.fields['PriceNoDifferent'].widget.attrs['disabled'] = 'disabled'
        else:
            self.fields['DateEvent'].required = False
            self.fields['DateEvent'].widget.attrs['disabled'] = 'disabled'
            self.fields['StatusSecurity'].required = False
            self.fields['StatusSecurity'].widget.attrs['disabled'] = 'disabled'

        self.fields['CityObject'].required = True

    AddressObject = forms.CharField(label=u'Адрес объекта',
                                    widget=forms.widgets.TextInput(attrs={'id': 'id_AddressObject'}))
    max_time_arrival = forms.CharField(required=True, label=u'Время прибытия', initial='5',
                                       widget=forms.widgets.NumberInput)
    DateEvent = forms.DateField(label=u'Дата события', input_formats=('%Y-%m-%d',),
                                widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = TechSecurityObject
        fields = ['NumObjectPCN', 'TypeObject', 'NameObject', 'AddressObject', 'CityObject', 'Coordinates',
                  'PaymentMethods', 'ChgPriceDifferent', 'PriceNoDifferent', 'StatusSecurity', 'max_time_arrival',
                  'DateEvent']

    def clean(self):
        cleaned_data = super(form_object_base, self).clean()
        date_event = cleaned_data['DateEvent']

        if not self.errors:
            if date_event is not None:
                # Прооверка года
                date_startsaldo_sc = SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue
                date_startsaldo = datetime.strptime(date_startsaldo_sc, "%d.%m.%Y").date()
                maxdate_event = datetime.today() + timedelta(weeks=30)
                if date_event < date_startsaldo or date_event > maxdate_event.date():
                    raise ValidationError(u'Дата не удовлетворяет требованиям. Допустимый период: %s - %s' % (date_startsaldo_sc, "{:%d.%m.%Y}".format(maxdate_event.date())))
        return cleaned_data


class form_groupobjects_actions(forms.ModelForm):
    DateEndContractRent = forms.DateField(label=u'Дата события', input_formats=('%Y-%m-%d',),
                                          widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))


class form_objects_activated(forms.Form):

    def __init__(self, *args, **kwargs):
        self.contract_id = kwargs.pop('contract', None)
        super(form_objects_activated, self).__init__(*args, **kwargs)

        self.fields['objects'].queryset = TechSecurityObject.objects.filter(
            TechSecurityContract=TechSecurityContract.objects.get(id=self.contract_id),
            StatusSecurity=StatusSecurity.objects.get(slug='noactive'))

    objects = forms.ModelChoiceField(label=u'Объекты для постановки в охрану',
                                     queryset=TechSecurityObject.objects.all(), widget=forms.Select())


# class form_objects_deactivated(forms.ModelForm):
#
#     # def __init__(self, *args, **kwargs):
#         # self.contract_id = kwargs.pop('contract', None)
#         # super(form_objects_deactivated, self).__init__(*args, **kwargs)
#
#         # self.fields['objects'].queryset = TechSecurityObject.objects.filter(
#         #     TechSecurityContract=TechSecurityContract.objects.get(id=self.contract_id),
#         #     StatusSecurity=StatusSecurity.objects.get(slug='active'))
#
#     objects = forms.ModelChoiceField(label=u'Объекты для снятия с охраны',
#                                      queryset=TechSecurityObject.objects.all(), widget=forms.Select())
#
#     class Meta:
#         model = TechSecurityObject
#         fields = ['to_contract']

ObjectsActivatedFormSet = modelformset_factory(TechSecurityObject,
                                               fields=('NumObjectPCN', 'NameObject', 'AddressObject',), extra=0)

ObjectsDeactivatedFormSet = modelformset_factory(TechSecurityObject,
                                                 fields=('NumObjectPCN', 'NameObject', 'AddressObject',), extra=0)


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
    copy_price = forms.BooleanField(label=u'Копировать стоимость охраны объектов (только для технической охраны)',
                                    widget=forms.CheckboxInput(attrs={'checked': 'checked'}))

    class Meta:
        model = TechSecurityContract
        fields = ['to_contract']


class form_object_rent(forms.ModelForm):
    OwnersPremises_Phone = forms.CharField(label=u'Телефон соб-ка',
                                           widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    DateEndContractRent = forms.DateField(label=u'Дата события', input_formats=('%Y-%m-%d',),
                                          widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = TechSecurityObjectRent
        fields = ['Question_ForRent', 'OwnersPremises_Name', 'OwnersPremises_Phone', 'DateEndContractRent']


PriceDifferentFormSet = modelformset_factory(TechSecurityObjectPriceDifferent, fields=('ListMonth', 'Price'),
                                             extra=12, max_num=12)


class form_object_typeequipinstalled(forms.ModelForm):
    class Meta:
        model = TechSecurityObjectTypeEquipInstalled
        fields = ['TypeEquipInstalled']


class form_TechSecurityContract_scan(forms.ModelForm):
    # ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = TechSecurityContract_scan
        fields = ['ScanFile']


class form_TechSecuritySubContract_scan(forms.ModelForm):
    # ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = TechSecuritySubContract_scan
        fields = ['ScanFile']


class form_TechSecurityObject_scan(forms.ModelForm):
    # ScanFile = forms.FileField(required=False, label="Сканированный договор", widget=forms.FileInput(attrs={'accept':'application/pdf'}), help_text='Документ обоюдно подписанный')
    class Meta:
        model = TechSecurityObject_scan
        fields = ['ScanFile']


class form_subcontract(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.contract_id = kwargs.pop('contract', None)
        super(form_subcontract, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        numsubcontract = TechSecuritySubContract.objects.filter(TechSecurityContract=TechSecurityContract.objects.get(
            id=self.contract_id)).count()  # aggregate(Max('NumSubContract'))

        if instance and instance.id:
            change_object = TechTemplateSubContract.objects.get(id=instance.Template.id).ChangeObjects
            if change_object is False:
                self.fields['TechSecurityObject'].required = False
                self.fields['TechSecurityObject'].widget.attrs['disabled'] = 'disabled'
            self.fields['Template'].required = False
            self.fields['Template'].widget.attrs['disabled'] = 'disabled'
            self.fields['TechSecurityObject'].queryset = TechSecurityObject.objects.filter(
                TechSecurityContract=instance.TechSecurityContract)
            self.fields['TechSecurityObject'].widget.attrs['size'] = 10
            self.fields['DateSubContract'].required = False
        else:
            self.fields['NumSubContract'].initial = numsubcontract + 1
            self.fields['TechSecurityObject'].queryset = TechSecurityObject.objects.filter(
                TechSecurityContract=self.contract_id)
            self.fields['TechSecurityObject'].widget.attrs['size'] = 10

    DateSubContract = forms.DateField(required=False, label='Дата допсоглашения', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    class Meta:
        model = TechSecuritySubContract
        fields = ['NumSubContract', 'DateSubContract', 'TechSecurityObject', 'Template']


# ------------------------------------------------------------------------------------------------------------------
class OpSoSCard_form(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OpSoSCard_form, self).__init__(*args, **kwargs)

    SimNumber = forms.CharField(required=False, label=u'(ХХХ) ХХХ-ХХХХ',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))

    class Meta:
        model = TechSecurityObjectOpSoSCard
        fields = ['OpSoSRate', 'SimICC', 'SimNumber']


OpSoSCardFormSet = modelformset_factory(TechSecurityObjectOpSoSCard, form=OpSoSCard_form, extra=1, max_num=2)
