# -*- coding: utf-8 -*-
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form, modelformset_factory, inlineformset_factory

from base.suggest import dadataapi_getdata_banki
from base.templatetags.other_tags import get_nameclient
from reference_books.models import ListPosts, PowersOfficeActs
from base.models import Branch, Client, ScannedDocuments, ServingCompanyBranch, Contacts, UserNote


class check_for_duplicate_company(forms.Form):
    inn = forms.CharField(label=u'ИНН', widget=forms.widgets.TextInput(attrs={'class': 'inn_company'}))
    kpp = forms.CharField(label=u'КПП', widget=forms.widgets.TextInput(attrs={'class': 'kpp'}))

    def clean(self):
        cleaned_data = super(check_for_duplicate_company, self).clean()
        inn = cleaned_data['inn']
        kpp = cleaned_data['kpp']

        if not self.errors:
            if len(inn) != 10:
                raise forms.ValidationError(u'Неверный формат ИНН')

            if len(kpp) != 9:
                raise forms.ValidationError(u'Неверный формат КПП')

            client = Client.objects.filter(INN=inn).last()
            if client:
                self.client = client
                branch = Branch.objects.filter(KPP=kpp, Client=client).last()
                if branch:
                    self.branch = branch
                else:
                    self.branch = None
            else:
                self.client = None

        return cleaned_data

    def get_client(self):
        return self.client or None

    def get_branch(self):
        return self.branch or None


class check_for_duplicate_businessman(forms.Form):
    inn = forms.CharField(label=u'ИНН', widget=forms.widgets.TextInput(attrs={'class': 'inn_businessman'}))

    def clean(self):
        cleaned_data = super(check_for_duplicate_businessman, self).clean()
        inn = cleaned_data['inn']

        if not self.errors:
            if len(inn) != 12:
                raise forms.ValidationError(u'Неверный формат ИНН')

            client = Client.objects.filter(INN=inn).last()
            if client:
                obj, created = Branch.objects.get_or_create(
                    Client=Client.objects.get(INN=inn),
                    defaults={'NameBranch': client.NameClient_short},)
                self.client = obj
            else:
                self.client = None

        return cleaned_data

    def get_client(self):
        return self.client or None


class check_for_duplicate_physical_person(forms.Form):
    full_name = forms.CharField(label='Фамилия Имя Отчество',
                                widget=forms.widgets.TextInput(attrs={'id': 'id_Person_FIO'}))
    passport_sernum = forms.CharField(label='Серия и номер паспорта',
                                      widget=forms.widgets.TextInput(attrs={'class': 'passportsernum'}))
    alien = forms.BooleanField(required=False, label='Не является гражданином РФ',
                               widget=forms.CheckboxInput(attrs={'onchange': 'ChangeAlien()'}))

    def clean(self):
        cleaned_data = super(check_for_duplicate_physical_person, self).clean()
        alien = cleaned_data['alien']
        full_name = cleaned_data['full_name']
        passport_sernum = cleaned_data['passport_sernum']

        if not self.errors:
            if alien is False:
                # Прооверка ФИО
                lastname = full_name.split(' ')[0]
                if len(lastname) < 3:
                    raise ValidationError(u'"Фамилия" не может быть менее трёх букв')

                firstname = full_name.split(' ')[1]
                if len(firstname) < 3:
                    raise ValidationError(u'"Имя" не может быть менее трёх букв')

                # if re.match(r"^[А-Яа-я]{3,}\s[А-Яа-я]{3,}\s[А-Яа-я]{3,}", full_name) is None:
                #     raise forms.ValidationError(u'Ошибка: ФИО должно быть полным')

                # Проверка паспортных данных
                if re.match(r"^([0-9]{4})\s{1}([0-9]{6})$", passport_sernum) is None:
                    raise forms.ValidationError(u'Введите серию и номер паспорта в формате ХХХХ ХХХХХХ')
            else:
                if re.match(r"^[А-Яа-я]{3,}\s[А-Яа-я]{2,}", full_name) is None:
                    raise forms.ValidationError(u'Ошибка: Фамилия и/или Имя отсутствуют')

            client = Branch.objects.filter(Client__in=Client.objects.filter(NameClient_full=full_name,
                                                                            PassportSerNum=passport_sernum))
            if client:
                if client.count() > 1:
                    raise forms.ValidationError(u'В базе данных обнаружен дубликат контрагента')
                client = client.first()
                obj, created = Branch.objects.get_or_create(
                    Client=Client.objects.get(NameClient_full=full_name, PassportSerNum=passport_sernum),
                    defaults={'NameBranch': get_nameclient(client.id)},)
                self.client = obj
            else:
                self.client = None
        return cleaned_data

    def get_client(self):
        return self.client or None


# ------------------------------------------------------------------------------------------------------------------

class client_form_company(Form):
    def __init__(self, *args, **kwargs):
        super(client_form_company, self).__init__(*args, **kwargs)
        if kwargs:
            if kwargs['data']['NameClient_short'] is None:
                self.fields['NameClient_short'].widget.attrs['readonly'] = False

    OKOPF = forms.CharField(required=False, label=u'ОКОПФ',
                            widget=forms.widgets.TextInput(attrs={'id': 'id_okopf'}))
    NameClient_full = forms.CharField(label=u'Наименование полное *',
                                      widget=forms.widgets.Textarea(
                                          attrs={'rows': 2, 'id': 'id_namefull', 'readonly': 'readonly'}))
    NameClient_short = forms.CharField(label=u'Наименование краткое *',
                                       widget=forms.widgets.TextInput(
                                           attrs={'id': 'id_nameshort', 'readonly': 'readonly'}))
    Address_reg = forms.CharField(label=u'Юридический адрес *',
                                  widget=forms.widgets.TextInput(attrs={'id': 'id_addressreg'}))
    INN = forms.CharField(label=u'ИНН *',
                          widget=forms.widgets.TextInput(attrs={'id': 'id_inn', 'readonly': 'readonly'}))
    kpp = forms.CharField(required=False,
                          widget=forms.widgets.HiddenInput)
    OGRN = forms.CharField(required=False, label=u'ОГРН',
                           widget=forms.widgets.TextInput(attrs={'id': 'id_ogrn'}))
    OKVED = forms.CharField(required=False, label=u'ОКВЭД',
                            widget=forms.widgets.TextInput(attrs={'id': 'id_okved'}))
    Management_post = forms.CharField(required=False, label=u'Должность руководителя',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_managerpost'}))
    Management_name = forms.CharField(required=False, label=u'ФИО руководителя', help_text='ФИО в именительном падеже',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_managername'}))

    def clean(self):
        cleaned_data = super(client_form_company, self).clean()
        namefull = cleaned_data['NameClient_full']
        addressreg = cleaned_data['Address_reg']

        if not self.errors:
            # Прооверка наименований
            if len(namefull) < 5:
                raise ValidationError(u'"Наименование" не может быть менее 5 символов')

            # if nameshort and len(nameshort) < 5:
            #     raise ValidationError(u'"Наименование" не может быть менее 5 символов')

            if len(addressreg) < 10:
                raise ValidationError(u'"Адрес прописки" не может быть менее 10 символов')

        return cleaned_data


class branch_form_company(Form):
    Client = forms.CharField(required=False, widget=forms.widgets.HiddenInput)
    NameBranch = forms.CharField(label=u'Наименование филиала *',
                                 widget=forms.widgets.TextInput(attrs={'id': 'id_namefull'}))
    Management_post = forms.ModelChoiceField(label=u'Должность руководителя *', queryset=ListPosts.objects.all(),
                                             widget=forms.Select(attrs={'id': 'id_managerpost'}))
    Management_name = forms.CharField(label=u'ФИО руководителя *', help_text='ФИО в именительном падеже',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_managername'}))
    PowersOffice_name = forms.ModelChoiceField(label=u'Действует на основании *',
                                               queryset=PowersOfficeActs.objects.all(),
                                               widget=forms.Select(attrs={'id': 'id_ponamedoc'}))
    PowersOffice_number = forms.CharField(required=False, label=u'Номер документа',
                                          widget=forms.widgets.TextInput(attrs={'id': 'id_ponumdoc'}),
                                          help_text=u'При выборе документа типа "доверенность", вводим номер')
    PowersOffice_date = forms.DateField(required=False, label=u'Дата выдачи',
                                        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
                                        input_formats=('%Y-%m-%d',),
                                        help_text=u'При выборе документа типа "доверенность", вводим срок действия')
    Address_reg = forms.CharField(label=u'Юридический адрес *',
                                  widget=forms.widgets.TextInput(attrs={'id': 'id_addressreg'}))
    Address_post = forms.CharField(label=u'Почтовый адрес *',
                                   widget=forms.widgets.TextInput(attrs={'id': 'id_addresspost'}))
    Address_email = forms.CharField(required=False, label=u'Адрес эл.почты',
                                    widget=forms.widgets.EmailInput(attrs={'id': 'id_addressemail'}))
    KPP = forms.CharField(label=u'КПП *',
                          widget=forms.widgets.TextInput(attrs={'id': 'id_kpp', 'readonly': 'readonly'}))
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Phone_city = forms.CharField(required=False, label=u'Факс',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_fax = forms.CharField(required=False, label=u'Стационарный тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(required=False, label=u'Мобильный тел.',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_sms = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    EDO = forms.BooleanField(required=False, label='ЭДО', widget=forms.CheckboxInput())

    def clean(self):
        cleaned_data = super(branch_form_company, self).clean()
        namebranch = cleaned_data['NameBranch']
        try:
            managername = cleaned_data['Management_name']
        except:
            managername = ''
        addressreg = cleaned_data['Address_reg']
        addresspost = cleaned_data['Address_post']
        bik = cleaned_data['Bank_BIK']
        bank = dadataapi_getdata_banki(bik)

        if not self.errors:
            # Прооверка наименования
            if len(namebranch) < 5:
                raise ValidationError(u'Наименование не может быть менее 5 символов')

            # Проверка адресов
            if len(addressreg) < 10:
                raise ValidationError(u'Адрес прописки не может быть менее 10 символов')

            if len(addresspost) < 10:
                raise ValidationError(u'Адрес прописки не может быть менее 10 символов')

            if len(managername.split(' ')[0]) < 2:
                raise ValidationError(u'Фамилия не может быть менее двух букв')

            if len(managername.split(' ')[1]) < 3:
                raise ValidationError(u'Имя не может быть менее трёх букв')

            # if len(managername.split(' ')[2]) < 3:
            #     raise ValidationError(u'Отчество не может быть менее трёх букв')

            if bik and len(bank.get('suggestions')) == 0:
                raise ValidationError(u'Банк с таким БИК не найден')

        return cleaned_data


# ------------------------------------------------------------------------------------------------------------------

class client_form_businessman(Form):
    NameClient_full = forms.CharField(label=u'Фамилия Имя Отчество *',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_fio', 'readonly': 'readonly'}))
    Address_reg = forms.CharField(label=u'Адрес прописки *',
                                  widget=forms.widgets.TextInput(attrs={'id': 'id_Address_reg'}))
    INN = forms.CharField(label=u'ИНН *',
                          widget=forms.widgets.TextInput(attrs={'id': 'id_inn', 'readonly': 'readonly'}))
    OGRN = forms.CharField(required=False, label=u'ОГРН',
                           widget=forms.widgets.TextInput(attrs={'id': 'id_ogrn', 'readonly': 'readonly'}))
    OKVED = forms.CharField(required=False, label=u'ОКВЭД',
                            widget=forms.widgets.TextInput(attrs={'id': 'id_okved'}))
    PassportSerNum = forms.CharField(required=False, label=u'Серия и номер паспорта',
                                     widget=forms.widgets.TextInput(attrs={'class': 'passportsernum'}))
    DatePassport = forms.DateField(required=False, label=u'Дата выдачи', input_formats=('%Y-%m-%d',),
                                   widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    IssuedByPassport = forms.CharField(required=False, label=u'Кем выдан паспорт',
                                       widget=forms.widgets.TextInput(attrs={'id': 'id_bypass'}))
    Address_email = forms.CharField(required=False, label=u'Адрес эл.почты',
                                    widget=forms.widgets.EmailInput(attrs={'id': 'id_addressemail'}))
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Phone_city = forms.CharField(required=False, label=u'Стационарный тел.',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(required=False, label=u'Мобильный тел.',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_fax = forms.CharField(required=False, label=u'Факс',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_sms = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    EDO = forms.BooleanField(required=False, label='ЭДО', widget=forms.CheckboxInput())

    def clean(self):
        cleaned_data = super(client_form_businessman, self).clean()
        nameclient = cleaned_data['NameClient_full']
        addressreg = cleaned_data['Address_reg']

        if not self.errors:
            # Прооверка ФИО
            lastname = nameclient.split(' ')[0]
            if len(lastname) < 3:
                raise ValidationError(u'"Фамилия" не может быть менее трёх букв')

            firstname = nameclient.split(' ')[1]
            if len(firstname) < 3:
                raise ValidationError(u'"Имя" не может быть менее трёх букв')

            if len(addressreg) < 10:
                raise ValidationError(u'Адрес прописки не может быть менее 10 символов')

        return cleaned_data


# ------------------------------------------------------------------------------------------------------------------

class client_form_physicalperson(Form):
    NameClient_full = forms.CharField(label=u'Фамилия Имя Отчество *',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_fio', 'readonly': 'readonly'}))
    Alien = forms.BooleanField(required=False, label='Не является гражданином Российской Федерации',
                               widget=forms.CheckboxInput(attrs={'disabled': "disabled"}))
    Address_reg = forms.CharField(label=u'Адрес прописки *',
                                  widget=forms.widgets.TextInput(attrs={'id': '#id_Address_reg'}))
    PassportSerNum = forms.CharField(label=u'Серия и номер паспорта *',
                                     widget=forms.widgets.TextInput(
                                         attrs={'readonly': 'readonly'}))    #'class': 'passportsernum',
    DatePassport = forms.DateField(label=u'Дата выдачи *', input_formats=('%Y-%m-%d',),
                                   widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    IssuedByPassport = forms.CharField(label=u'Кем выдан паспорт *',
                                       widget=forms.widgets.TextInput(attrs={'id': 'id_bypass'}))
    Address_email = forms.CharField(required=False, label=u'Адрес эл.почты',
                                    widget=forms.widgets.EmailInput(attrs={'id': 'id_addressemail'}))
    INN = forms.CharField(required=False, label=u'ИНН',
                          widget=forms.widgets.TextInput(attrs={'class': 'inn_businessman'}))
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Phone_city = forms.CharField(required=False, label=u'Стационарный тел.',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(label=u'Мобильный тел. *',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_sms = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    EDO = forms.BooleanField(required=False, label='ЭДО', widget=forms.CheckboxInput())

    def clean(self):
        cleaned_data = super(client_form_physicalperson, self).clean()
        nameclient = cleaned_data['NameClient_full']

        if not self.errors:
            # Прооверка ФИО
            lastname = nameclient.split(' ')[0]
            if len(lastname) < 3:
                raise ValidationError(u'"Фамилия" не может быть менее трёх букв')

            firstname = nameclient.split(' ')[1]
            if len(firstname) < 3:
                raise ValidationError(u'"Имя" не может быть менее трёх букв')

            # surname = nameclient.split(' ')[2]
            # if len(surname) < 5:
            #     raise ValidationError(u'"Отчество" не может быть менее пяти букв')

            if len(cleaned_data['Address_reg']) < 10:
                raise ValidationError(u'"Адрес прописки" не может быть менее 10 символов')

            if len(cleaned_data['IssuedByPassport']) < 10:
                raise ValidationError(u'"Кем выдан паспорт" не может быть менее 10 символов')

        return cleaned_data


# ------------------------------------------------------------------------------------------------------------------
#                             Изменение данных контрагента
# ------------------------------------------------------------------------------------------------------------------

class ClientCompanyUpdateForm(ModelForm):
    class Meta:
        model = Client
        fields = ['INN', 'OGRN']


class BranchCompanyUpdateForm(ModelForm):
    NameBranch = forms.CharField(required=False, label=u'Наименование филиала', widget=forms.widgets.TextInput())
    Management_post = forms.ModelChoiceField(label=u'Должность руководителя *', queryset=ListPosts.objects.all(),
                                             widget=forms.Select(attrs={'id': 'id_managerpost'}))
    Management_name = forms.CharField(required=False, label=u'ФИО руководителя', help_text='ФИО в именительном падеже',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_Management_name'}))
    Management_data = forms.CharField(label=u'В лице', widget=forms.widgets.Textarea(attrs={'rows': 2   }))
    PowersOffice_name = forms.ModelChoiceField(required=False, label=u'Действует на основании',
                                               queryset=PowersOfficeActs.objects.all(), widget=forms.Select())
    PowersOffice_number = forms.CharField(required=False, label=u'Номер документа основания',
                                          widget=forms.widgets.TextInput(attrs={'id': 'id_Management_name'}))
    PowersOffice_date = forms.DateField(required=False, label=u'Срок действия доверенности', input_formats=('%Y-%m-%d',),
                                        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    Address_reg = forms.CharField(required=False, label=u'Юридический адрес',
                                  widget=forms.widgets.TextInput(attrs={'class': 'id_Address_reg'}))
    Address_post = forms.CharField(required=False, label=u'Почтовый адрес',
                                   widget=forms.widgets.TextInput(attrs={'class': 'id_Address_post'}))
    Address_email = forms.CharField(required=False, label=u'Адрес эл.почты',
                                    widget=forms.widgets.EmailInput(attrs={'class': 'id_addressemail'}))
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Bank_Details = forms.CharField(label=u'Подробно', widget=forms.widgets.Textarea(attrs={'rows': 2}))
    Phone_city = forms.CharField(required=False, label=u'Стационарный тел.',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(required=False, label=u'Мобильный тел.',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_fax = forms.CharField(required=False, label=u'Факс',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_sms = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    EDO = forms.BooleanField(required=False, label='ЭДО', widget=forms.CheckboxInput())
    Accruals_roundoff = forms.BooleanField(required=False, label='Округлять копейки', widget=forms.CheckboxInput())

    class Meta:
        model = Branch
        fields = ['NameBranch', 'Management_post', 'Management_name', 'Management_data', 'KPP',
                  'PowersOffice_name', 'PowersOffice_number', 'PowersOffice_date',
                  'Address_reg', 'Address_post', 'Address_email',
                  'Bank_BIK', 'Bank_RaschetSchet', 'Bank_Details',
                  'Phone_city', 'Phone_mobile', 'Phone_fax', 'Phone_SMS', 'EDO', 'Accruals_roundoff']


class ClientBusinessmanUpdateForm(ModelForm):
    NameClient_full = forms.CharField(label=u'Фамилия Имя Отчество',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_fio'}))
    Address_reg = forms.CharField(label=u'Адрес прописки',
                                  widget=forms.widgets.TextInput(attrs={'id': 'id_Address_reg'}))
    INN = forms.CharField(required=False, label=u'ИНН',
                          widget=forms.widgets.TextInput(attrs={'class': 'inn_businessman'}))
    PassportSerNum = forms.CharField(label=u'Серия и номер паспорта',
                                     widget=forms.widgets.TextInput(attrs={'class': 'passportsernum'}))
    DatePassport = forms.DateField(label=u'Дата выдачи', input_formats=('%Y-%m-%d',),
                                   widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    IssuedByPassport = forms.CharField(label=u'Кем выдан паспорт',
                                       widget=forms.widgets.TextInput(attrs={'id': 'id_bypass'}))

    class Meta:
        model = Client
        fields = ['NameClient_full', 'Alien', 'Address_reg',
                  'INN', 'OGRN', 'PassportSerNum', 'DatePassport', 'IssuedByPassport']


class BranchBusinessmanUpdateForm(ModelForm):
    Address_post = forms.CharField(label=u'Почтовый адрес',
                                   widget=forms.widgets.TextInput(attrs={'id': 'id_Address_post'}))
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Bank_Details = forms.CharField(label=u'Подробно', widget=forms.widgets.Textarea(attrs={'rows': 2}))
    Phone_city = forms.CharField(required=False, label=u'Стационарный тел.',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(label=u'Мобильный тел.',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_SMS = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))

    class Meta:
        model = Branch
        fields = ['Address_post', 'Address_email', 'Bank_BIK', 'Bank_RaschetSchet', 'Bank_Details',
                  'Phone_city', 'Phone_mobile', 'Phone_fax', 'Phone_SMS', 'EDO', 'Accruals_roundoff']


class ClientPhysicalPersonUpdateForm(ModelForm):
    NameClient_full = forms.CharField(label=u'Фамилия Имя Отчество',
                                      widget=forms.widgets.TextInput(attrs={'id': 'id_fio'}))
    Address_reg = forms.CharField(label=u'Адрес прописки',
                                  widget=forms.widgets.TextInput(attrs={'id': 'id_Address_reg'}))
    INN = forms.CharField(required=False, label=u'ИНН',
                          widget=forms.widgets.TextInput(attrs={'class': 'inn_businessman'}))
    PassportSerNum = forms.CharField(label=u'Серия и номер паспорта',
                                     widget=forms.widgets.TextInput(attrs={'class': 'passportsernum'}))
    DatePassport = forms.DateField(label=u'Дата выдачи', input_formats=('%Y-%m-%d',),
                                   widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    IssuedByPassport = forms.CharField(label=u'Кем выдан паспорт',
                                       widget=forms.widgets.TextInput(attrs={'id': 'id_bypass'}))

    class Meta:
        model = Client
        fields = ['NameClient_full', 'Alien', 'Address_reg', 'INN',
                  'PassportSerNum', 'DatePassport', 'IssuedByPassport']


class BranchPhysicalPersonUpdateForm(ModelForm):
    Bank_BIK = forms.CharField(required=False, label=u'БИК банка',
                               widget=forms.widgets.TextInput(attrs={'class': 'bank_bik'}))
    Bank_RaschetSchet = forms.CharField(required=False, label=u'Расчетный счёт',
                                        widget=forms.widgets.TextInput(attrs={'class': 'bank_rs'}))
    Bank_Details = forms.CharField(label=u'Подробно', widget=forms.widgets.Textarea(attrs={'rows': 2}))
    Phone_city = forms.CharField(required=False, label=u'Стационарный тел.',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_mobile = forms.CharField(label=u'Мобильный тел.',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_SMS = forms.CharField(required=False, label=u'SMS тел.',
                                widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))

    class Meta:
        model = Branch
        fields = ['Address_email', 'Bank_BIK',  'Bank_RaschetSchet', 'Bank_Details',
                  'Phone_city', 'Phone_mobile', 'Phone_SMS', 'EDO', 'Accruals_roundoff']


# ------------------------------------------------------------------------------------------------------------------
class contact_form(ModelForm):

    def __init__(self, *args, **kwargs):
        super(contact_form, self).__init__(*args, **kwargs)
        self.fields['Person_post'].required = False

    Person_FIO = forms.CharField(label=u'ФИО', widget=forms.widgets.TextInput(attrs={'alt': 'fio'}))
    Phone_mobile = forms.CharField(required=False, label=u'(ХХХ) ХХХ-ХХХХ',
                                   widget=forms.widgets.TextInput(attrs={'class': 'phone_mobile'}))
    Phone_city = forms.CharField(required=False, label=u'(ХХХХ) ХХ-ХХХХ',
                                 widget=forms.widgets.TextInput(attrs={'class': 'phone_stat'}))
    Phone_city_extra = forms.CharField(required=False, label=u'ХХХХХ',
                                       widget=forms.widgets.TextInput(attrs={'class': 'phone_stat_extra'}))

    class Meta:
        model = Contacts
        fields = ['Person_FIO', 'Person_post', 'Phone_mobile', 'Phone_city', 'Phone_city_extra', 'Email']


ContactsFormSet = modelformset_factory(Contacts, form=contact_form, extra=1)
# ------------------------------------------------------------------------------------------------------------------


class usernote_form(ModelForm):

    class Meta:
        model = UserNote
        fields = ['Title', 'Note']


# ------------------------------------------------------------------------------------------------------------------
class form_additional_info(ModelForm):
    Additional_info = forms.CharField(required=False, label=u'Дополнительная информация',
                                      widget=forms.widgets.Textarea(attrs={'rows': 2}))

    class Meta:
        model = Branch
        fields = ['Additional_info']


class load_scan_form(ModelForm):
    class Meta:
        model = ScannedDocuments
        fields = ['NameDocument', 'Branch', 'TypeDocument', 'ScanPath']


class search_form(forms.Form):
    search_text = forms.CharField(required=False, label='объект поиска',
                                  widget=forms.widgets.TextInput(attrs={'id': 'q', 'placeholder': 'Поиск...'}))
    field_search = forms.ChoiceField(required=False, label=u'Поиск по... ', choices=[
        ["all", "везде"],
        ["name_client", "по наименованию контрагента"],
        ["name_object", "по наименованию объекта"],
        ["address_object", "по адресу объекта"],
        ["inn", "по наименованию объекта"]
    ])


class search_filter_form(forms.Form):
    active = forms.BooleanField(required=False, label='активные объекты')


# class advanced_search_form(forms.Form):
#     client = forms.CharField(required=False, label='Контрагент', widget=forms.widgets.TextInput)
#     inn = forms.CharField(required=False, label='ИНН', widget=forms.widgets.TextInput)
#     contract = forms.CharField(required=False, label='Договор', widget=forms.widgets.TextInput)
#     num_object = forms.CharField(required=False, label='Номер объекта', widget=forms.widgets.TextInput)
#     adr_object = forms.CharField(required=False, label='Адрес объекта', widget=forms.widgets.TextInput)
#
#     def clean(self):
#         cleaned_data = super(advanced_search_form, self).clean()
#         inn = cleaned_data['inn']
#
#         if not self.errors:
#             if inn != '':
#                 if re.match(r"^[0-9]{10,12}$", inn) is None:
#                     raise ValidationError(u'ИНН юридических лиц - 10 цифр, физических лиц (ИП в том числе) - 12 цифр')
#
#         return cleaned_data


class get_forchange_scompany(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания", queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(get_forchange_scompany, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['scompany'].queryset = ServingCompanyBranch.objects.all()
