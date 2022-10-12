__author__ = 'bondarenkoav'

from django import template
from base.models import logging_sms
from base.smsc_api import SMSC
from accounting.models import credited_with_paid
from reference_books.models import StatusSecurity
from tech_security.models import TechSecurityObject, TechSecurityContract
from django.db.models import Sum, FloatField

register = template.Library()


@register.inclusion_tag('templatetags/smssend_tr.html')
def smssend_debt_data_view(branch, scompany):
    saldo_debt = []
    statussecur = StatusSecurity.objects.get(slug='active')
    saldo = credited_with_paid.objects.filter(branch=branch, scompany=scompany, type_dct=1).aggregate(
        summ=Sum('summ', output_field=FloatField()))

    cost_techsecur_object = TechSecurityObject.objects.filter(
        TechSecurityContract__in=TechSecurityContract.objects.filter(ServingCompany=scompany, Branch=branch),
        StatusSecurity=statussecur).aggregate(price=Sum('PriceNoDifferent', output_field=FloatField()))
    if cost_techsecur_object['price']:
        if saldo['summ'] > cost_techsecur_object['price'] * 2:
            saldo_debt = saldo
    # cost_physsecur_object = PhysSecurityObject.objects.filter(PhysSecurityContract=PhysSecurityContract.objects.get(ServingCompany=scompany),StatusSecurity=statussecur).aggregate(summ=Sum('summ', output_field=FloatField()))
    # cost_inkasssecur_object = InkassSecurityObject.objects.filter(InkassSecurityContract=InkassSecurityContract.objects.get(ServingCompany=scompany),StatusSecurity=statussecur).aggregate(summ=Sum('summ', output_field=FloatField()))
    # cost_maintservice_object = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=MaintenanceServiceContract.objects.get(ServingCompany=scompany),DateStart__lte=datetime.today(),Q(DateEnd__isnull=True)|Q(DateEnd__gte=datetime.today()))

    # cost_objects = cost_techsecur_object

    return {'saldo': saldo_debt, 'branch': branch}


code_status = {
    '-3': u'Сообщение не найдено',
    '-1': u'Ожидает отправки',
    '0': u'Передано оператору',
    '1': u'Доставлено абоненту',
    '2': u'Прочитано абонентом',
    '3': u'Просрочено (не доставлено)',
    '20': u'Невозможно доставить',
    '22': u'Неверный номер',
    '23': u'Запрещено',
    '24': u'Недостаточно средств',
    '25': u'Недоступный номер'
}

error_status = {
    '0': u'Нет ошибки',
    '1': u'Абонент не существует',
    '6': u'Абонент не в сети',
    '11': u'Абонент не может принять SMS-сообщение',
    '12': u'Ошибка в телефоне абонента',
    '13': u'Абонент заблокирован',
    '21': u'Нет поддержки SMS',
    '200': u'Виртуальная отправка (Режим "Тест"',
    '220': u'Переполнена очередь',
    '240': u'Абонент занят',
    '241': u'Ошибка конвертации звука',
    '242': u'Зафиксирован автоответчик',
    '243': u'Не заключен договор',
    '244': u'Рассылки запрещены',
    '245': u'Статус не получен',
    '246': u'Ограничение по времени',
    '247': u'Превышен лимит сообщений',
    '248': u'Нет маршрута',
    '249': u'Неверный формат номера',
    '250': u'Номер запрещен настройками',
    '251': u'Превышен лимит на один номер',
    '252': u'Номер запрещен',
    '253': u'Запрещено спам-фильтром',
    '254': u'Незарегистрированный sender id',
    '255': u'Отклонено оператором'
}


@register.inclusion_tag('templatetags/smsstatus.html')
def sms_status(id, phone):
    smsc = SMSC()
    result_status = smsc.get_status(id, '7%s' % phone)

    if result_status:
        logging_sms.objects.filter(sms_id=id). \
            update(status_sms=int(result_status[0]), error_code=int(result_status[2]))
        status_text = code_status.get(result_status[0])
        error_text = error_status.get(result_status[2])
        return {'status_sms': status_text, 'error_code': error_text}
    else:
        return {'error_getstatus': u'Ошибка получения статуса'}
