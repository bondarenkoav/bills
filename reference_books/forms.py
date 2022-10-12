from django import forms
from django.forms import ModelForm, widgets
from base.models import ServingCompany, GroupClient, CoWorkers, ServingCompanyBranch
from reference_books.models import ListPosts, ListEquipment, TypeObject, TypeWork

__author__ = 'bondarenkoav'


class group_form(ModelForm):
    Address_residence = forms.CharField(required=False, label=u'Адрес нахождения',
                                        widget=forms.widgets.TextInput(attrs={'id': 'id_addressreg'}))

    class Meta:
        model = GroupClient
        fields = ['NameGroupClient', 'Founder_FIO', 'Address_residence', 'Phone_mobile', 'Phone_city', 'Phone_fax',
                  'Address_email']


class scompany_form(ModelForm):
    class Meta:
        model = ServingCompany
        fields = ['OKOPF', 'NameCompany_full', 'NameCompany_short', 'Management_post', 'Management_name',
                  'Address_reg', 'INN', 'OGRN', 'OKPO', 'OKVED']


class scompany_branch_form(ModelForm):
    Bank_Details = forms.CharField(label='Реквизиты банка',
                                   widget=forms.widgets.Textarea(attrs={'rows': 3, 'readonly': 'readonly'}))

    class Meta:
        model = ServingCompanyBranch
        fields = ['ServingCompany', 'NameBranch', 'City',
                  'Management_post', 'Management_name',
                  'PowersOffice_name', 'PowersOffice_number',
                  'Address_post', 'Address_email', 'KPP',
                  'Phone_city', 'Phone_fax', 'Phone_mobile',
                  'Bank_BIK', 'Bank_Details', 'Bank_RaschetSchet']


class post_form(ModelForm):
    class Meta:
        model = ListPosts
        fields = ['NamePost', 'PrefixPost', 'PostfixPost']


class equipment_form(ModelForm):
    class Meta:
        model = ListEquipment
        fields = ['Name']


class typesobject_form(ModelForm):
    class Meta:
        model = TypeObject
        fields = ['ShortName', 'DescName']


class typeswork_form(ModelForm):
    class Meta:
        model = TypeWork
        fields = ['Name']


class coworker_form(ModelForm):
    Person_FIO = forms.CharField(required=False, label=u'Фамилия Имя Отчество',
                                 widget=forms.widgets.TextInput(attrs={'id': 'id_fio'}))

    class Meta:
        model = CoWorkers
        fields = ['Person_FIO', 'ListPosts', 'ServingCompanyBranch']
