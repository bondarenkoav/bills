import datetime

from django.db.models import Sum, FloatField, Q
from django import template
from django_currentuser.middleware import get_current_user

from base.models import Menu, logging, SectionsApp, Event, action_planned
from accounting.models import credited_with_paid
from base.views import get_scompany_foruser
from build_service.models import BuildServiceContract
from maintenance_service.models import MaintenanceServiceObject, MaintenanceServiceContract
from tech_security.models import TechSecurityContract, TechSecurityObjectRent, TechSecurityObject

__author__ = 'bondarenkoav'

register = template.Library()


@register.inclusion_tag('templatetags/sidebar.html')
def tag_navigation():
    return {'nodes': Menu.objects.all()}


@register.inclusion_tag('templatetags/profile_menu.html')
def tag_topbar():
    return {'user': get_current_user()}


@register.simple_tag()
def get_accurals_currentmonth():
    list_scompany = get_scompany_foruser()
    credits = credited_with_paid.objects. \
        filter(scompany__in=list_scompany,
               date_event__month=datetime.datetime.today().month,
               date_event__year=datetime.datetime.today().year, summ__gt=0, payment_methods__isnull=True). \
        aggregate(summ=Sum('summ', output_field=FloatField()))
    credits = abs(credits['summ']) if credits['summ'] else 0
    return credits


@register.simple_tag()
def get_paids_currentmonth():
    list_scompany = get_scompany_foruser()
    paids = credited_with_paid.objects. \
        filter(scompany__in=list_scompany,
               date_event__month=datetime.datetime.today().month,
               date_event__year=datetime.datetime.today().year, summ__lt=0, payment_methods__isnull=False). \
        aggregate(summ=Sum('summ', output_field=FloatField()))
    paids = abs(paids['summ']) if paids['summ'] else 0
    return paids


# Количество поставленых в охрану объеков за текущий месяц
@register.simple_tag()
def get_count_ts_objectsaction_currentmonth():
    list_scompany = get_scompany_foruser()
    objects = logging.objects.\
        filter(app=SectionsApp.objects.get(slug='tech_security'),
               event_code=Event.objects.get(slug='change_activationSecur_object'),
               event_date__month=datetime.datetime.today().month,
               event_date__year=datetime.datetime.today().year,
               contract_id__in=TechSecurityContract.objects.filter(ServingCompany__in=list_scompany))\
        .distinct('object_id',)
    return int(0 if objects is None else objects.count())


# Количество снятых объеков за текущий месяц
@register.simple_tag()
def get_count_ts_objectsnoaction_currentmonth():
    list_scompany = get_scompany_foruser()
    objects = logging.objects.\
        filter(app=SectionsApp.objects.get(slug='tech_security'),
               event_code=Event.objects.get(slug='change_deactivationSecur_object'),
               event_date__month=datetime.datetime.today().month,
               event_date__year=datetime.datetime.today().year,
               contract_id__in=TechSecurityContract.objects.filter(ServingCompany__in=list_scompany))\
        .distinct('object_id',)
    return int(0 if objects is None else objects.count())


# Количество объектов в обслуживании (ТО)
@register.simple_tag()
def get_count_ms_objectsnoaction_currentmonth():
    list_scompany = get_scompany_foruser()
    objects = MaintenanceServiceObject.objects.\
        filter(Q(DateEnd__gt=datetime.datetime.today())|Q(DateEnd__isnull=True),
               DateStart__lte=datetime.datetime.today(),
               MaintenanceServiceContract__in=MaintenanceServiceContract.objects.
               filter(ServingCompany__in=list_scompany))
    return int(0 if objects is None else objects.count())


# Количество объектов в обслуживании (ТО)
@register.simple_tag()
def get_count_usersaction():
    list_scompany = get_scompany_foruser()
    objects = MaintenanceServiceObject.objects.\
        filter(Q(DateEnd__gt=datetime.datetime.today())|Q(DateEnd__isnull=True),
               DateStart__lte=datetime.datetime.today(),
               MaintenanceServiceContract__in=MaintenanceServiceContract.objects.
               filter(ServingCompany__in=list_scompany))
    return int(0 if objects is None else objects.count())


# Запланировано операций
@register.simple_tag()
def get_count_actionplanned_currentmonth():
    list_scompany = get_scompany_foruser()
    operations = action_planned.objects.filter(
        scompany_id__in=list_scompany.values('id'), event_date__gt=datetime.datetime.today().date())
    return operations.count()


# Договора с истечением срока
@register.simple_tag()
def get_count_expiringcontract_currentmonth():
    list_scompany = get_scompany_foruser()
    contracts_ts = TechSecurityContract.objects.filter(
        ServingCompany__in=list_scompany, DateTermination__gte=datetime.datetime.today().date())
    contracts_bs = BuildServiceContract.objects.filter(
        ServingCompany__in=list_scompany, DateTermination__gte=datetime.datetime.today().date())
    contracts_ms = MaintenanceServiceContract.objects.filter(
        ServingCompany__in=list_scompany, DateTermination__gte=datetime.datetime.today().date())
    contracts = int(0 if contracts_ts is None else contracts_ts.count()) + \
                int(0 if contracts_bs is None else contracts_bs.count()) + \
                int(0 if contracts_ms is None else contracts_ms.count())
    return contracts


# Объекты с истечением срока аренды
@register.simple_tag()
def get_count_ts_objectswithexpiredlease_currentmonth():
    list_scompany = get_scompany_foruser()
    objects = TechSecurityObjectRent.objects.filter(
        Question_ForRent=True,
        DateEndContractRent=datetime.datetime.today().date(),
        TechSecurityObject__in=TechSecurityObject.objects.filter(
            TechSecurityContract__in=TechSecurityContract.objects.filter(
                ServingCompany__in=list_scompany))).distinct('TechSecurityObject')
    return int(0 if objects is None else objects.count())
