from datetime import datetime, timedelta, date
from django import forms
from django.forms import modelformset_factory

from accounting.models import credited_with_paid
from base.models import ServingCompanyBranch, SystemConstant, alldocuments_fulldata, ServingCompany
from base.views import get_scompany_foruser
from reference_books.models import PaymentMethods, TypeDocument, City
from tech_security.models import TechSecurityObject, TechSecurityContract


__author__ = 'bondarenkoav'


class form_payment(forms.Form):

    def __init__(self, *args, **kwargs):
        self.branch_id = kwargs.pop('branch_id', None)
        self.scompany_id = kwargs.pop('scompany_id', None)
        self.session_paymethods = kwargs.pop('session_paymethods', None)
        self.session_dateevent = kwargs.pop('session_dateevent', None)
        super(form_payment, self).__init__(*args, **kwargs)

        branch_documents = alldocuments_fulldata.objects.filter(ServingCompany_id=self.scompany_id,
                                                                Branch_id=self.branch_id)
        self.fields['document'].queryset = branch_documents
        if branch_documents.count() == 1:
            self.fields['document'].initial = branch_documents.first().id
        if self.session_paymethods:
            self.fields['paymethods'].initial = self.session_paymethods
        if self.session_dateevent:
            self.fields['date_event'].initial = datetime.strptime(self.session_dateevent, "%Y-%m-%d")
        else:
            self.fields['date_event'].initial = datetime.today()

    summ = forms.CharField(label='Сумма')
    document = forms.ModelChoiceField(required=False, label="Документ", queryset=alldocuments_fulldata.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    date_event = forms.DateTimeField(label='Дата', input_formats=('%Y-%m-%d',),
                                     widget=forms.DateInput(format='%Y-%m-%d',
                                                            attrs={'type': 'date', 'style': 'height: 44px;'}))
    paymethods = forms.ModelChoiceField(label="Форма оплаты", queryset=PaymentMethods.objects.all(),
                                        widget=forms.Select(attrs={'class': 'selector'}))

    def clean(self):
        cleaned_data = self.cleaned_data
        date_event = cleaned_data['date_event']

        if not self.errors:
            date_startsaldo = SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue
            if date_event.date() > datetime.now().date() or date_event.date() < datetime.strptime(date_startsaldo, "%d.%m.%Y").date():
                # pass
                # self.data["date_event"] = datetime.now()
                self.cleaned_data['date_event'] = datetime.now()
        return cleaned_data


class form_addaccural(forms.Form):
    def __init__(self, *args, **kwargs):
        self.branch_id = kwargs.pop('branch_id', None)
        self.scompany_id = kwargs.pop('scompany_id', None)
        super(form_addaccural, self).__init__(*args, **kwargs)

        branch_contracts = TechSecurityContract.objects.filter(ServingCompany_id=self.scompany_id,
                                                               Branch_id=self.branch_id)
        self.fields['objects'].queryset = TechSecurityObject.objects.filter(
            TechSecurityContract__in=branch_contracts)
            # StatusSecurity=StatusSecurity.objects.get(slug='active'))

    date_event = forms.DateTimeField(label='Дата', input_formats=('%Y-%m-%d',),
                                     widget=forms.DateInput(format='%Y-%m-%d',
                                                            attrs={'type': 'date', 'style': 'height: 44px;'}))
    objects = forms.ModelChoiceField(label="Объект", queryset=TechSecurityObject.objects.all(),
                                     widget=forms.Select(attrs={'class': 'selector'}))
    summ = forms.CharField(label='Сумма',
                           widget=forms.widgets.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'max': '999999'}))


class accrual_for_period_form(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(accrual_for_period_form, self).__init__(*args, **kwargs)
        # self.fields['scompany'] = Profile.objects.filter(user=self.user).values('scompany')

    scompany = forms.ModelChoiceField(label="Сервисная компания", queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    date_start = forms.DateField(label='Дата начала', input_formats=('%Y-%m-%d',),
                                 initial=date(datetime.today().year, datetime.today().month, 1),
                                 widget=forms.DateInput(format='%Y-%m-%d',
                                                        attrs={'type': 'date', 'style': 'height: 44px;'}))
    date_end = forms.DateField(label='Дата окончания', initial=datetime.today(),
                               widget=forms.DateInput(format='%Y-%m-%d',
                                                      attrs={'type': 'date', 'style': 'height: 44px;'}))
    type_dct = forms.ModelChoiceField(required=False, label="Тип документа", queryset=TypeDocument.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))

    def clean(self):
        cleaned_data = self.cleaned_data
        date_start = cleaned_data['date_start']
        date_end = cleaned_data['date_end']

        if not self.errors:
            if date_start > date_end:
                raise forms.ValidationError(u'Введите правильно даты')

        return cleaned_data


class form_act_reconciliation(forms.Form):

    def __init__(self, *args, **kwargs):
        self.branch_id = kwargs.pop('branch_id', None)
        self.scompany_id = kwargs.pop('scompany_id', None)
        super(form_act_reconciliation, self).__init__(*args, **kwargs)

        self.start_saldo = datetime.strptime(SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue,
                                             '%d.%m.%Y')

        branch_documents = alldocuments_fulldata.objects.filter(ServingCompany_id=self.scompany_id, Branch_id=self.branch_id)
        self.fields['document'].queryset = branch_documents
        if branch_documents.count() == 1:
            self.fields['document'].initial = branch_documents.first().id

        if datetime.today().year == self.start_saldo.year:
            self.fields['date_start'].initial = self.start_saldo
            self.fields['date_start'].help_text = u'Дата начала периода в акте сверки не может быть ранее этой даты'
        else:
            self.fields['date_start'].initial = date(datetime.today().year, 1, 1)

    date_start = forms.DateField(label='Дата начала', input_formats=('%Y-%m-%d',),
                                 widget=forms.DateInput(format='%Y-%m-%d',
                                                        attrs={'type': 'date', 'style': 'height: 44px;'}))
    date_end = forms.DateField(label='Дата окончания', initial=datetime.today(), input_formats=('%Y-%m-%d',),
                               widget=forms.DateInput(format='%Y-%m-%d',
                                                      attrs={'type': 'date', 'style': 'height: 44px;'}))
    document = forms.ModelChoiceField(required=False, label="Документ", queryset=alldocuments_fulldata.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}),
                                      help_text=u'Выбор документа не обязателен')

    def clean(self):
        cleaned_data = self.cleaned_data
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')

        if not self.errors:
            if date_start >= date_end:
                raise forms.ValidationError(u'Правильно введите даты')
            else:
                if self.start_saldo.date() > date_start:
                    forms.ValidationError(
                        u'Дата начала периода в акте сверки не может быть ранее %s' % self.start_saldo)
        return cleaned_data


class form_startbalance(forms.Form):
    summ = forms.CharField(label='Сумма', widget=forms.widgets.NumberInput(attrs={'step': 0.01}))   # 'min': -999999.0, 'max': 999999

    def clean(self):
        cleaned_data = self.cleaned_data
        summ = cleaned_data['summ']

        if summ is None:
            self._errors['summ'] = self.error_class('Поле "сумма" не может быть пустым')

        return cleaned_data


AccuralsModelFormset = modelformset_factory(
    credited_with_paid,
    fields='__all__',
    exclude=('branch', 'scompany', 'dct', 'DateTime_add', 'DateTime_update', 'Create_user', 'Update_user'),
    extra=0,
    widgets={}
)


class form_payment_change(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(form_payment_change, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['summ'].initial = abs(instance.summ)

    class Meta:
        model = credited_with_paid
        fields = ['summ']


class forms_payment_out_date(forms.Form):
    scompany = forms.ModelChoiceField(label=u'Сервисная компания',
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    paymentmethods = forms.ModelChoiceField(required=False, label=u'Способ оплаты',
                                            queryset=PaymentMethods.objects.all(),
                                            widget=forms.Select(attrs={'class': 'selector'}))
    filter_start_date = forms.DateField(required=True, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                        initial=datetime.today() - timedelta(days=1),
                                        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    filter_end_date = forms.DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                      widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))


class arrears_form(forms.Form):
    def __init__(self, *args, **kwargs):
        super(arrears_form, self).__init__(*args, **kwargs)
        self.fields['scompany'].queryset = get_scompany_foruser()

    count_months = forms.CharField(label='Количество месяцев просрочки', initial=3,
                                   widget=forms.widgets.NumberInput(attrs={'size': '2', 'min': '2', 'max': '5'}),
                                   help_text=u'месяцев просрочки')
    scompany = forms.ModelChoiceField(label=u'Сервисная компания', queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    status = forms.ChoiceField(label=u'Статус', choices=(('active', 'действующие'), ('passive', 'снятые')),
                               widget=forms.Select(), initial='active')

    def clean(self):
        cleaned_data = self.cleaned_data
        count_months = cleaned_data['count_months']

        if not self.errors:
            if int(count_months) not in range(1, 6):
                raise forms.ValidationError(u'Количество месяцев просрочки от 1 до 5')

        return cleaned_data


CHOICES_MONTHS = (
    (1, u'Январь'),
    (2, u'Февраль'),
    (3, u'Март'),
    (4, u'Апрель'),
    (5, u'Май'),
    (6, u'Июнь'),
    (7, u'Июль'),
    (8, u'Август'),
    (9, u'Сентябрь'),
    (10, u'Октябрь'),
    (11, u'Ноябрь'),
    (12, u'Декабрь'),
)


class forms_turnover_statement(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(forms_turnover_statement, self).__init__(*args, **kwargs)

    scompany = forms.ModelChoiceField(required=False, label=u'Сервисная компания',
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    filter_month = forms.ChoiceField(label=u'Месяц',
                                     choices=CHOICES_MONTHS, initial=datetime.today().month,
                                     widget=forms.Select())
    filter_year = forms.CharField(label=u'Год', initial=datetime.today().year, min_length=4, max_length=4,
                                  widget=forms.NumberInput())

    def clean(self):
        cleaned_data = self.cleaned_data
        filter_year = cleaned_data['filter_year']
        self.start_saldo = datetime.strptime(SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue, '%d.%m.%Y')
        next_year = datetime.today() + timedelta(days=365)

        if not self.errors:
            if int(filter_year) not in range(self.start_saldo.year, next_year.year):
                raise forms.ValidationError(u'Данный год не доступен')
        return cleaned_data


class forms_turnover_statement_forunits(forms.Form):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(forms_turnover_statement_forunits, self).__init__(*args, **kwargs)

    scompany = forms.ModelChoiceField(required=False, label=u'Сервисная компания',
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    city = forms.ModelChoiceField(required=False, label=u'Населенный пункт',
                                  queryset=City.objects.all(),
                                  widget=forms.Select(attrs={'class': 'selector'}))
    filter_month = forms.ChoiceField(label=u'Месяц',
                                     choices=CHOICES_MONTHS, initial=datetime.today().month,
                                     widget=forms.Select())
    filter_year = forms.CharField(label=u'Год', initial=datetime.today().year, min_length=4, max_length=4,
                                  widget=forms.NumberInput())
    filter_accrual = forms.ChoiceField(label=u'Начислено', widget=forms.Select(), initial='yes',
                                       choices=(('all', 'начисление - не важно'), ('yes', 'начисление - да')),)

    def clean(self):
        cleaned_data = self.cleaned_data
        filter_year = cleaned_data['filter_year']
        self.start_saldo = datetime.strptime(SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue, '%d.%m.%Y')
        next_year = datetime.today() + timedelta(days=365)

        if not self.errors:
            if int(filter_year) not in range(self.start_saldo.year, next_year.year):
                raise forms.ValidationError(u'Данный год не доступен')
        return cleaned_data


class forms_export_to1S_objects_action(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания", queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    edo = forms.BooleanField(required=False, initial=False, label='ЭДО')
    paymentAfter = forms.BooleanField(required=False, initial=False, label='Постоплата')


class forms_import_from1C_bankpayments(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompany.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    date_payments = forms.DateField(required=False, label=u'Дата ', input_formats=('%Y-%m-%d',),
                                    widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))


class forms_smssend_debtors(forms.Form):
    scompany = forms.ModelChoiceField(label="Сервисная компания",
                                      queryset=ServingCompanyBranch.objects.all(),
                                      widget=forms.Select(attrs={'class': 'selector'}))
    ct_months = forms.ChoiceField(label="Кол-во месяцев просрочки",
                                  widget=forms.Select(), choices=([(1, '1'), (2, '2'), (3, '3'), ]), initial='3')
