import datetime

from django.forms import DateField, DateInput, ModelChoiceField
from django import forms

from base.views import get_scompany_foruser
from base.models import ServingCompanyBranch, SectionsApp, Event
from reference_books.models import TypeDocument, City

__author__ = 'bondarenkoav'


class form_term_contracts(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    typedoc = forms.ModelChoiceField(label="Тип документ",
                                     queryset=TypeDocument.objects.filter(type='contract'),
                                     widget=forms.Select(attrs={'class': 'selector'}))


class form_acts_period(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    filter_start_date = DateField(required=True, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                  initial=datetime.timedelta(days=-1),
                                  widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    filter_end_date = DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))


class form_maintenance_listObjects(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    city = forms.ModelChoiceField(label="Населённый пункт", queryset=City.objects.all(),
                                  widget=forms.Select(attrs={'class': 'selector'}), required=False)
    sortby_column = forms.ChoiceField(required=False, label=u'Сортировка ', choices=[
        ["name", "по наименованию"],
        ["city", "по населенному пункту"],
        ["date_end", "по дате окончания"]
    ])


class form_assembly_production(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    filter_month = forms.DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                   widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
                                   help_text=u'Выберите любой день нужного месяца')


class forms_events_period(forms.Form):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(forms_events_period, self).__init__(*args, **kwargs)
        self.fields['filter_scompany'].queryset = get_scompany_foruser()

    filter_app = forms.ModelMultipleChoiceField(required=True, label="Разделы",
                                                queryset=SectionsApp.objects.filter(choice=True).order_by('id'),
                                                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check mr-1',
                                                                                           'checked': 'checked',
                                                                                           'onchange': 'checkboxes()'}))
    filter_start_date = DateField(required=True, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                  initial=datetime.timedelta(days=-1),
                                  widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    filter_end_date = DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    filter_typeevent = ModelChoiceField(required=False, label="Событие", queryset=Event.objects.filter(forfilter=True),
                                        widget=forms.Select(attrs={'class': 'selector'}))
    filter_scompany = forms.ModelChoiceField(label=u'Сервисная компания', queryset=ServingCompanyBranch.objects.all(),
                                             widget=forms.Select(attrs={'class': 'selector'}))


class form_quarterly_to_police(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания", queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))


class form_weekly_to_police(forms.Form):
    scompany = ModelChoiceField(label="Сервисная компания", queryset=ServingCompanyBranch.objects.all(),
                                widget=forms.Select(attrs={'class': 'selector'}))
    date_start = DateField(label='Дата начала', initial=(datetime.date.today() - datetime.timedelta(6)),
                           input_formats=('%Y-%m-%d',),
                           widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    date_end = DateField(label='Дата окончания', initial=datetime.date.today(),
                         input_formats=('%Y-%m-%d',), widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    def clean(self):
        cleaned_data = self.cleaned_data
        date_start = cleaned_data['date_start']
        date_end = cleaned_data['date_end']

        if not self.errors:
            if date_start > date_end:
                raise forms.ValidationError(u'Введите в хронологическом порядке')


# class forms_contracts_maintenance(forms.Form):
#
#     scompany = forms.ModelChoiceField(required=False, label=u'Сервисная компания',
#                                       queryset=ServingCompanyBranch.objects.all(),
#                                       widget=forms.Select(attrs={'class': 'selector'}))
#     filter_month = forms.ChoiceField(label=u'Месяц', choices=CHOICES_MONTHS, initial=datetime.datetime.today().month,
#                                      widget=forms.Select())
