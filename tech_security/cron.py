from datetime import datetime
from django.db.models import Q
from django.shortcuts import redirect

from accounting.models import credited_with_paid
from tech_security.views import calculation, recalculation, get_price_object
from base.models import action_planned, Event, Branch, ServingCompanyBranch
from base.views import logging_event
from reference_books.models import StatusSecurity, TypeDocument
from tech_security.models import TechSecurityObject
from tech_security.views import period_tech_security

__author__ = 'bondarenkoav'


# автоматическое начисление абонплаты на все объекты в охране
def cron_charge_subscription_fees_full_month():
    list_object_active = TechSecurityObject.objects.\
        filter(Q(ChgPriceDifferent=False, PriceNoDifferent__gt=0) | Q(ChgPriceDifferent=True),
               StatusSecurity=StatusSecurity.objects.get(slug='active')).\
        distinct('id')

    list_object_exclude = credited_with_paid.objects.filter(
        date_event=datetime.today().date(), object__isnull=False, summ__gt=0)

    list_object_active = list_object_active.exclude(id__in=list_object_exclude.values('object'))

    for object_item in list_object_active:
        if get_price_object(object_item.id) is not None:
            credited_with_paid.objects.create(
                object=object_item.id,
                dct=object_item.TechSecurityContract.id,
                type_dct=object_item.TechSecurityContract.TypeDocument,
                branch=object_item.TechSecurityContract.Branch,
                scompany=object_item.TechSecurityContract.ServingCompany,
                date_event=datetime.today(),
                summ=get_price_object(object_item.id),
            )


# автоматическое начисление абонплаты на все объекты в охране
def cron_charge_subscription_fees_full_month_manual(request):
    objects_active = TechSecurityObject.objects. \
        filter(Q(ChgPriceDifferent=False, PriceNoDifferent__gt=0) | Q(ChgPriceDifferent=True),
               StatusSecurity=StatusSecurity.objects.get(slug='active')).distinct('id')
    objects_exclude = credited_with_paid.objects.filter(date_event__range=('2022-10-01', '2022-10-03'), object__isnull=False)
    list_objects_filtered = objects_active.exclude(id__in=objects_exclude.values('object'))

    for item in list_objects_filtered:
        price = 0
        if item.PriceNoDifferent > 0:
            price = item.PriceNoDifferent
        else:
            price = get_price_object(item.id)
        if price:
            credited_with_paid.objects.create(
                object=item.id,
                dct=item.TechSecurityContract.id,
                type_dct=item.TechSecurityContract.TypeDocument,
                branch=item.TechSecurityContract.Branch,
                scompany=item.TechSecurityContract.ServingCompany,
                date_event=datetime.today(),
                summ=price,
            )
    return redirect('index:dashboard')


# автоматическое начисление абонплаты на один объект
def cron_charge_subscription_fees_one_object(id_object):
    object_data = TechSecurityObject.objects.get(id=id_object)

    credited_with_paid.objects.create(
        object=object_data.id,
        dct=object_data.TechSecurityContract.id,
        type_dct=TypeDocument.objects.get(slug='tech_security_contract'),
        branch=object_data.TechSecurityContract.Branch,
        scompany=object_data.TechSecurityContract.ServingCompany,
        summ=object_data.PriceNoDifferent
    )


# обработчик запланированных действий
def cron_tech_security_actions_planned():
    planned = action_planned.objects.filter(complete=False, event_date=datetime.today(), no_complete='')
    active = StatusSecurity.objects.get(slug='active')
    noactive = StatusSecurity.objects.get(slug='noactive')

    for item in planned:
        old_data = TechSecurityObject.objects.get(id=item.object_id)

        if item.event_code.slug == 'planned_activationSecur_object':
            TechSecurityObject.objects.filter(id=item.object_id).update(StatusSecurity=active)
            logging_event(item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                          old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                          item.branch_id, item.contract_id, item.object_id)
            period_tech_security(
                TechSecurityObject.objects.get(id=item.object_id),
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                old_data.PriceNoDifferent
            )
            calculation(  # начисление
                item.object_id, item.contract_id, 'tech_security_contract',
                Branch.objects.get(id=item.branch_id), ServingCompanyBranch.objects.get(id=item.scompany_id),
                item.event_date, old_data.PriceNoDifferent
            )
            logging_event(  # запись в логи об автоматическом начислении
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )

        elif item.event_code.slug == 'planned_deactivationSecur_object':
            TechSecurityObject.objects.filter(id=item.object_id).update(StatusSecurity=noactive)
            logging_event(item.event_date, Event.objects.get(slug='change_deactivationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id)
            period_tech_security(  # закрываем период охраны
                TechSecurityObject.objects.get(id=item.object_id),
                item.event_date, Event.objects.get(slug='change_deactivationSecur_object'),
                old_data.PriceNoDifferent
            )
            recalculation(  # перерасчёт
                item.object_id, item.contract_id, 'tech_security_contract',
                item.event_date, old_data.PriceNoDifferent
            )
            logging_event(  # запись в логи об автоматическом перерасчете
                item.event_date, Event.objects.get(slug='change_activationSecur_object'), old_data.StatusSecurity,
                'tech_security', old_data.TechSecurityContract.ServingCompany, item.branch_id,
                item.contract_id, item.object_id
            )

        elif item.event_code.slug == 'planned_activationSecur_and_change_priceNoDifferent_object':
            TechSecurityObject.objects.filter(id=item.object_id).update(StatusSecurity=active,
                                                                        PriceNoDifferent=float(item.event_value))
            logging_event(
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )
            logging_event(  # запись в логи
                item.event_date, Event.objects.get(slug='change_priceNoDifferent_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )
            period_tech_security(
                TechSecurityObject.objects.get(id=item.object_id),
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                float(item.event_value)
            )
            calculation(  # начисление
                item.object_id, item.contract_id, 'tech_security_contract',
                Branch.objects.get(id=item.branch_id), ServingCompanyBranch.objects.get(id=item.scompany_id),
                item.event_date, float(item.event_value)
            )
            logging_event(  # запись в логи об автоматическом начислении
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )

        elif item.event_code.slug == 'planned_change_priceNoDifferent_object':
            logging_event(  # запись в логи
                item.event_date, Event.objects.get(slug='change_deactivationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )
            period_tech_security(  # закрываем период охраны
                TechSecurityObject.objects.get(id=item.object_id),
                item.event_date, Event.objects.get(slug='change_deactivationSecur_object'),
                old_data.PriceNoDifferent
            )
            recalculation(  # перерасчёт
                item.object_id, item.contract_id, 'tech_security_contract',
                item.event_date, old_data.PriceNoDifferent
            )
            calculation(  # начисление
                item.object_id, item.contract_id, 'tech_security_contract',
                Branch.objects.get(id=item.branch_id), ServingCompanyBranch.objects.get(id=item.scompany_id),
                item.event_date, old_data.PriceNoDifferent
            )
            logging_event(  # запись в логи об автоматическом перерасчете
                item.event_date, Event.objects.get(slug='change_activationSecur_object'),
                old_data.StatusSecurity, 'tech_security', old_data.TechSecurityContract.ServingCompany,
                item.branch_id, item.contract_id, item.object_id
            )

        else:
            action_planned.objects.filter(id=item.id).update(no_complete='задание неопределено системой')
