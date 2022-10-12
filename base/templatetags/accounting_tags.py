import datetime
import re
import time

from itertools import chain
from django import template
from django.db.models import Sum, FloatField, Q
from django.template.defaultfilters import stringfilter

from accounting.models import credited_with_paid, start_balance, temp_export_bankpayments_from1C
from base.models import Branch, ServingCompanyBranch, alldocuments_fulldata, allobjects, Client
from base.templatetags.other_tags import get_nameclient
from build_service.models import BuildServiceContract, BuildServiceObject, BuildServiceAct
from contract_department.models import allactive_securityobjects
from maintenance_service.models import MaintenanceServiceContract, MaintenanceServiceObject
from reference_books.models import TypeDocument
from tech_security.models import TechSecurityObject

__author__ = 'bondarenkoav'

register = template.Library()


@register.inclusion_tag('templatetags/table_accounting.html')
def view_table_accounting(branch, scompany, event_date):
    credits = credited_with_paid.objects. \
        filter(branch=branch, scompany=scompany, date_event=event_date, summ__gt=0, payment_methods__isnull=True). \
        group_by('date_event', 'dct', 'type_dct').annotate(summ=Sum('summ'))

    paids = credited_with_paid.objects. \
        filter(branch=branch, scompany=scompany, date_event=event_date, payment_methods__isnull=False). \
        group_by('date_event', 'dct', 'type_dct', 'payment_methods', 'id').annotate(summ=Sum('summ'))

    saldo_day = credited_with_paid.objects. \
        filter(branch=branch, scompany=scompany, date_event=event_date). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    combine = chain(credits, paids)
    accounting_data_sorted = sorted(combine, key=lambda instance: (-time.mktime(instance.date_event.timetuple())))

    return {'accounting_data': accounting_data_sorted, 'date': event_date,
            'saldo_day': format(saldo_day['summ'], '.2f'), 'branch_id': branch, 'scompany_id': scompany}


# Отображение таблицы должников
@register.inclusion_tag('templatetags/table_arrears.html')
def views_table_arrears(branch_id, scompany_id, total_summ, count_months):
    curdate = datetime.datetime.today()
    branch = Branch.objects.get(id=branch_id)
    scompany = ServingCompanyBranch.objects.get(id=scompany_id)
    object_str = ''

    # Последняя оплата
    last_payment = credited_with_paid.objects.filter(branch=branch, scompany=scompany, summ__lt=0).last()

    # Сумма начисления в этом месяце
    accural = credited_with_paid.objects. \
        filter(branch=branch, scompany=scompany, date_event__month=curdate.month,
               date_event__year=curdate.year, summ__gt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    # Если сумма долга > 0 и есть начисления в текущем месяце
    if accural['summ']:
        accural_summ = accural['summ']
        if accural_summ:
            # Если сумма долга превышает начисления на указанное количество месяцев (1,1 - компенсация недостающих копеек)
            if ((float(total_summ) / accural_summ) * 1.1) >= int(count_months):
                # то выводим
                objects = allobjects.objects.filter(branch_id=branch_id, scompany_id=scompany_id).exclude(
                    object_num__iexact='б/н')
                for object in objects:
                    if object_str:
                        object_str = object_str + ', ' + object.object_num
                    else:
                        object_str = object.object_num

                return {'branch': branch, 'total_summ': total_summ, 'summ_accural': accural_summ,
                        'last_payment': last_payment, 'objects': object_str}


# Отображение таблицы должников по снятым
@register.inclusion_tag('templatetags/table_arrears_client_noactive.html')
def views_table_arrears_client_noactive(branch_id, scompany_id, total_summ):
    curdate = datetime.datetime.today()
    branch = Branch.objects.get(id=branch_id)
    scompany = ServingCompanyBranch.objects.get(id=scompany_id)
    object_str = ''

    # Последняя оплата
    last_payment = credited_with_paid.objects.filter(branch=branch, scompany=scompany, summ__lt=0).last()

    # Сумма начисления в этом месяце
    accural = credited_with_paid.objects. \
        filter(branch=branch, scompany=scompany, date_event__month=curdate.month,
               date_event__year=curdate.year, summ__gt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    if accural:
        accural_summ = accural['summ']

    return {'branch': branch, 'total_summ': total_summ, 'summ_accural': accural_summ, 'last_payment': last_payment,
            'objects': object_str}


# Отображение начислений и оплат контрагента
@register.inclusion_tag('templatetags/table_turnoven_statement.html')
def views_table_turnover_statement(branch, scompany, select_month, select_year):
    branch_data = Branch.objects.get(id=branch)
    startbalance = start_balance.objects. \
        filter(branch=branch, scompany=scompany). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    startbalance_period = credited_with_paid.objects. \
        filter(scompany=scompany, branch=branch,
               date_event__lt=datetime.date(int(select_year), int(select_month), 1)). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    credits = credited_with_paid.objects. \
        filter(scompany=scompany, branch=branch,
               date_event__month=select_month, date_event__year=select_year, summ__gt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    paids = credited_with_paid.objects. \
        filter(scompany=scompany, branch=branch,
               date_event__month=select_month, date_event__year=select_year, summ__lt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    if startbalance['summ'] is None:
        startbalance['summ'] = 0
    if startbalance_period['summ'] is None:
        startbalance_period['summ'] = 0
    if credits['summ'] is None:
        credits['summ'] = 0
    if paids['summ'] is None:
        paids['summ'] = 0

    total = startbalance['summ'] + startbalance_period['summ'] + credits['summ'] + paids['summ']
    return {'branch': branch_data, 'sum_startbalance': startbalance['summ'] + startbalance_period['summ'],
            'summ_accural': credits['summ'], 'summ_payment': paids['summ'], 'total': total}


# Отображение начислений и оплат контрагента
@register.inclusion_tag('templatetags/table_turnoven_statement_forunits.html')
def views_table_turnover_statement_forunits(branch_id, scompany_id, contract_id, object_id, month, year):
    branch_data = Branch.objects.get(id=branch_id)
    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
    accrual = credited_with_paid.objects.filter(branch=branch_data, scompany=scompany_data, object=object_id,
                                                date_event__month=month, date_event__year=year, summ__gt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))
    paids = credited_with_paid.objects.filter(branch=branch_data, scompany=scompany_data, dct=contract_id,
                                              date_event__month=month, date_event__year=year, summ__lt=0). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    return {'summa_accrual': (0 if accrual['summ'] is None else accrual['summ']),
            'summa_paids': (0 if paids['summ'] is None else paids['summ'] * (-1))}


@register.simple_tag()
def filter_actionObject_turnover_statement_forunits(branch_id, scompany_id, contract_id, object_id, month, year, accrual):
    flag = 'no'
    branch_data = Branch.objects.get(id=branch_id)
    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)

    accrualandpaids = credited_with_paid.objects.filter(Q(object=object_id) | Q(dct=contract_id),
                                                        branch=branch_data, scompany=scompany_data,
                                                        date_event__month=month, date_event__year=year)
    if accrualandpaids.count() > 0:
        if accrual == 'yes':
            accruals = credited_with_paid.objects.\
                filter(branch=branch_data, scompany=scompany_data, object=object_id, date_event__month=month,
                       date_event__year=year, summ__gt=0).\
                aggregate(summ=Sum('summ', output_field=FloatField()))
            if (0 if accruals['summ'] is None else accruals['summ']) > 0:
                flag = 'yes'
        else:
            flag = 'all'
    return flag


# Отображение начисления
@register.inclusion_tag('templatetags/table_accural.html')
def views_table_accural(accural):
    address = ()
    type_document = accural.type_dct.slug
    if type_document == 'tech_security_contract':
        address = TechSecurityObject.objects.get(id=accural.object).AddressObject
    elif type_document == 'build_service_contract' or type_document == 'maintenance_service_contract':
        address = ''

    return {'id': accural.id, 'num_object': accural.object, 'address': address, 'summa': accural.summ}


@register.filter
@stringfilter
def get_document(document_id):
    types_doc = TypeDocument.objects.all()
    try:
        doc = alldocuments_fulldata.objects.get(id=document_id)
        if types_doc.get(id=doc.TypeDocument_id).type == 'contract':
            return doc.NumDocument.__str__() + ' от ' + doc.DateConclusion.strftime('%d.%m.%Y')

        if types_doc.get(id=doc.TypeDocument_id).type == 'act':
            return doc.id.__str__() + ' от ' + doc.DateWork.strftime('%d.%m.%Y')
    except:
        return 'Ошибка'


@register.filter
@stringfilter
def get_object(object_id, branch_id):
    try:
        return allobjects.objects.get(id=int(object_id), branch_id=branch_id).object_address
    except:
        return 'Ошибка'


@register.filter
@stringfilter
def list_objects(dct, date):
    str = ''
    document = alldocuments_fulldata.objects.get(id=int(dct))
    type_document = TypeDocument.objects.get(id=document.TypeDocument_id)
    objects = credited_with_paid.objects.filter(dct=int(dct), date_event=date, summ__gt=0).values('dct', 'object',
                                                                                                  'summ')

    if objects:
        for item in objects:
            # Охрана (для охраны это объекты)
            if type_document.slug == 'tech_security_contract':
                if str == '':
                    str = TechSecurityObject.objects.get(id=item['object']).AddressObject + ' (' + item[
                        'summ'].__str__() + ' р.)'
                else:
                    str = str + ' | ' + TechSecurityObject.objects.get(id=item['object']).AddressObject + ' (' + item[
                        'summ'].__str__() + ' р.)'
            # Монтаж (для монтажа это договоры)
            if type_document.slug == 'build_service_contract':
                blist_object = BuildServiceObject.objects. \
                    filter(BuildServiceContract=BuildServiceContract.objects.get(id=item['dct']))
                for bobject in blist_object:
                    if str == '':
                        str = bobject.AddressObject + ' (' + bobject.Price.__str__() + ' р.)'
                    else:
                        str = str + ', ' + bobject.AddressObject + ' (' + bobject.Price.__str__() + ' р.)'
            # ТО (для ТО это договоры)
            if type_document.slug == 'maintenance_service_contract':
                mlist_object = MaintenanceServiceObject.objects. \
                    filter(MaintenanceServiceContract=MaintenanceServiceContract.objects.get(id=item['dct']))
                for mobject in mlist_object:
                    if str == '':
                        str = mobject.AddressObject + ' (' + mobject.Price.__str__() + ' р.)'
                    else:
                        str = str + ', ' + mobject.AddressObject + ' (' + mobject.Price.__str__() + ' р.)'
        return str
    else:
        return 'Данные отсутствуют'


@register.simple_tag
def get_beginyearsaldo(year, branch_id, scompany_id):
    branch = Branch.objects.get(id=branch_id)
    scompany = ServingCompanyBranch.objects.get(id=scompany_id)

    startbalance = start_balance.objects. \
        filter(branch=branch, scompany=scompany). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    balance_period = credited_with_paid.objects. \
        filter(scompany=scompany, branch=branch,
               date_event__lt=datetime.date(int(year + 1), 1, 1)). \
        aggregate(summ=Sum('summ', output_field=FloatField()))

    if startbalance['summ'] is None:
        startbalance['summ'] = 0
    if balance_period['summ'] is None:
        balance_period['summ'] = 0

    return round(startbalance['summ'] + balance_period['summ'], 2)


@register.simple_tag()
def get_priceact(act_id, typedocument_slug):
    if typedocument_slug == 'build_service_act':
        return BuildServiceAct.objects.get(id=act_id).Price


@register.inclusion_tag('templatetags/select_client_forpayments.html')
def get_client_forpayments(payment_id, npp):
    contract = True
    payment = temp_export_bankpayments_from1C.objects.get(id=payment_id)
    branches = Branch.objects.filter(Client__in=Client.objects.filter(INN=payment.client_inn))

    if payment.contract_number:
        numcontract = payment.contract_number.lstrip(' ')
        numcontract = numcontract.rstrip(' ')
        list_branch = alldocuments_fulldata.objects.filter(Branch_id__in=branches, NumDocument__icontains=numcontract)

        if list_branch.count() == 0:
            contract = False
            list_branch = alldocuments_fulldata.objects.filter(Branch_id__in=branches)
    else:
        list_branch = alldocuments_fulldata.objects.filter(Branch_id__in=branches)
        contract = False
    return {'branches': list_branch, 'contract': contract, 'npp': npp}
