import datetime
import locale
import random
import sys

from datetime import date
from itertools import chain

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, FloatField, Q
from django.shortcuts import render, redirect
from django.template import Template, Context
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from excel_response import ExcelResponse
from uuslug import slugify

from accounting.forms import arrears_form, forms_turnover_statement, form_act_reconciliation, \
    form_startbalance, forms_payment_out_date, forms_export_to1S_objects_action, accrual_for_period_form, \
    forms_smssend_debtors, form_payment, form_addaccural, AccuralsModelFormset, form_payment_change, \
    forms_import_from1C_bankpayments, forms_turnover_statement_forunits
from accounting.models import credited_with_paid, AccountingTemplates, temp_export_object_to1S_client, start_balance, \
    saldobranch, saldotoday, temp_export_bankpayments_from1C
from base.models import ServingCompanyBranch, Branch, SystemConstant, ServingCompany, alldocuments_fulldata, allobjects
from base.numtostring import decimal2text
from base.templatetags.other_tags import get_nameclient
from base.views import logging_event
from contract_department.models import allactive_securityobjects, clients_active_securityobjects
from maintenance_service.models import MaintenanceServiceContract, MaintenanceServiceObject
from reference_books.models import TypeDocument, PaymentMethods
from tech_security.models import TechSecurityContract, TechSecurityObject


# Округление копеек
def roundoff_accruals(branch_id, summ):
    if Branch.objects.get(id=branch_id).Accruals_roundoff:
        return round(summ)  # Округление до целого
    else:
        return round(summ, 2)  # Округление до сотых рубля


# Начальное сальдо по контрагенту и сервисной компании
def balance_start(branch_id, scompany_id):
    initial_balance = start_balance.objects.filter(branch=branch_id, scompany=scompany_id).aggregate(saldo=Sum('summ'),
                                                                                                     output_field=FloatField())
    if initial_balance:
        return initial_balance.saldo
    else:
        return 0


# Общее сальдо по контрагенту и сервисной компании
def balance_final(branch_id, scompany_id):
    balance = credited_with_paid.objects.filter(branch=branch_id, scompany=scompany_id).aggregate(saldo=Sum('summ'),
                                                                                                  output_field=FloatField())
    return balance_start(branch_id, scompany_id) + balance.saldo


# Общее сальдо по контрагенту и сервисной компании за 1 год
def balance_year(branch_id, scompany_id, year_event):
    return credited_with_paid.objects.filter(branch=branch_id, scompany=scompany_id,
                                             date_event__year=year_event).aggregate(saldo=Sum('summ'),
                                                                                    output_field=FloatField())


# Общее сальдо по контрагенту и сервисной компании
def balance_dct(branch_id, scompany_id, dct_id, type_dct_id):
    return credited_with_paid.objects.filter(branch=branch_id, scompany=scompany_id, type_dct=type_dct_id,
                                             dct=dct_id).aggregate(saldo=Sum('summ'), output_field=FloatField())


# Удаление платежа
def dlt_payment(payment, **kwargs):
    payment_id = kwargs['payment_id']
    paid = credited_with_paid.objects.get(id=payment_id)
    try:
        paid.delete()
        logging_event('delete_payment', None, paid.summ, paid.type_dct.app, 'system', paid.type_dct, paid.scompany,
                      paid.branch, paid.dct)
        return redirect('finance_department:payment', branch_id=paid.branch.id, scompany_id=paid.scompany.id)
    except:
        return redirect('finance_department:payment', branch_id=paid.branch.id, scompany_id=paid.scompany.id)


# Удаление возврата
def dlt_payment(payment, **kwargs):
    payment_id = kwargs['payment_id']
    paid = credited_with_paid.objects.get(id=payment_id)
    try:
        paid.delete()
        logging_event('delete_payment', None, paid.summ, paid.type_dct.app, 'system', paid.type_dct, paid.scompany,
                      paid.branch, paid.dct)
        return redirect('finance_department:payment', branch_id=paid.branch.id, scompany_id=paid.scompany.id)
    except:
        return redirect('finance_department:payment', branch_id=paid.branch.id, scompany_id=paid.scompany.id)


# Удаление начисления
def dlt_accural(accural, **kwargs):
    accural_id = kwargs['accural_id']
    accural_data = credited_with_paid.objects.get(id=accural_id)
    try:
        accural_data.delete()
        logging_event('delete_accural', None, accural_data.summ, accural_data.type_dct.app, 'system',
                      accural_data.type_dct, accural_data.scompany, accural_data.branch, accural_data.dct)
        return redirect('finance_department:payment', branch_id=accural_data.branch.id,
                        scompany_id=accural_data.scompany.id)
    except:
        return redirect('finance_department:payment', branch_id=accural_data.branch.id,
                        scompany_id=accural_data.scompany.id)


# Вывод начислений на дату по договору или акту
def view_accurals(request, branch_id, scompany_id, dct, date_event):
    event_date = datetime.datetime.strptime(date_event, '%Y%m%d')
    accurals = credited_with_paid.objects.filter(branch=Branch.objects.get(id=branch_id),
                                                 scompany=ServingCompanyBranch.objects.get(id=scompany_id))
    # if request.GET:
    formset = AccuralsModelFormset(queryset=accurals.filter(dct=dct, summ__gt=0, date_event=event_date))

    if request.POST:
        formset = AccuralsModelFormset(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('summ'):
                    accural = accurals.get(id=form.instance.id)
                    new_accural = form.save(commit=False)
                    new_accural.type_dct = accural.type_dct
                    new_accural.date_event = accural.date_event
                    new_accural.Create_user = accural.Create_user
                    new_accural.Update_user = request.user
                    new_accural.save()
            return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)

    return render(request, 'view_accurals.html', {
        'formset': formset,
        'branch_id': branch_id,
        'scompany_id': scompany_id,
        'document': dct,
        'date_event': event_date,
        'title': "Начисления на дату %s" % event_date.date().strftime("%d.%m.%Y"),
        'title_area': "Сальдовая ведомость",
        'title_small': Branch.objects.get(id=branch_id).Client.NameClient_short,
    })


# Вывод оплаты на дату
def view_payment(request, branch_id, scompany_id, payment_id):
    form = form_payment_change(request.POST or None,
                               instance=payment_id and credited_with_paid.objects.get(id=payment_id))

    if request.POST:
        if form.is_valid():
            new_payment = form.save(commit=False)
            if form.cleaned_data['summ'] > 0:
                new_payment.summ = form.cleaned_data['summ'] * (-1)
            new_payment.save()

            return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)
        else:
            return render(request, 'accounting.html', {
                'branch_id': branch_id,
                'scompany_id': scompany_id,
                'form': form})

    return render(request, 'view_payment.html', {
        'form': form,
        'title': "Оплата на дату %s" % form.instance.date_event.strftime("%d.%m.%Y"),
        'title_area': "Сальдовая ведомость",
        'title_small': Branch.objects.get(id=branch_id).Client.NameClient_short,
    })


# Вывод взаиморасчётов
@login_required()
@permission_required('accounting.cwp_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def get_accounting(request, branch_id, scompany_id, type_dct=None, dct=None):
    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
    branch_data = Branch.objects.get(id=branch_id)
    try:
        paymethods_id = request.session['paymethod_id']
        dateevent = request.session['date_event']
    except:
        paymethods_id = None
        dateevent = None

    list = credited_with_paid.objects.filter(branch=branch_data.id, scompany=scompany_data.id). \
        group_by('date_event', 'branch', 'scompany').values('date_event', 'branch', 'scompany'). \
        order_by('-date_event').distinct('date_event')

    form = form_payment(request.POST or None, branch_id=branch_id, scompany_id=scompany_id,
                        session_paymethods=paymethods_id, session_dateevent=dateevent)

    if request.POST:
        if form.is_valid():
            summ = float(form.cleaned_data['summ'])
            date_event = form.cleaned_data['date_event']
            document = form.cleaned_data.get('document')
            paymethods = form.cleaned_data.get('paymethods')

            credited_with_paid.objects. \
                create(dct=(None if document is None else document.id),
                       type_dct=(None if document is None else TypeDocument.objects.get(id=document.TypeDocument_id)),
                       summ=(summ * (-1) if summ > 0 and paymethods.slug != 'return' else summ),
                       branch=Branch.objects.get(id=branch_id),
                       scompany=ServingCompanyBranch.objects.get(id=scompany_id),
                       Create_user=request.user,
                       date_event=date_event, payment_methods=paymethods)

            request.session['paymethod_id'] = paymethods.id
            request.session['date_event'] = date_event.strftime("%Y-%m-%d")

            return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)
        else:
            return render(request, 'accounting.html',
                          {'form': form, 'act_reconciliation': form_act_reconciliation, 'branch_id': branch_data,
                           'scompany_id': scompany_data})
    else:
        account_saldo_start = start_balance.objects.filter(branch=branch_data, scompany=scompany_data).aggregate(
            summ=Sum('summ', output_field=FloatField()))
        account_saldo_total = credited_with_paid.objects.filter(branch=branch_data, scompany=scompany_data).aggregate(
            summ=Sum('summ', output_field=FloatField()))
        if account_saldo_total['summ'] is None: account_saldo_total['summ'] = 0
        if account_saldo_start['summ'] is None: account_saldo_start['summ'] = 0

        saldo_total = account_saldo_total['summ'] + account_saldo_start['summ']
        start_saldo = start_balance.objects.filter(branch=branch_data, scompany=scompany_data)
        if start_saldo:
            start_saldo = start_saldo.first().date_saldo

        return render(request, 'accounting.html', {
            'list_dates': list,
            'page_template': 'desktop_accounting.html',
            'scompany': scompany_data,
            'branch': branch_data,
            'account_saldo_start': account_saldo_start['summ'],
            'account_saldo_total': saldo_total,
            'curdate': datetime.datetime.today(),
            'date_startsaldo': start_saldo,
            'form_payment': form,
            'form_addaccural': form_addaccural(branch_id=branch_id, scompany_id=scompany_id),
            'form_actreconciliation': form_act_reconciliation(branch_id=branch_id, scompany_id=scompany_id),
            'form_startbalance': form_startbalance(data={'summ': account_saldo_start['summ']}),
            'year_list': reversed(range(2018, datetime.datetime.today().year + 1)),
            'random_num': random.randint(5, 100)
        })


# Добавить начисление вручную
@login_required()
@csrf_protect
def add_accural(request, branch_id, scompany_id):
    form = form_addaccural(request.POST or None, branch_id=branch_id, scompany_id=scompany_id)

    if request.POST:
        if form.is_valid():
            summ = form.cleaned_data['summ']
            date_event = form.cleaned_data['date_event']
            object = form.cleaned_data['objects']

            credited_with_paid.objects.create(type_dct=TypeDocument.objects.get(slug='tech_security_contract'),
                                              dct=object.TechSecurityContract.id, object=object.id,
                                              summ=float(summ),
                                              branch=object.TechSecurityContract.Branch,
                                              scompany=object.TechSecurityContract.ServingCompany,
                                              accural_methods='manual',
                                              Create_user=request.user, date_event=date_event)

            return redirect('finance_department:payment',
                            branch_id=object.TechSecurityContract.Branch.id,
                            scompany_id=object.TechSecurityContract.ServingCompany.id)
        else:
            return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)
    else:
        return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)


# Вывод платежей за период
@login_required()
@csrf_protect
def journal_payments_period(request):
    form = forms_payment_out_date(request.POST or None)

    if request.POST:
        if form.is_valid():
            filter_method = form.cleaned_data.get('paymentmethods', None)
            filter_scompany = form.cleaned_data.get('scompany', None)
            filter_start_date = form.cleaned_data['filter_start_date']
            filter_end_date = form.cleaned_data['filter_end_date']
            if filter_end_date is None:
                filter_end_date = filter_start_date

            payment_methods = PaymentMethods.objects.all()

            payments = credited_with_paid.objects.filter(scompany=filter_scompany,
                                                         date_event__gte=filter_start_date,
                                                         date_event__lte=filter_end_date,
                                                         summ__lt=0).order_by('date_event', 'branch')
            if filter_method:
                payments = payments.filter(payment_methods=filter_method)

            total_payments = total_bank = total_checkout = total_terminal = total_offsetting = 0
            if payments:
                TotalPayments = payments.aggregate(summ=Sum('summ', output_field=FloatField()))
                if TotalPayments['summ']:
                    total_payments = TotalPayments['summ']

                TotalBank = payments.filter(payment_methods=payment_methods.get(slug='bank'))
                if TotalBank:
                    TotalBank = TotalBank.aggregate(summ=Sum('summ', output_field=FloatField()))
                    if TotalBank['summ']:
                        total_bank = TotalBank['summ']

                TotalCheckout = payments.filter(payment_methods=payment_methods.get(slug='сheckout'))
                if TotalCheckout:
                    TotalCheckout = TotalCheckout.aggregate(summ=Sum('summ', output_field=FloatField()))
                    if TotalCheckout['summ']:
                        total_checkout = TotalCheckout['summ']

                TotalOffsetting = payments.filter(payment_methods=payment_methods.get(slug='offsetting'))
                if TotalOffsetting:
                    TotalOffsetting = TotalOffsetting.aggregate(summ=Sum('summ', output_field=FloatField()))
                    if TotalOffsetting['summ']:
                        total_offsetting = TotalOffsetting['summ']

                TotalTerminal = payments.filter(payment_methods=payment_methods.get(slug='terminal'))
                if TotalTerminal:
                    TotalTerminal = TotalTerminal.aggregate(summ=Sum('summ', output_field=FloatField()))
                    if TotalTerminal['summ']:
                        total_terminal = TotalTerminal['summ']

            return render(request, 'paids_from_date.html', {
                'form': form,
                'payments': payments,
                'method': (None if filter_method is None else filter_method.slug),
                'Total': total_payments,
                'TotalBank': total_bank,
                'TotalCheckout': total_checkout,
                'TotalOffsetting': total_offsetting,
                'TotalTerminal': total_terminal
            })

    return render(request, 'paids_from_date.html', {'form': form})


# Выборка начислений за период
@login_required()
@csrf_protect
def journal_accruals_period(request):
    form = accrual_for_period_form(request.POST or None, user=request.user)

    if request.POST:
        if form.is_valid():
            filter_datestart = form.cleaned_data['date_start']
            filter_dateend = form.cleaned_data['date_end']
            filter_scompany = form.cleaned_data.get('scompany', None)
            filter_typedct = form.cleaned_data.get('type_dct', None)

            accruals = credited_with_paid.objects.filter(scompany=filter_scompany, summ__gt=0,
                                                         date_event__range=(filter_datestart, filter_dateend)). \
                order_by('date_event', 'branch')
            if filter_typedct:
                accruals = accruals.filter(type_dct=filter_typedct)

            return render(request, 'accruals_from_period.html', {'form': form,
                                                                 'accurals': accruals,
                                                                 'Total': accruals.aggregate(summ=Sum('summ'))})
        else:
            return render(request, 'accruals_from_period.html', {'form': form})
    else:
        return render(request, 'accruals_from_period.html', {'form': form})


# Оборотная ведомость
@login_required()
@csrf_protect
def get_turnover_statement(request):
    form = forms_turnover_statement(request.POST or None, user=request.user)

    if request.POST:
        if form.is_valid():
            filter_scompany = form.cleaned_data.get('scompany', None)
            filter_month = form.cleaned_data.get('filter_month', None)
            filter_year = form.cleaned_data['filter_year']

            list_branch = credited_with_paid.objects. \
                filter(scompany=filter_scompany, date_event__month=filter_month, date_event__year=filter_year). \
                distinct('branch').values('branch')

            total_startbalance = total_startbalance_period = total_allitogo_accural = total_allitogo_payments = 0

            startbalance = start_balance.objects.filter(scompany=filter_scompany, branch__in=list_branch)
            if startbalance:
                startbalance = startbalance.aggregate(summ=Sum('summ', output_field=FloatField()))
                if startbalance['summ']:
                    total_startbalance = startbalance['summ']

            startbalance_period = credited_with_paid.objects. \
                filter(scompany=filter_scompany, branch__in=list_branch,
                       date_event__lt=date(int(filter_year), int(filter_month), 1))
            if startbalance_period:
                startbalance_period = startbalance_period.aggregate(summ=Sum('summ', output_field=FloatField()))
                if startbalance_period['summ']:
                    total_startbalance_period = startbalance_period['summ']

            allitogo_accural = credited_with_paid.objects. \
                filter(scompany=filter_scompany, summ__gt=0, branch__in=list_branch,
                       date_event__month=filter_month, date_event__year=filter_year)
            if allitogo_accural:
                allitogo_accural = allitogo_accural.aggregate(summ=Sum('summ', output_field=FloatField()))
                if allitogo_accural['summ']:
                    total_allitogo_accural = allitogo_accural['summ']

            allitogo_payments = credited_with_paid.objects. \
                filter(scompany=filter_scompany, summ__lt=0, branch__in=list_branch,
                       date_event__month=filter_month, date_event__year=filter_year)
            if allitogo_payments:
                allitogo_payments = allitogo_payments.aggregate(summ=Sum('summ', output_field=FloatField()))
                if allitogo_payments['summ']:
                    total_allitogo_payments = allitogo_payments['summ']

            total = total_startbalance + total_startbalance_period + total_allitogo_accural + total_allitogo_payments

            return render(request, 'turnover_statement.html', {
                'form': form,
                'scompany': filter_scompany,
                'list_branch': list_branch,
                'select_month': filter_month,
                'select_year': filter_year,
                'allitogo_accural': total_allitogo_accural,
                'allitogo_payments': total_allitogo_payments,
                'allitogo': total})
        else:
            return render(request, 'turnover_statement.html', {'form': form})
    else:
        return render(request, 'turnover_statement.html', {'form': form})


# Оборотная ведомость
@login_required()
@csrf_protect
def get_turnover_statement_forunits(request):
    form = forms_turnover_statement_forunits(request.POST or None, user=request.user)

    if request.POST:
        if form.is_valid():
            filter_scompany = form.cleaned_data.get('scompany', None)
            filter_city = form.cleaned_data.get('city', None)
            filter_month = form.cleaned_data.get('filter_month', None)
            filter_year = form.cleaned_data['filter_year']
            filter_accrual = form.cleaned_data['filter_accrual']

            list_objects = allobjects.objects.filter(city_id=filter_city.id, scompany_id=filter_scompany.id)

            return render(request, 'turnover_statement_forunits.html', {
                'form': form,
                'scompany': filter_scompany,
                'list_objects': list_objects,
                'select_month': filter_month,
                'select_year': filter_year,
                'accrual': filter_accrual
            })
        else:
            return render(request, 'turnover_statement_forunits.html', {'form': form})
    else:
        return render(request, 'turnover_statement_forunits.html', {'form': form})


# Дебиторская задолженность
@login_required()
@csrf_protect
def get_arrears(request):
    filter_cmonths = list_duty = filter_status = filter_scompany = None
    total_duty = 0
    form = arrears_form(request.POST or None)

    if request.POST:
        if form.is_valid():
            curdate = datetime.datetime.today()
            filter_cmonths = form.cleaned_data['count_months']
            filter_scompany = form.cleaned_data.get('scompany', None)
            filter_status = form.cleaned_data.get('status', None)
            min_credit = int(SystemConstant.objects.get(slug='min_credit').ConstantsValue)

            if filter_status == 'active':
                list_duty = saldotoday.objects.filter(scompany_id=filter_scompany.id, saldo_today__gte=min_credit)

                for duty in list_duty:
                    branch = Branch.objects.get(id=duty.id)
                    scompany = ServingCompanyBranch.objects.get(id=duty.scompany_id)

                    # Сумма начисления в этом месяце
                    accural = credited_with_paid.objects.filter(
                        branch=branch, scompany=scompany, date_event__month=curdate.month,
                        date_event__year=curdate.year, summ__gt=0).aggregate(summ=Sum('summ', output_field=FloatField()))

                    # Если сумма долга > 0 и есть начисления в текущем месяце
                    if accural['summ']:
                        # Если сумма долга превышает начисления на указанное количество месяцев
                        # (1,1 - компенсация недостающих копеек)
                        if ((float(duty.saldo_today) / accural['summ']) * 1.1) >= int(filter_cmonths):
                            # то выводим
                            total_duty = total_duty + accural['summ']
            else:
                list_clients = Branch.objects.filter(id__in=clients_active_securityobjects.objects.filter(scompany_id=filter_scompany.id))
                list_duty = saldotoday.objects.filter(scompany_id=filter_scompany.id, saldo_today__gt=0).exclude(id__in=list_clients)
                total_duty = list_duty.aggregate(summ=Sum('saldo_today', output_field=FloatField()))
                total_duty = total_duty['summ']

    return render(request, 'arrears.html', {'form': form, 'count_months': filter_cmonths, 'status': filter_status,
                                            'list_duty': list_duty, 'scompany': filter_scompany,
                                            'total_duty': round(total_duty, 2)})


def export_toexcel_arrears(request, cmonths, scompany_id, status):
    lst = []
    curdate = datetime.datetime.today()
    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
    title = ['Контрагент', 'Начислено', 'Долг']
    lst.append(title)

    if status == 'active':
        min_credit = int(SystemConstant.objects.get(slug='min_credit').ConstantsValue)
        list_duty = saldotoday.objects.filter(scompany_id=scompany_data.id, saldo_today__gte=min_credit)

        for duty in list_duty:
            branch = Branch.objects.get(id=duty.id)
            # Сумма начисления в этом месяце
            accural = credited_with_paid.objects.filter(
                branch=branch, scompany=scompany_data, date_event__month=curdate.month,
                date_event__year=curdate.year, summ__gt=0).aggregate(summ=Sum('summ', output_field=FloatField()))

            # Если сумма долга > 0 и есть начисления в текущем месяце
            if accural['summ']:
                if ((float(duty.saldo_today) / accural['summ']) * 1.1) >= int(cmonths):
                    line = [get_nameclient(branch.id), accural['summ'], duty.saldo_today]
                    lst.append(line)
    else:
        list_duty = saldotoday.objects.filter(scompany_id=scompany_data.id, saldo_today__gt=0).\
            exclude(id__in=Branch.objects.filter(id__in=clients_active_securityobjects.objects.
                                                 filter(scompany_id=scompany_data.id)))
        for duty in list_duty:
            # Сумма начисления в этом месяце
            accural = credited_with_paid.objects.filter(
                branch=Branch.objects.get(id=duty.id), scompany=scompany_data, date_event__month=curdate.month,
                date_event__year=curdate.year, summ__gt=0).aggregate(summ=Sum('summ', output_field=FloatField()))

            line = [get_nameclient(duty.id), accural['summ'], duty.saldo_today]
            lst.append(line)

    filename = 'billing_export_arrears_%s_%s_%s' % (status, slugify(scompany_data.NameBranch, max_length=20, word_boundary=True, separator="_"),
                                                    datetime.datetime.today().__str__())
    return ExcelResponse(lst, output_filename=filename, worksheet_name='arrears')


# Рассылка смс-сообщений
def sendsms_debtors_list(request):
    form = forms_smssend_debtors(request.POST or None)
    list_saldo = []

    if request.POST:
        if form.is_valid():
            scompany = form.cleaned_data['scompany']
            ct_months = form.cleaned_data['ct_months']
            list_branch = []

            list_saldo = saldobranch.objects.\
                exclude(phone_sms__exact='').filter(scompany_id=scompany.id, saldo__gte=1000)

            for client in list_saldo:
                # размер ежемесячного начисления
                techsecurity_objects = TechSecurityObject.objects.filter(
                    StatusSecurity=True,
                    TechSecurityContract__in=TechSecurityContract.objects.
                        filter(Branch=Branch.objects.get(id=client.id), ServingCompany=scompany)). \
                    aggregate(saldo=Sum('PriceNoDifferent', output_field=FloatField()))
                maintservice_objects = MaintenanceServiceObject.objects.filter(
                    (Q(DateEnd__gt=datetime.datetime.today()) | Q(DateEnd__isnull=True)),
                    (Q(DateStart__lt=datetime.datetime.today()) | Q(DateStart__isnull=True)),
                    MaintenanceServiceContract=MaintenanceServiceContract.objects.
                        filter(Branch=Branch.objects.get(id=client.id), ServingCompany=scompany)). \
                    aggregate(saldo=Sum('Price', output_field=FloatField()))
                cost_currmonth = (0 if techsecurity_objects['saldo'] is None else techsecurity_objects['saldo']) + \
                                 (0 if maintservice_objects['saldo'] is None else maintservice_objects['saldo'])

                if cost_currmonth > 0:
                    if (float(client.saldo) / cost_currmonth) * 1.1 >= int(ct_months):
                        list_branch.append(client.id)

            list_saldo = list_saldo.filter(id__in=list_branch)

    return render(request, 'sendsms_debtors.html', {'form': form, 'list': list_saldo})


@csrf_exempt            # Отключим проверку токена формы
def sendDebtSMS(request):
    scompany = 'amuletpco'
    phone = request.GET.get('phone', None)
    summ = request.GET.get('summ', None)




    # if request.is_ajax():
    #     phone = request.POST['phone']
    #     summ = request.POST['summ']
    #     if phone and summ is not None:
    #         smsc = SMSC()
    #         result = smsc.send_sms('7%s' % phone, u'Ваш долг Амулету состовляет %s руб. Подробно по телефону (3537)26-54-45' % summ, sender="%s" % scompany)
    #         if len(result) == 4:
    #             return HttpResponse('Success')
    #         else:
    #             return HttpResponse('Error')


def byDateEvent_key(accurals):
    return accurals['date_event']


# Акт сверки
def view_act_reconciliation_template(request, branch_id, scompany_id):
    form = form_act_reconciliation(request.POST or None, branch_id=branch_id, scompany_id=scompany_id)

    if request.POST:
        if form.is_valid():

            # Настраиваем локали
            if sys.platform == 'win32':
                locale.setlocale(locale.LC_ALL, 'rus_rus')
            else:
                locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
            int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
            exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')
            saldo_end_paid = saldo_end_accural = saldo_start_paid = saldo_start_accural = ''

            # Получаем с формы даты
            date_start = form.cleaned_data['date_start']
            date_end = form.cleaned_data['date_end']
            document = form.cleaned_data['document']

            # Получаем данные о сервисной компании и контрагенте
            scompany = ServingCompanyBranch.objects.get(id=scompany_id)
            branch = Branch.objects.get(id=branch_id)

            # Получаем данные о начальном сальдо
            startbalance = start_balance.objects. \
                filter(branch=branch, scompany=scompany). \
                aggregate(summ=Sum('summ', output_field=FloatField()))

            # Выбираем все начисления и оплаты
            cwp = credited_with_paid.objects.filter(branch=branch_id, scompany=scompany_id)
            if document:
                cwp = cwp.filter(dct=document.id)

            # Считаем сумму за предыдущий период (на начало периода)
            previous_period = cwp.filter(date_event__lt=date_start).aggregate(
                summ=Sum('summ', output_field=FloatField()))

            # Вибираем начисления и оплаты за нужный период
            cash_period = cwp.filter(date_event__range=(date_start, date_end))

            # Отделяем начисления от оплат и фильтруем по заданному периоду
            accurals_period = cash_period.filter(summ__gt=0).order_by('date_event')
            paids_period = cash_period.filter(summ__lt=0).order_by('date_event')

            # Групируем начисления и оплаты по дате
            accurals_group = accurals_period.values('date_event').annotate(summ=Sum('summ', output_field=FloatField()))
            paids_group = paids_period.values('date_event', 'summ')

            # Объединяем начисления и оплаты
            balance_period_list = list(chain(accurals_group, paids_group))
            balance_period_list = sorted(balance_period_list, key=byDateEvent_key)

            # Считаем сумму за период
            balance_period_summ = cash_period.aggregate(summ=Sum('summ', output_field=FloatField()))

            saldo_start = (0 if startbalance['summ'] is None else startbalance['summ']) + (
                0 if previous_period['summ'] is None else previous_period['summ'])
            saldo_end = saldo_start + (0 if balance_period_summ['summ'] is None else balance_period_summ['summ'])

            if branch.NameBranch:
                ClientName = branch.NameBranch
            else:
                if branch.Client.NameClient_full:
                    ClientName = branch.Client.NameClient_full
                else:
                    ClientName = branch.Client.NameClient_short

            if saldo_start < 0:
                saldo_start_paid = abs(saldo_start)
            else:
                saldo_start_accural = abs(saldo_start)

            if saldo_end < 0:
                Company = ClientName
                saldo_end_paid = abs(saldo_end)
                saldo_itogo = saldo_end_paid
                saldo_text = decimal2text(abs(saldo_end_paid), int_units=int_units, exp_units=exp_units)
            else:
                Company = scompany.ServingCompany.NameCompany_short
                saldo_end_accural = abs(saldo_end)
                saldo_itogo = saldo_end_accural
                saldo_text = decimal2text(abs(saldo_end_accural), int_units=int_units, exp_units=exp_units)

            text_template = Template(AccountingTemplates.objects.get(slug='act_reconciliation').TextTemplate)

            StringTable = '<table border="1" cellpadding="0" cellspacing="0" style="width:100%"><tbody>'
            for i, item in enumerate(balance_period_list):
                dateevent = item['date_event']
                if item['summ'] < 0:  # Оплата
                    string_table = '<tr><td style="width:7%">&nbsp;' + (i + 1).__str__() + \
                                   '</td><td style="width:23%">&nbsp;Оплата от ' + dateevent.strftime("%d.%m.%y") + \
                                   '</td><td style="width:10%">&nbsp;</td><td style="width:10%">&nbsp;' + str(
                        abs(item['summ'])) + \
                                   '</td><td style="width:7%">&nbsp;</td><td style="width:23%">&nbsp;</td><td style="width:10%">&nbsp;</td><td style="width:10%">&nbsp;</td></tr>'
                else:
                    string_table = '<tr><td style="width:7%">&nbsp;' + (i + 1).__str__() + \
                                   '</td><td style="width:23%">&nbsp;Оказание услуг от ' + dateevent.strftime(
                        "%d.%m.%y") + \
                                   '</td><td style="width:10%">&nbsp;' + str(abs(item['summ'])) + \
                                   '</td><td style="width:10%">&nbsp;</td><td style="width:7%">&nbsp;</td><td style="width:23%">&nbsp;</td><td style="width:10%">&nbsp;</td><td style="width:10%">&nbsp;</td></tr>'
                StringTable = StringTable + string_table
            StringTable = StringTable + '</tbody></table>'

            # Итоги, обороты
            return_accural = return_paid = 0
            if accurals_period:
                ReturnAccural = accurals_period.aggregate(summ=Sum('summ', output_field=FloatField()))
                if ReturnAccural['summ']:
                    return_accural = ReturnAccural['summ']
            if paids_period:
                ReturnPaid = paids_period.aggregate(summ=Sum('summ', output_field=FloatField()))
                if ReturnPaid['summ']:
                    return_paid = ReturnPaid['summ']

            tags = Context({
                'Period': date_start.strftime("%d.%m.%Y") + ' - ' + date_end.strftime("%d.%m.%Y"),
                'PeriodDateEnd': date_end.strftime("%d.%m.%Y"),
                'Document': ('' if document is None else 'по ' + document.TypeDocumentName + ' ' + document.NumDocument + ' от ' + document.DateConclusion.strftime("%d.%m.%Y")),
                'ServingCompanyName_short': scompany.ServingCompany.NameCompany_short,
                'ServingCompanyManage_name': scompany.ServingCompany.Management_name,
                'ServingCompanyManage_post': scompany.ServingCompany.Management_post,
                'BranchName': ClientName,
                'Company': Company,
                'GenerateStringTable': StringTable,

                # Сальдо начальное
                'SaldoAccural_start': saldo_start_accural,
                'SaldoPaid_start': saldo_start_paid,

                # Обороты за период
                'ReturnAccural': return_accural,
                'ReturnPaid': abs(return_paid),

                # Сальдо конечное
                'SaldoAccural_end': saldo_end_accural,
                'SaldoPaid_end': saldo_end_paid,
                'Saldo': saldo_itogo,
                'SaldoText': saldo_text
            })

            return render(request, 'view_template.html', {'title': 'Акт сверки',
                                                          'area': scompany.NameBranch + ' с ' + ClientName,
                                                          'text': text_template.render(tags)})
        else:
            redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)
    else:
        redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)


# Скорректировать начальное сальдо
@login_required()
def view_change_startbalance_template(request, branch_id, scompany_id):
    if request.POST:
        date_saldo = datetime.datetime.strptime(SystemConstant.objects.get(slug='date_startsaldo').ConstantsValue,
                                                '%d.%m.%Y')
        form = form_startbalance(request.POST or None)
        if form.is_valid():
            summ = form.cleaned_data['summ']
            obj, created = start_balance.objects.update_or_create(branch=Branch.objects.get(id=branch_id),
                                                                  scompany=ServingCompanyBranch.objects.get(
                                                                      id=scompany_id),
                                                                  defaults={"summ": float(summ),
                                                                            "date_saldo": date_saldo})
            if created:
                start_balance.objects.filter(id=obj.id).update(Create_user=request.user)
            else:
                start_balance.objects.filter(id=obj.id).update(Update_user=request.user)
    return redirect('finance_department:payment', branch_id=branch_id, scompany_id=scompany_id)


# Выгрузка объектов для формирования счетов - вывод на экран
@login_required()
@csrf_protect
def export_to1S_objects_action(request):
    edo = paymentAfter = scompany_id = None
    objects_error = objects_noerror = []
    form = forms_export_to1S_objects_action(request.POST or None)

    if request.POST:
        if form.is_valid():
            payment_type = PaymentMethods.objects.get(slug='bank').id
            edo = form.cleaned_data['edo']
            paymentAfter = form.cleaned_data['paymentAfter']
            scompany_id = request.POST['scompany']

            objects_paymentAfter = TechSecurityObject.objects.\
                filter(TechSecurityContract__in=TechSecurityContract.objects.filter(PaymentAfter=True)).values_list('id')
            objects_action = allactive_securityobjects.objects.filter(scompany_id=scompany_id,
                                                                      price__gt=0, edo=edo,
                                                                      payment_id=payment_type)
            if paymentAfter:
                objects_action = objects_action.filter(id__in=objects_paymentAfter)
            else:
                objects_action = objects_action.exclude(id__in=objects_paymentAfter)
            objects_noerror = objects_action.filter(
                Q(inn__isnull=False) & (Q(inn__regex=r'^\d{10}') | Q(inn__regex=r'^\d{12}'))).order_by('name_client')
            objects_error = objects_action.exclude(
                Q(inn__isnull=False) & (Q(inn__regex=r'^\d{10}') | Q(inn__regex=r'^\d{12}'))).order_by('name_client')

    return render(request, 'export_to1S_objects.html', {
        'form': form,
        'edo': edo,
        'paymentAfter': paymentAfter,
        'scompany_id': scompany_id,
        'objects_error': objects_error,
        'objects_noerror': objects_noerror})


# Выгрузка объектов для формирования счетов - вывод в файл
def export_to1S_objects_to_xml(request, scompany_id, edo, paymentAfter):
    scompany = ServingCompanyBranch.objects.get(id=scompany_id)
    payment_type = PaymentMethods.objects.get(slug='bank').id

    file_name = 'objects_billing_%s_d%s_t%s.%s' % (
        str('edo' if edo == 'True' else 'noedo'),
        datetime.datetime.today().strftime("%Y%m%d"),
        datetime.datetime.today().strftime("%H%M"), scompany.file_expansion_to1S)

    # Путь до папки на сервере
    file = '/home/django/1c_exchange/%s/%s' % (scompany.catalog_expansion_to1S, file_name)
    # Путь до папки на тестовом
    # file = 'C:/Temp/%s' % file_name

    f = open(file, 'w', encoding='windows-1251')
    f.write('<?xml version="1.0" encoding="windows-1251">' + '\n')
    # name_client = type(scompany.NameBranch)       .decode('utf8').encode('cp1251')
    f.write('<OrgPoluch>%s</OrgPoluch>' % scompany.NameBranch + '\n')
    f.write('<EDO>%s</EDO>' % str('YES' if edo is True else 'NO') + '\n')

    objects_action = allactive_securityobjects.objects.filter(
        Q(inn__isnull=False) & (Q(inn__regex=r'^\d{10}') | Q(inn__regex=r'^\d{12}')),
        scompany_id=scompany_id, price__gt=0, edo=edo, payment_id=payment_type
    )

    branch_list = objects_action.distinct('branch_id')

    for branch_item in branch_list:
        branch_data = Branch.objects.get(id=branch_item.branch_id)
        name_client = (branch_item.name_client if branch_item.name_client != '' else get_nameclient(branch_item.id))

        if branch_data.FormsSchet.slug == 'form_general':
            f.write('<Org>' + '\n')
            f.write('<INN>%s</INN>' % branch_item.inn + '\n')
            f.write('<Plat>%s</Plat>' % name_client + '\n')

            objects_list = objects_action.\
                filter(branch_id=branch_item.branch_id).\
                values_list('address_object', 'numcontract_external', 'numcontract_internal', 'price')
            for object_item in objects_list:
                #address = numcontract = None
                #address = object_item.address_object.encode('cp1251').decode('cp1251')
                #numcontract = object_item.numcontract_internal.encode('cp1251').decode('cp1251')

                numcontract = (object_item.numcontract_external if object_item.numcontract_external != '' else object_item.numcontract_internal)
                text = '<Object><Adress>%s</Adress><Dogovor>%s от %s</Dogovor><Summa>%s</Summa></Object>' % \
                       (branch_item.address_object, numcontract, object_item.date_conclusion.strftime('%d.%m.%Y'), str(object_item.price)) + '\n'
                f.write(text)
            f.write('</Org>' + '\n')

        elif branch_data.FormsSchet.slug == 'form_contract':
            contract_list = objects_action.filter(branch_id=branch_item.branch_id).values('contract_id').distinct('contract_id')
            for contract_item in contract_list:
                f.write('<Org>' + '\n')
                f.write('<INN>%s</INN>' % branch_item.inn + '\n')
                f.write('<Plat>%s</Plat>' % name_client + '\n')

                objects_list = objects_action.\
                    filter(branch_id=branch_item.branch_id, contract_id=contract_item['contract_id']).\
                    values('address_object', 'numcontract_external', 'numcontract_internal', 'date_conclusion', 'price')

                for object_item in objects_list:
                    numcontract = (object_item['numcontract_external'] if object_item['numcontract_external'] != '' else object_item['numcontract_internal'])
                    text = '<Object><Adress>%s</Adress><Dogovor>%s от %s</Dogovor><Summa>%s</Summa></Object>' % \
                           (object_item['address_object'], numcontract, object_item['date_conclusion'].strftime('%d.%m.%Y'), str(object_item['price'])) + '\n'
                    f.write(text)
                f.write('</Org>' + '\n')

        else:
            for object_item in objects_action:
                f.write('<Org>' + '\n')
                f.write('<INN>%s</INN>' % branch_item.inn + '\n')
                f.write('<Plat>%s</Plat>' % name_client + '\n')

                numcontract = (object_item.numcontract_external if object_item.numcontract_external != '' else object_item.numcontract_internal)
                text = '<Object><Adress>%s</Adress><Dogovor>%s от %s</Dogovor><Summa>%s</Summa></Object>' % \
                       (branch_item.address_object, numcontract, object_item.date_conclusion.strftime('%d.%m.%Y'), str(object_item.price)) + '\n'
                f.write(text)
            f.write('</Org>' + '\n')
    f.close()
    return redirect('finance_department:export_to1S_objects_action')


def export_to1S_objects_action_nofit(request, scompany_id):
    objects_fit = allactive_securityobjects.objects. \
        filter(scompany_id=scompany_id, payment_id=PaymentMethods.objects.get(slug='bank').id). \
        exclude(Q(inn__isnull=False) & (Q(inn__regex=r'^\d{10}') | Q(inn__regex=r'^\d{12}')))
    return render(request, 'nofit_objects_for_export.html', {'objects_nofit': objects_fit})


# Выгрузка объектов для формирования счетов - записать в таблицу
def export_to1S_objects_action_run(request, scompany_id, edo):
    clients = allactive_securityobjects.objects. \
        filter(scompany_id=scompany_id, price__gt=0, payment_id=PaymentMethods.objects.get(slug='bank').id). \
        filter(Q(inn__isnull=False) & (Q(inn__regex=r'^\d{10}') | Q(inn__regex=r'^\d{12}'))). \
        group_by('inn', 'name_client', 'name_branch', 'numcontract_internal', 'numcontract_external', 'edo').distinct()

    if clients:
        for client in clients:
            if client.name_branch:
                client_name = client.name_branch
            else:
                client_name = client.name_client

            if client.numcontract_external:
                contract = client.numcontract_external
            else:
                contract = client.numcontract_internal

            objects = allactive_securityobjects.objects.filter(inn=client.inn, numcontract_internal='',
                                                               numcontract_external='')

            client_add = temp_export_object_to1S_client.objects.create(inn=client.inn, name_client=client_name,
                                                                       edo=client.edo, contract=contract)
            client_add.objects.add(*objects)

    return redirect('index:dashboard')


# Загрузка банковских платежей из 1С
def import_from1C_bankpayments(request):
    payments = scompany = date_payments = total_summ = None
    form = forms_import_from1C_bankpayments(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany = form.cleaned_data.get('scompany')
            date_payments = form.cleaned_data['date_payments']
            payments = temp_export_bankpayments_from1C.objects.filter(date_entry=date_payments,
                                                                      scompany_inn=scompany.INN).order_by('-summ')
            total_summ = payments.aggregate(summ=Sum('summ', output_field=FloatField()))

    return render(request, 'import_from1S_bankpayments.html', {
        'form': form,
        'payments': payments,
        'scompany': scompany,
        'date_entry': date_payments,
        'total_payments': total_summ
    })


# Перенос банковских платежей из временной таблицы
def import_from1C_bankpayments_run(request):
    payment_type = PaymentMethods.objects.get(slug='bank')

    if request.POST:
        date_payments = datetime.datetime.strptime(request.POST['date_entry'], '%Y-%m-%d').date()
        scompany = ServingCompany.objects.get(id=request.POST['scompany_id'])
        payments = temp_export_bankpayments_from1C.objects.filter(date_entry=date_payments,
                                                                  scompany_inn=scompany.INN).order_by('-summ')
        for i, payments_item in enumerate(payments):
            if request.POST['branch_' + (i + 1).__str__()].isdigit():
                document_id = request.POST['branch_' + (i + 1).__str__()]
                document_data = alldocuments_fulldata.objects.get(id=document_id)
                payment_move = temp_export_bankpayments_from1C.objects.get(id=payments_item.id)
                credited_with_paid.objects.create(dct=document_data.id,
                                                  type_dct=TypeDocument.objects.get(id=document_data.TypeDocument_id),
                                                  branch=Branch.objects.get(id=document_data.Branch_id),
                                                  scompany=ServingCompanyBranch.objects.get(id=document_data.ServingCompany_id),
                                                  date_event=date_payments,
                                                  payment_methods=payment_type,
                                                  summ=payment_move.summ*(-1))
                temp_export_bankpayments_from1C.objects.filter(id=payments_item.id).delete()

    return redirect('finance_department:import_from1C_bankpayments')


# Насчитать начальное сальдо
def get_initial_balance(date_balance):
    list_branch = Branch.objects.all()
    list_scompany = ServingCompanyBranch.objects.all()
    for branch in list_branch:
        for scompany in list_scompany:
            saldo = credited_with_paid.objects.filter(branch=branch.id, scompany=scompany.id,
                                                      date__lt=date_balance).aggregate(
                summ=Sum('summ', output_field=FloatField()))
            if saldo:
                credited_with_paid.objects.create(branch=branch, scompany=scompany, summ=saldo,
                                                  date_balance=date_balance)

    return redirect('index:dashboard')


# Удалить начисления и оплаты до нужного дня
def dlt_credited_paid(date_balance):
    credited_with_paid.objects.filter(date__lt=date_balance).delete()

    return redirect('index:dashboard')
