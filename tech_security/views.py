# -*- coding: utf-8 -*-
import os
import sys
import locale

from datetime import datetime, timedelta
from time import strptime

from django.contrib.auth.models import User
from django.forms import formset_factory
from django.template import Template, Context
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, FloatField
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_protect
from uuslug import slugify
from django.utils.safestring import mark_safe
from django_currentuser.middleware import get_current_user

from accounting.models import credited_with_paid
from accounting.views import roundoff_accruals
from base.integration_armzayavki import add_request_return_equipment
from base.models import Branch, ServingCompany_settingsDocuments, Event, logging, ServingCompanyBranch, \
    ServingCompany_specialtools, SectionsApp
from base.numtostring import decimal2text
from base.templatetags.other_tags import get_count_days_of_month, get_nameclient
from base.views import logging_event, action_planned_base
from bills import settings
from contract_department.views import get_headtext, get_customer_details, get_executor_details, get_customer_signature, \
    get_executor_signature
from maintenance_service.models import MaintenanceServiceObject
from reference_books.models import StatusSecurity, TypeDocument
from tech_security.apps import TechSecurityAppConfig
from tech_security.models import TechSecurityContract, TechSecurityObject, TechSecurityObjectPeriodSecurity, \
    TechSecuritySubContract, TechTemplateSubContract, TechSecurityContract_scan, TechSecurityObject_scan, \
    TechTemplateOtherDocuments, TechSecurityObjectTypeEquipInstalled, TechSecurityObjectRent, \
    TechSecurityObjectPriceDifferent, TechSecurityObjectOpSoSCard
from tech_security.forms import form_contract, form_object_base, form_subcontract, form_object_rent, \
    form_object_typeequipinstalled, form_TechSecurityContract_scan, form_TechSecuritySubContract_scan, \
    form_TechSecurityObject_scan, PriceDifferentFormSet, OpSoSCardFormSet, form_copy_objects, form_groupobjects_actions, \
    ObjectsDeactivatedFormSet, ObjectsActivatedFormSet

apps_name = TechSecurityAppConfig.name


def get_price_object(object_id):
    object_data = TechSecurityObject.objects.get(id=object_id)
    user = User.objects.get(username='system')
    if object_data.ChgPriceDifferent is False:
        return object_data.PriceNoDifferent
    else:
        if datetime.today().date() < object_data.TechSecurityContract.DateTermination:
            price = TechSecurityObjectPriceDifferent.objects.\
                filter(ListMonth_id=datetime.today().month, TechSecurityObject=object_data).last()
            if price:
                return price.Price
            else:
                # запись об ошибке получения стоимости услуг
                logging_event('error_get_priceobject_permonth', None, '', apps_name, user.username,
                              'tech_security_contract', 
                              object_data.TechSecurityContract.ServingCompany, 
                              object_data.TechSecurityContract.Branch.id,
                              object_data.TechSecurityContract.id, object_data.id)
        else:
            # запись об ошибке получения стоимости услуг
            logging_event('error_get_priceobject_noactiveobject', None, '', apps_name, user.username,
                          'tech_security_contract',
                          object_data.TechSecurityContract.ServingCompany,
                          object_data.TechSecurityContract.Branch.id,
                          object_data.TechSecurityContract.id, object_data.id)


# Создание, закрытие, прерывание периодов охраны
def period_tech_security(object, date, code_event, old_summ, new_summ):
    # если это постановка
    if Event.objects.get(slug='change_activationSecur_object') == code_event:
        # начинаем новый период
        if old_summ is None:
            if get_price_object(object.id):
                old_summ = get_price_object(object.id)
            else:
                old_summ = 0
        TechSecurityObjectPeriodSecurity.objects.create(TechSecurityObject=object, DateStart=date,
                                                        PeriodPrice=old_summ, event_code=code_event)

    # если это снятие
    elif Event.objects.get(slug='change_deactivationSecur_object') == code_event:
        # закрываем период
        TechSecurityObjectPeriodSecurity.objects.filter(
            TechSecurityObject=object, DateStart__lt=date, DateEnd__isnull=True, PeriodPrice=old_summ).\
            order_by('-id').update(DateEnd=date, event_code=code_event)

    # если это смена абонплаты
    elif Event.objects.get(slug='change_priceNoDifferent_object') == code_event:
        # закрываем период
        TechSecurityObjectPeriodSecurity.objects.filter(
            TechSecurityObject=object, DateStart__lt=date, DateEnd__isnull=True, PeriodPrice=old_summ
        ).order_by('-id').update(DateEnd=date - timedelta(days=1))

        # начинаем новый период
        TechSecurityObjectPeriodSecurity.objects.create(
            TechSecurityObject=object, DateStart=date, PeriodPrice=new_summ, event_code=code_event
        )


def calculation(coworker, object, document, type_document, branch, scompany, date_event, price):
    if date_event.month == datetime.today().month:
        # количество дней в текущем месяце
        count_day_ofmonth = get_count_days_of_month(datetime.today().year, datetime.today().month)

        count_days_until_end_month = (count_day_ofmonth - date_event.day) + 1
        if date_event.day == 1:
            cost = price
        else:
            cost = roundoff_accruals(branch.id, (price / count_day_ofmonth) * count_days_until_end_month)

        # Доначисляем за остаток месяца
        credited_with_paid.objects.create(object=object, dct=document, type_dct=type_document, branch=branch,
                                          scompany=scompany, date_event=date_event, summ=cost,
                                          Create_user=get_current_user())

        # запись в логи об автоматическом начислении
        logging_event('auto_calculation_cost_services_object', None, '', apps_name, coworker, 'tech_security_contract',
                      scompany, branch.id, document, object)
    else:
        if (date_event.month < 12 and date_event.month + 1 == datetime.today().month and date_event.year == datetime.today().year) or (date_event.month == 12 and datetime.today().month == 1 and date_event.year + 1 == datetime.today().year):

            # количество дней в месяце события
            count_day_ofmonth = get_count_days_of_month(date_event.year, date_event.month)
            count_days_until_end_month = (count_day_ofmonth - date_event.day) + 1

            if date_event.day == 1:
                cost = price
            else:
                cost = roundoff_accruals(branch.id, (price / count_day_ofmonth) * count_days_until_end_month)

            # Доначисляем за остаток месяца
            credited_with_paid.objects.create(object=object, dct=document, type_dct=type_document, branch=branch,
                                              scompany=scompany, date_event=date_event, summ=cost,
                                              Create_user=get_current_user())
            # запись в логи об автоматическом начислении
            logging_event('auto_calculation_cost_services_object', None, '', apps_name, coworker,
                          'tech_security_contract', scompany, branch.id, document, object)

            # Если объект ставят в охрану в следующем месяце, то он пропустил общее начисление и ему как
            # "опоздавшей овце" надо доначислить за весь текущий месяц
            credited_with_paid.objects.create(
                object=object, dct=document, type_dct=type_document, branch=branch, scompany=scompany,
                date_event=datetime.strptime(
                    '01.' + datetime.today().month.__str__() + '.' + datetime.today().year.__str__(), "%d.%m.%Y"),
                summ=price, Create_user=get_current_user())
            # запись в логи об автоматическом начислении
            logging_event('auto_calculation_cost_services_object', None, '', apps_name, coworker,
                          'tech_security_contract', scompany, branch.id, document, object)
        else:
            # запись об ошибке начисления
            logging_event('error_auto_calculation_cost', None, '', apps_name, coworker, 'tech_security_contract',
                          scompany, branch.id, document, object)


# ФУНКЦИЯ ПЕРЕРАСЧЕТА
def recalculation(coworker, object, document, type_document, branch, scompany, date_event, old_price, new_price, event):
    # количество дней в месяце события
    count_day_ofmonth = get_count_days_of_month(date_event.year, date_event.month)

    # ЕСЛИ СНИМАЕТСЯ С ОХРАНЫ
    if event == 'change_deactivationSecur_object':
        if old_price:
            if old_price > 0:

                try:
                    # Ищем начисления позже даты снятия и удаляем их
                    credited_with_paid.objects.filter(object=object, dct=document, type_dct=type_document,
                                                      date_event__gte=date_event, summ__gt=0).delete()

                    # Ищем последнее начисление для перерасчета
                    accural_last = credited_with_paid.objects.filter(object=object, dct=document, type_dct=type_document,
                                                                     date_event__month=date_event.month,
                                                                     date_event__year=date_event.year, summ__gt=0).\
                                                              order_by('date_event').last()
                    if accural_last:
                        accural_last_day = accural_last.date_event.day
                        # Если начисление не с 1 числа, то надо посчитать период охраны
                        if accural_last_day > 1:
                            count_days_secure = (date_event.day - accural_last_day) + 1
                            cost = roundoff_accruals(branch.id, (old_price / count_day_ofmonth) * count_days_secure)
                        else:
                            cost = roundoff_accruals(branch.id, (old_price / count_day_ofmonth) * date_event.day)
                        credited_with_paid.objects.filter(id=accural_last.id).update(summ=cost, Update_user=get_current_user())
                except:
                    # запись об ошибке перерасчета
                    logging_event('error_auto_recalculation_cost', None, '', apps_name, coworker, 'tech_security_contract',
                                  scompany, branch.id, document, object)
                else:
                    # запись в логи об автоматическом перерасчете
                    logging_event('auto_recalculation_cost_services_object', None, '', apps_name, coworker,
                                  'tech_security_contract', scompany, branch.id, document, object)

    # ЕСЛИ МЕНЯЕТСЯ АБОНПЛАТА
    elif event == 'change_priceNoDifferent_object':
        count_days_havepassed = date_event - timedelta(days=1)

        # считаем сумму за предыдущий период
        old_cost = roundoff_accruals(branch.id, (old_price / count_day_ofmonth) * count_days_havepassed.day)

        # количество дней в месяце смены периода
        count_day_of_month = get_count_days_of_month(datetime.today().year, datetime.today().month)

        # количество дней до конца месяца (последний день включительно)
        count_days_until_end_month = (count_day_of_month - date_event.day) + 1
        new_cost = roundoff_accruals(branch.id, (new_price / count_day_of_month) * count_days_until_end_month)

        # Если смена абонплаты с текущего месяца
        if date_event.month == datetime.today().month and date_event.year == datetime.today().year:
            try:
                # Ищем начисления позже даты прерывания периода и удаляем их
                credited_with_paid.objects.filter(object=object, dct=document, type_dct=type_document,
                                                  date_event__gt=date_event, summ__gt=0).delete()

                # Ищем последнее начисление для перерасчета
                accural_id = credited_with_paid.objects.filter(object=object, dct=document,
                                                               type_dct=type_document, summ__gt=0,
                                                               date_event__month=date_event.month,
                                                               date_event__year=date_event.year).\
                                                        order_by('date_event').last().id
                # перерасчет начисления
                if date_event.day != 1:
                    if accural_id:
                        credited_with_paid.objects.filter(id=accural_id).update(summ=old_cost,
                                                                                Update_user=get_current_user())
                else:
                    credited_with_paid.objects.filter(object=object, date_event=date_event).delete()

                # добавляем новое начисление
                credited_with_paid.objects.create(object=object, dct=document, type_dct=type_document, branch=branch,
                                                  scompany=scompany, date_event=date_event, summ=new_cost,
                                                  Create_user=get_current_user())
            except:
                # запись об ошибке перерасчета
                logging_event('error_auto_recalculation_cost', None, '', apps_name, coworker,
                              'tech_security_contract', scompany, branch.id, document, object)
            else:
                # запись в логи об автоматическом перерасчете
                logging_event('auto_recalculation_cost_services_object', None, '', apps_name, coworker,
                              'tech_security_contract', scompany, branch.id, document, object)
                # запись в логи об автоматическом начислении
                logging_event('auto_calculation_cost_services_object', None, '', apps_name, coworker,
                              'tech_security_contract', scompany, branch.id, document, object)
        else:
            # запись о невозможности смены абонплаты с прошедшего месяца
            logging_event('canceled_auto_recalculation_cost', None, '', apps_name, coworker,
                          'tech_security_contract', scompany, branch.id, document, object)


@login_required
@permission_required('tech_security.contract_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_contract(request, branch_id, contract_id=None):
    type_dct = 'tech_security_contract'
    SumPriceAllObject = SumPriceInWork = 0
    contract_data = list_objects = list_subcontract = file_scancontract = file_scanobject = []

    branch_data = Branch.objects.get(id=branch_id)
    if contract_id:
        contract_data = TechSecurityContract.objects.get(id=contract_id)

        list_objects = TechSecurityObject.objects.filter(TechSecurityContract=contract_data).order_by('CityObject')
            #.\ values('id', 'NumObjectPCN', 'TypeObject', 'NameObject', 'AddressObject', 'CityObject', 'PaymentMethods')

        list_subcontract = TechSecuritySubContract.objects.filter(TechSecurityContract=contract_data)

        SumPriceAllObject = TechSecurityObject.objects.filter(TechSecurityContract=contract_data). \
            aggregate(price=Sum('PriceNoDifferent', output_field=FloatField()))
        SumPriceInWork = TechSecurityObject.objects.filter(TechSecurityContract=contract_data, StatusSecurity=1). \
            aggregate(price=Sum('PriceNoDifferent', output_field=FloatField()))

        file_scancontract = TechSecurityContract_scan.objects.filter(TechSecurityContract=contract_data).last()
        file_scanobject = TechSecurityObject_scan.objects.filter(TechSecurityObject__in=list_objects)

    form = form_contract(request.POST or None,
                         instance=contract_id and TechSecurityContract.objects.get(id=contract_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if contract_id:
                old_data = TechSecurityContract.objects.get(id=contract_id)
                scompany_id = old_data.ServingCompany.id

                if old_data.NumContractInternal != form.cleaned_data['NumContractInternal']:
                    logging_event('change_numInternal_contract', None, old_data.NumContractInternal, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.NumContractBranch != form.cleaned_data['NumContractBranch']:
                    logging_event('change_numBranch_contract', None, old_data.NumContractBranch, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.DateConclusion != form.cleaned_data['DateConclusion']:
                    logging_event('change_dateConclusion_contract', None, old_data.DateConclusion, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.DateTermination != form.cleaned_data['DateTermination']:
                    logging_event('change_dateTermination_contract', None, old_data.DateTermination, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.TemplateDocuments != form.cleaned_data['TemplateDocuments']:
                    logging_event('change_templateDocuments_contract', None, old_data.TemplateDocuments, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.PaymentDate != form.cleaned_data['PaymentDate']:
                    logging_event('change_paymentDate_contract', None, old_data.PaymentDate, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.NameOfService != form.cleaned_data['NameOfService']:
                    logging_event('change_nameOfService_contract', None, old_data.NameOfService, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
            else:
                scompany_id = form.cleaned_data.get('ServingCompany')

            num_last_contract = ServingCompany_settingsDocuments.objects.\
                get(TypeDocument=TypeDocument.objects.get(slug='tech_security_contract'),
                    ServingCompanyBranch=scompany_id)
            NumContractInternal = str(num_last_contract.prefix_num) + str(num_last_contract.current_num + 1) + str(num_last_contract.postfix_num)

            new_contract = form.save(commit=False)
            if contract_id is None:
                new_contract.Branch = Branch.objects.get(id=branch_id)
                new_contract.NumContractInternal = NumContractInternal
                new_contract.TypeDocument = TypeDocument.objects.get(slug='tech_security_contract')
            else:
                new_contract.ServingCompany = old_data.ServingCompany
            new_contract.save()
            ServingCompany_settingsDocuments.objects.\
                filter(TypeDocument=TypeDocument.objects.get(slug='tech_security_contract'),
                       ServingCompanyBranch=scompany_id).\
                update(current_num=num_last_contract.current_num + 1)

            if contract_id is None:
                logging_event('add_contract', None, '', apps_name, request.user.username, type_dct, 
                              new_contract.ServingCompany, branch_id, contract_id)

            return redirect('tech_security:addget_contract', branch_id=new_contract.Branch.id,
                            contract_id=new_contract.id)

    return render(request, 'contract_tech_security.html', {
        'form': form,
        'form_scancontract': form_TechSecurityContract_scan,
        'form_scansubcontract': form_TechSecuritySubContract_scan,
        'form_scanobject': form_TechSecurityObject_scan,
        'branch_data': branch_data,
        'contract_data': contract_data,
        'objects': list_objects,
        'SumPriceAllObject': SumPriceAllObject,
        'SumPriceInWork': SumPriceInWork,
        'list_subcontract': list_subcontract,
        'file_scancontract': file_scancontract,
        'file_scanobject': file_scanobject,
    })


@login_required
@permission_required('tech_security.object_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_object(request, branch_id, contract_id, object_id=None):
    contract_data = TechSecurityContract.objects.get(id=contract_id)
    type_dct = TypeDocument.objects.get(slug='tech_security_contract')
    object_data = periodsecurity = events = list_pricedifferent = []

    if object_id:
        object_data = TechSecurityObject.objects.get(id=object_id)
        list_pricedifferent = TechSecurityObjectPriceDifferent.objects.filter(TechSecurityObject=object_id).\
            order_by('ListMonth__id')
        periodsecurity = TechSecurityObjectPeriodSecurity.objects.filter(TechSecurityObject=object_id)
        events = logging.objects.filter(app=SectionsApp.objects.get(slug='tech_security'),
                                        type_dct=type_dct, object_id=object_id).order_by('-id')
        rent = TechSecurityObjectRent.objects.filter(
            TechSecurityObject=TechSecurityObject.objects.get(id=object_id)).last()
        if rent:
            data_rent = {'Question_ForRent': rent.Question_ForRent, 'OwnersPremises_Name': rent.OwnersPremises_Name,
                         'OwnersPremises_Phone': rent.OwnersPremises_Phone,
                         'DateEndContractRent': rent.DateEndContractRent}
        else:
            data_rent = {'Question_ForRent': False, 'OwnersPremises_Name': "", 'OwnersPremises_Phone': "",
                         'DateEndContractRent': ""}

        typeequipinstalled = TechSecurityObjectTypeEquipInstalled.objects.\
            filter(TechSecurityObject=TechSecurityObject.objects.get(id=object_id)).last()

        if typeequipinstalled:
            data_typeequipinstalled = {'TypeEquipInstalled': typeequipinstalled.TypeEquipInstalled}
        else:
            data_typeequipinstalled = {'TypeEquipInstalled': ""}

        form_connection = OpSoSCardFormSet(queryset=TechSecurityObjectOpSoSCard.objects.
                                           filter(TechSecurityObject=object_data))

    else:
        form_connection = None
        data_rent = {'Question_ForRent': False, 'OwnersPremises_Name': "", 'OwnersPremises_Phone': "",
                     'DateEndContractRent': ""}
        data_typeequipinstalled = {'TypeEquipInstalled': ""}

    form = form_object_base(request.POST or None, instance=object_id and TechSecurityObject.objects.get(id=object_id))

    if request.POST:
        if form.is_valid():
            scompany_id = TechSecurityContract.objects.get(id=contract_id).ServingCompany.id
            if object_id is not None:
                date_event = form.cleaned_data['DateEvent']
                old_data = TechSecurityObject.objects.get(id=object_id)

                # если событие уже наступило (действия выполняемые немедленно)
                if date_event <= datetime.today().date():
                    #  смена № объекта
                    if old_data.NumObjectPCN != form.cleaned_data['NumObjectPCN']:
                        logging_event(
                            'change_numObjectPCN_object', date_event, old_data.NumObjectPCN, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany, 
                            branch_id, contract_id, object_id
                        )
                    # смена типа объекта
                    if old_data.TypeObject != form.cleaned_data.get('TypeObject'):
                        logging_event(
                            'change_typeObject_object', date_event, old_data.TypeObject, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany,
                            branch_id, contract_id, object_id
                        )
                    # смена наименования объекта
                    if old_data.NameObject != form.cleaned_data['NameObject']:
                        logging_event(
                            'change_nameObject_object', date_event, old_data.NameObject, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany,
                            branch_id, contract_id, object_id
                        )
                    # смена адреса объекта
                    if old_data.AddressObject != form.cleaned_data['AddressObject']:
                        logging_event(
                            'change_addressObject_object', date_event, old_data.AddressObject, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany,
                            branch_id, contract_id, object_id
                        )
                    # смена координат расположения объекта
                    if old_data.Coordinates != form.cleaned_data['Coordinates']:
                        logging_event(
                            'change_coordinates_object', date_event, old_data.Coordinates, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany,
                            branch_id, contract_id, object_id
                        )
                    # смена способа оплаты
                    if old_data.PaymentMethods != form.cleaned_data.get('PaymentMethods'):
                        logging_event(
                            'change_paymentMethods_object', date_event, old_data.PaymentMethods, apps_name,
                            request.user.username, type_dct.slug, contract_data.ServingCompany,
                            branch_id, contract_id, object_id
                        )
                    # смена не дифференцированной стоимости охраны
                    if old_data.PriceNoDifferent != form.cleaned_data['PriceNoDifferent']:
                        if old_data.StatusSecurity == form.cleaned_data.get('StatusSecurity'):
                            # закрываем период охраны
                            period_tech_security(
                                TechSecurityObject.objects.get(id=object_id),
                                date_event, Event.objects.get(slug='change_priceNoDifferent_object'),
                                old_data.PriceNoDifferent, form.cleaned_data['PriceNoDifferent']
                            )
                            # перерасчёт
                            recalculation(
                                request.user.username, object_id, contract_data.id, type_dct,
                                contract_data.Branch, contract_data.ServingCompany,
                                date_event, old_data.PriceNoDifferent, form.cleaned_data['PriceNoDifferent'],
                                'change_priceNoDifferent_object')
                            logging_event(
                                'change_priceNoDifferent_object', date_event, old_data.PriceNoDifferent, apps_name,
                                request.user.username, type_dct.slug,  contract_data.ServingCompany,
                                branch_id, contract_id, object_id
                            )
                    # смена состояния охраны
                    if old_data.StatusSecurity != form.cleaned_data.get('StatusSecurity'):
                        # ставим в охрану
                        if form.cleaned_data.get('StatusSecurity') == StatusSecurity.objects.get(slug='active'):
                            period_tech_security(
                                TechSecurityObject.objects.get(id=object_id),
                                date_event, Event.objects.get(slug='change_activationSecur_object'),
                                old_data.PriceNoDifferent, form.cleaned_data['PriceNoDifferent']
                            )
                            # начисление
                            if form.cleaned_data.get('ChgPriceDifferent') is False:
                                calculation(
                                    request.user.username, object_id, contract_id, type_dct,
                                    Branch.objects.get(id=branch_id),
                                            ServingCompanyBranch.objects.get(id=scompany_id),
                                            date_event, form.cleaned_data['PriceNoDifferent'])
                            else:
                                credited_with_paid.objects.create(
                                    object=object_id, dct=contract_data.id, type_dct=type_dct,
                                    branch=contract_data.Branch, scompany=contract_data.ServingCompany,
                                    date_event=datetime.strptime('01.' + datetime.today().month.__str__() + '.' + datetime.today().year.__str__(), "%d.%m.%Y"),
                                    summ=get_price_object(object_id))
                            logging_event(
                                'change_activationSecur_object', date_event, old_data.StatusSecurity, apps_name,
                                request.user.username, type_dct.slug,  contract_data.ServingCompany,
                                branch_id, contract_id, object_id
                            )
                        else:
                            # снимаем с охраны
                            # закрываем период охраны
                            period_tech_security(
                                TechSecurityObject.objects.get(id=object_id),
                                date_event, Event.objects.get(slug='change_deactivationSecur_object'),
                                get_price_object(object_id), form.cleaned_data['PriceNoDifferent']
                            )
                            # перерасчёт
                            if form.cleaned_data.get('ChgPriceDifferent') is False:
                                recalculation(
                                    request.user.username, object_id, contract_data.id, type_dct, contract_data.Branch,
                                    contract_data.ServingCompany, date_event, get_price_object(object_id),
                                    form.cleaned_data['PriceNoDifferent'], 'change_deactivationSecur_object')
                            logging_event('change_deactivationSecur_object', date_event, old_data.StatusSecurity, 
                                          apps_name, request.user.username, type_dct.slug, 
                                          contract_data.ServingCompany, branch_id, contract_id, object_id)
                            if contract_data.NotDirect is False:
                                add_request_return_equipment(contract_data.ServingCompany,
                                                             get_nameclient(contract_data.Branch.id),
                                                             form.cleaned_data['NumObjectPCN'],
                                                             form.cleaned_data['AddressObject'],
                                                             date_event, request.user.username)
                    if old_data.max_time_arrival != int(form.cleaned_data['max_time_arrival']):
                        logging_event('change_maxTimeArrival_object', date_event, old_data.max_time_arrival,
                                      apps_name, request.user.username, type_dct.slug,
                                      contract_data.ServingCompany, branch_id, contract_id, object_id)

                else:
                    # если событие еще не произошло, создаём задачу/планируем на выполнение (запланированные действия)
                    if old_data.StatusSecurity != form.cleaned_data.get('StatusSecurity'):
                        # ставим в охрану
                        if form.cleaned_data.get('StatusSecurity') == StatusSecurity.objects.get(slug='active'):
                            # если помимо постановки в охрану сменилась абонплата
                            if old_data.PriceNoDifferent != form.cleaned_data['PriceNoDifferent']:
                                action_planned_base(
                                    apps_name, date_event, Event.objects.get(
                                        slug='planned_activationSecur_and_change_priceNoDifferent_object'),
                                    form.cleaned_data['PriceNoDifferent'], branch_id, contract_id, object_id,
                                    scompany_id, request.user
                                )
                            # если только абонплата
                            else:
                                action_planned_base(
                                    apps_name, date_event, Event.objects.get(slug='planned_activationSecur_object'),
                                    '', branch_id, contract_id, object_id, scompany_id, request.user
                                )
                        # снимаем с охраны
                        elif form.cleaned_data.get('StatusSecurity') != StatusSecurity.objects.get(slug='active'):
                            action_planned_base(apps_name, date_event,
                                                Event.objects.get(slug='change_deactivationSecur_object'), '',
                                                branch_id, contract_id, object_id, scompany_id, request.user)
                        # смена абонентской платы
                        elif old_data.PriceNoDifferent != form.cleaned_data['PriceNoDifferent']:
                            action_planned_base(apps_name, date_event,
                                                Event.objects.get(slug='change_activationSecur_object'),
                                                form.cleaned_data['PriceNoDifferent'], branch_id, contract_id,
                                                object_id,
                                                scompany_id, request.user)

            new_object = form.save(commit=False)
            new_object.TechSecurityContract = TechSecurityContract.objects.get(id=contract_id)
            if object_id is None:
                new_object.StatusSecurity = StatusSecurity.objects.get(slug='noactive')
            new_object.save()

            if object_id is None:
                logging_event('add_object', None, '', apps_name, request.user.username, type_dct.slug,
                              contract_data.ServingCompany, branch_id, contract_id, new_object.id)

            return redirect('tech_security:addget_object', branch_id=branch_id, contract_id=contract_id,
                            object_id=new_object.id)

    return render(request, 'object_tech_security.html', {
        'form': form,
        'form_rent': form_object_rent(data=data_rent),
        'form_typeequipinstalled': form_object_typeequipinstalled(data=data_typeequipinstalled),
        'form_connection': form_connection,
        'contract_data': contract_data,
        'object_data': object_data,
        'periodsecurity': periodsecurity,
        'list_pricedifferent': list_pricedifferent,
        'events': events,
    })


@login_required
@csrf_protect
def objects_activate(request, contract_id):
    contract_data = TechSecurityContract.objects.get(id=contract_id)

    queryset = TechSecurityObject.objects.\
        filter(TechSecurityContract=TechSecurityContract.objects.get(id=contract_id),
               StatusSecurity=StatusSecurity.objects.get(slug='noactive'))

    if request.POST:
        formset = ObjectsActivatedFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            date_event = request.POST('date_event') # strptime(request.POST('date_event'), "%d.%m.%Y")
            objects = request.POST.getlist('sel_object')

            if date_event and objects:
                for object in objects:
                    # снимаем с охраны
                    # закрываем период охраны
                    object_data = TechSecurityObject.objects.get(id=object)
                    period_tech_security(
                        object_data, date_event, Event.objects.get(slug='change_activationSecur_object'),
                        object_data.PriceNoDifferent, object_data.PriceNoDifferent)
                    logging_event(
                        'change_activationSecur_object', date_event, object_data.StatusSecurity, apps_name,
                        request.user.username, contract_data.TypeDocument.slug, contract_data.ServingCompany,
                        contract_data.Branch.id, contract_id, object
                    )
                    # начисление
                    if object_data.ChgPriceDifferent is False:
                        calculation(
                            request.user.username, object, contract_id, contract_data.TypeDocument,
                            contract_data.Branch, contract_data.ServingCompany, date_event, object_data.PriceNoDifferent)
                    else:
                        credited_with_paid.objects.create(
                            object=object, dct=contract_data.id, type_dct=object_data.TechSecurityContract.TypeDocument,
                            branch=contract_data.Branch, scompany=contract_data.ServingCompany,
                            date_event=datetime.strptime(
                                    '01.' + datetime.today().month.__str__() + '.' + datetime.today().year.__str__(),
                                    "%d.%m.%Y"), summ=get_price_object(object))

                return redirect('addget_contract', pk={contract_data.Branch.id, contract_id})
        else:
            print(formset.errors)
    else:
        formset = ObjectsDeactivatedFormSet(queryset=queryset)

    return render(request, 'objects_groupactions.html', {
        'title': 'Постановка объектов в охрану',
        'title_area': 'Договор техохраны №%s от %s' % (contract_data.NumContractInternal, contract_data.DateConclusion),
        'title_small': 'Групповая обработка объектов',
        'formset': formset,
        'contract_data': contract_data,
        'url': reverse('tech_security:objects_activate', kwargs={'contract_id': contract_id})
    })


@login_required
@csrf_protect
def objects_deactivate(request, contract_id):
    contract_data = TechSecurityContract.objects.get(id=contract_id)

    queryset = TechSecurityObject.objects.\
        filter(TechSecurityContract=TechSecurityContract.objects.get(id=contract_id),
               StatusSecurity=StatusSecurity.objects.get(slug='active'))

    if request.POST:
        formset = ObjectsDeactivatedFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            date_event = request.POST('date_event')
            objects = request.POST.getlist('sel_object')

            if date_event and objects:
                for object in objects:
                    # снимаем с охраны
                    # закрываем период охраны
                    object_data = TechSecurityObject.objects.get(id=object)
                    period_tech_security(
                        object_data, date_event, Event.objects.get(slug='change_deactivationSecur_object'),
                        get_price_object(object), object_data.PriceNoDifferent)
                    # запись в события о снятии с охраны
                    logging_event('change_deactivationSecur_object', date_event, object_data.StatusSecurity, apps_name,
                                  request.user.username, contract_data.TypeDocument.slug,
                                  contract_data.ServingCompany, contract_data.Branch.id,
                                  object_data.TechSecurityContract.id, object_data.id)
                    # перерасчёт
                    if object_data.ChgPriceDifferent is False:
                        recalculation(request.user.username, object, contract_data.id,
                                      contract_data.TypeDocument, contract_data.Branch,
                                      contract_data.ServingCompany, date_event, get_price_object(object),
                                      object_data.PriceNoDifferent, 'change_deactivationSecur_object')

                return redirect('addget_contract', pk={contract_data.Branch.id, contract_id})
        else:
            print(formset.errors)
    else:
        formset = ObjectsDeactivatedFormSet(queryset=queryset)

    return render(request, 'objects_groupactions.html', {
        'title': 'Снятие объектов с охраны',
        'title_area': 'Договор техохраны №%s от %s' % (contract_data.NumContractInternal, contract_data.DateConclusion),
        'title_small': 'Групповая обработка объектов',
        'formset': formset,
        'contract_data': contract_data,
        'url': reverse('tech_security:objects_activate', kwargs={'contract_id': contract_id})
    })


def object_pricedifferent(request, object_id):
    old_price = ''
    object_data = TechSecurityObject.objects.get(id=object_id)
    formset = PriceDifferentFormSet(queryset=TechSecurityObjectPriceDifferent.objects.\
                                    filter(TechSecurityObject=object_id))

    if request.POST:
        formset = PriceDifferentFormSet(data=request.POST)
        for item in TechSecurityObjectPriceDifferent.objects.filter(TechSecurityObject=object_data):
            if old_price == '':
                old_price = (str(item.ListMonth.id) + '/' + str(item.Price))
            else:
                old_price = old_price + ', ' + (str(item.ListMonth.id) + '/' + str(item.Price))

        for form in formset:
            if form.is_valid():
                if form.cleaned_data.get('ListMonth'):
                    new_pricediff = form.save(commit=False)
                    new_pricediff.TechSecurityObject = object_data
                    new_pricediff.save()

        logging_event(
            'change_priceDifferent_object', datetime.today(), old_price, apps_name, request.user.username,
            'tech_security_contract', object_data.TechSecurityContract.ServingCompany,
            object_data.TechSecurityContract.Branch.id, object_data.TechSecurityContract.id, object_data.id
        )

        return redirect('tech_security:addget_object', branch_id=object_data.TechSecurityContract.Branch.id,
                        contract_id=object_data.TechSecurityContract.id, object_id=object_data.id)

    return render(request, "price_different.html", {
        'title': 'Дифференцированая стоимость услуг',
        'title_area': 'Объект %s' % object_data.NumObjectPCN,
        'title_small': 'Данные объекта охраны',
        'object_data': object_data,
        'formset': formset})


@login_required
def rent_object(request, object_id):
    object_data = TechSecurityObject.objects.get(id=object_id)

    if request.POST:
        form = form_object_rent(request.POST or None)
        if form.is_valid():
            new_rent = form.save(commit=False)
            new_rent.TechSecurityObject = TechSecurityObject.objects.get(id=object_id)
            new_rent.save()
        return redirect('tech_security:addget_object',
                        branch_id=object_data.TechSecurityContract.Branch.id,
                        contract_id=object_data.TechSecurityContract.id, object_id=object_data.id)


@login_required
def connection_object(request, object_id):
    object_data = TechSecurityObject.objects.get(id=object_id)

    if request.POST:
        formset = OpSoSCardFormSet(data=request.POST)
        for form in formset:
            if form.is_valid():
                if form.cleaned_data['SimICC']:
                    new_sim = form.save(commit=False)
                    new_sim.TechSecurityObject = object_data
                    new_sim.save()
                form.save()

    return redirect('tech_security:addget_object',
                    branch_id=object_data.TechSecurityContract.Branch.id,
                    contract_id=object_data.TechSecurityContract.id, object_id=object_data.id)


@login_required
def equip_installed_object(request, branch_id, contract_id, object_id):
    if request.POST:
        form = form_object_typeequipinstalled(request.POST or None)
        if form.is_valid():
            new_rent = form.save(commit=False)
            new_rent.TechSecurityObject = TechSecurityObject.objects.get(id=object_id)
            new_rent.save()
        return redirect('tech_security:addget_object', branch_id=branch_id, contract_id=contract_id,
                        object_id=object_id)


@login_required
@permission_required('tech_security.subcontract_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_subcontract(request, branch_id, contract_id, subcontract_id=None):
    type_dct = 'tech_security_contract'
    contract_data = TechSecurityContract.objects.get(id=contract_id)
    if subcontract_id:
        subcontract_data = TechSecuritySubContract.objects.get(id=subcontract_id)
    else:
        subcontract_data = TechSecuritySubContract.objects.none()

    form = form_subcontract(request.POST or None, contract=contract_id,
                            instance=subcontract_id and TechSecuritySubContract.objects.get(id=subcontract_id))

    if request.POST:
        if form.is_valid():
            new_subcontract = form.save(commit=False)
            new_subcontract.TechSecurityContract = contract_data
            new_subcontract.save()
            form.save_m2m()

            if subcontract_id is None:
                logging_event('add_subcontract', None, '', apps_name, request.user.username, type_dct,
                              contract_data.ServingCompany, branch_id, new_subcontract.id)

            return redirect('tech_security:addget_subcontract', branch_id=branch_id, contract_id=contract_id,
                            subcontract_id=new_subcontract.id)
        else:
            return render(request, 'subcontract_tech_security.html', {
                'form': form,
                'contract_data': contract_data,
                'subcontract_id': subcontract_data,
            })
    else:
        return render(request, 'subcontract_tech_security.html', {
            'form': form,
            'contract_data': contract_data,
            'subcontract_id': subcontract_data,
        })


@login_required
def addget_contract_pdf(request, branch_id, contract_id, file_id=None):
    if request.POST:
        file = form_TechSecurityContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = TechSecurityContract.objects.get(id=contract_id)
            upload_scan.save()
            print("Договор подтвержден сканированным документом с печатями и подписями")
            return redirect('tech_security:addget_contract', branch_id=branch_id, contract_id=contract_id)
    else:
        fname = TechSecurityContract_scan.objects.get(id=file_id).ScanFile.path
        path = os.path.join(settings.MEDIA_ROOT, fname)
        response = FileResponse(open(path, 'rb'), content_type="application/pdf")
        response["Content-Disposition"] = "filename={}".format(fname)
        return response


@login_required
def addget_subcontract_pdf(request, branch_id=None, contract_id=None, file_id=None):
    if request.POST:
        file = form_TechSecuritySubContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = TechSecurityContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return redirect('tech_security:addget_contract', branch_id=branch_id, contract_id=contract_id)
    else:
        fname = TechSecurityContract_scan.objects.get(id=file_id).ScanFile.path
        path = os.path.join(settings.MEDIA_ROOT, fname)
        response = FileResponse(open(path, 'rb'), content_type="application/pdf")
        response["Content-Disposition"] = "filename={}".format(fname)
        return response


@login_required
def upload_object_pdf(request, branch_id=None, contract_id=None, file_id=None):
    if request.POST:
        file = form_TechSecurityContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = TechSecurityContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return redirect('tech_security:addget_contract', branch_id=branch_id, contract_id=contract_id)
    else:
        fname = TechSecurityContract_scan.objects.get(id=file_id).ScanFile.path
        path = os.path.join(settings.MEDIA_ROOT, fname)
        response = FileResponse(open(path, 'rb'), content_type="application/pdf")
        response["Content-Disposition"] = "filename={}".format(fname)
        return response


@login_required
def view_contract_template(request, contract_id=None):
    i = 0
    list_objects = ''

    contract = TechSecurityContract.objects.get(id=contract_id)
    text_template = Template(TechSecurityContract.objects.get(id=contract_id).TemplateDocuments.TextTemplate)

    objects = TechSecurityObject.objects.filter(TechSecurityContract=contract)
    table_list_objects = '<table style="width:100%"><thead>' \
                         '<tr><th style="width:5%">№ п/п</th><th style="width:30%">Наименование</th>' \
                         '<th style="width:45%">Адрес</th><th style="width:20%">Время прибытия, мин</th></tr>' \
                         '</thead><tbody>'

    for object in objects:
        i = i + 1

        if object.max_time_arrival == 0:
            str_max_time_arrival = 'минимально возможное'
        else:
            str_max_time_arrival = str(object.max_time_arrival)
        row_object = '<tr><th>' + str(i) + '</th><th>' + object.NameObject + '</th><th>' + object.AddressObject + \
                     '</th><th>' + str_max_time_arrival + '</th></tr>'
        table_list_objects = table_list_objects + row_object

        if len(list_objects) == 0:
            list_objects = object.AddressObject
        else:
            list_objects = list_objects + ', ' + object.AddressObject

    table_list_objects = table_list_objects + '</tbody></table>'
    TotalPrice = objects.aggregate(price=Sum('PriceNoDifferent', output_field=FloatField()))

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
    exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')

    tags = Context({
        'NumContract': contract.NumContractInternal,
        'City': contract.ServingCompany.City,
        'DateConclusion': contract.DateConclusion.strftime('"%d" %B %Y'),
        'head_text': get_headtext(contract),
        'customer_details': get_customer_details(contract),
        'executor_details': get_executor_details(contract),
        'customer_signature': get_customer_signature(contract),
        'executor_signature': get_executor_signature(contract),
        'ServingCompanyName_short': contract.ServingCompany.ServingCompany.NameCompany_short,
        'ServingCompanyManage_name': contract.ServingCompany.ServingCompany.Management_name,
        'ServingCompanyManage_post': contract.ServingCompany.ServingCompany.Management_post,
        'BranchName': contract.Branch.NameBranch,
        'BranchManager': contract.Branch.Management_name,
        'BranchManager_short': contract.Branch.Management_name,
        'BranchManagerPost': contract.Branch.Management_post.__str__(),
        'Table_Objects': mark_safe(table_list_objects),
        'List_Objects': list_objects,
        'TotalPrice': str(TotalPrice['price']) + ' (' + decimal2text(
            int(0 if TotalPrice['price'] is None else TotalPrice['price']), int_units=int_units,
            exp_units=exp_units) + ')'
    })
    text = text_template.render(tags)
    # TechSecurityContract.objects.filter(id=contract_id).update(TextContract=text)

    return render(request, 'view_template.html', {
        'title': 'Печатная форма договора ',
        'filename': slugify(str(contract.Branch.NameBranch if contract.Branch.NameBranch is None else contract.Branch.Client.NameClient_short) + '-' + contract.NumContractInternal.__str__()),
        'contract': contract,
        'area': 'Техническая охрана',
        'title_small': 'Печать',
        'text': text}
    )


@login_required
def view_checklist_contract(request, contract_id=None):
    i = 0

    contract = TechSecurityContract.objects.get(id=contract_id)
    text_template = Template(TechTemplateOtherDocuments.objects.get(slug='checklist_contract').TextTemplate)

    objects = TechSecurityObject.objects.\
        filter(TechSecurityContract=contract).\
        order_by('StatusSecurity', 'AddressObject')

    table_list_objects = '<table style="width:100%"><thead><tr>' \
                         '<th style="width:5%">№ п/п</th>' \
                         '<th style="width:5%">Тип</th><th style="width:8%">№ ПЦН</th>' \
                         '<th style="width:20%">Наименование</th><th style="width:25%">Адрес</th>' \
                         '<th style="width:10%">Форма оплаты</th><th style="width:10%">Время прибытия, мин</th>' \
                         '<th style="width:9%">Абонентская, руб.</th><th style="width:8%">Состояние</th>' \
                         '</tr></thead><tbody>'

    for object in objects:
        i = i + 1

        if object.max_time_arrival == 0:
            str_max_time_arrival = 'минимально возможное'
        else:
            str_max_time_arrival = str(object.max_time_arrival)

        row_object = '<tr><th>' + str(i) + '</th><td>' + object.TypeObject.ShortName + '</td><td>' + \
                    object.NumObjectPCN + '</td><td>' + object.NameObject + '</td><td>' + \
                    object.AddressObject + '</td><td>' + object.PaymentMethods.ShortName + '</td><td>' + \
                    str_max_time_arrival + '</td><td>' + object.PriceNoDifferent.__str__() + '</td><td>' + \
                    object.StatusSecurity.ShortName + '</td><tr>'

        table_list_objects = table_list_objects + row_object

    table_list_objects = table_list_objects + '</tbody></table>'

    TotalPrice = objects.aggregate(price=Sum('PriceNoDifferent', output_field=FloatField()))

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
    exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')

    tags = Context({
        'CurrentDate': datetime.today().strftime('"%d" %B %Y'),
        'NumContract': contract.NumContractInternal,
        'City': contract.ServingCompany.City,
        'DateConclusion': contract.DateConclusion.strftime('"%d" %B %Y'),
        'TypeContract': contract.TemplateDocuments.NameTemplate,
        'customer_signature': get_customer_signature(contract),
        'executor_signature': get_executor_signature(contract),
        'executor_NameClient_full': contract.ServingCompany.ServingCompany.NameCompany_short,
        'customer_NameClient_full': contract.Branch.NameBranch,
        'customer_PowersOffice_name': contract.Branch.Management_name,
        'customer_ManagerPost': contract.Branch.Management_post.__str__(),
        'Table_Objects': mark_safe(table_list_objects),
        'TotalPrice': str(TotalPrice['price']) + ' (' + decimal2text(
            int(0 if TotalPrice['price'] is None else TotalPrice['price']), int_units=int_units,
            exp_units=exp_units) + ')',
        'TotalCountObjects': objects.count()
    })
    text = text_template.render(tags)
    # TechSecurityContract.objects.filter(id=contract_id).update(TextContract=text)

    return render(request, 'view_template.html', {
        'title': 'Чек-лист договора ',
        'filename': slugify(str(contract.Branch.NameBranch if contract.Branch.NameBranch is None else contract.Branch.Client.NameClient_short) + '-' + contract.NumContractInternal.__str__()),
        'contract': contract,
        'area': 'Техническая охрана',
        'title_small': 'Печать',
        'text': text}
    )


@login_required
def view_subcontract_template(request, subcontract_id=None):
    args = {}
    i = 0
    int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
    exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')

    subcontract = TechSecuritySubContract.objects.get(id=subcontract_id)
    text_template = Template(TechTemplateSubContract.objects.get(id=subcontract.Template.id).TextTemplate)

    allobjects = subcontract.TechSecurityObject.all()

    TableRowsObjects = '<table border="1" cellpadding="5" cellspacing="0" style="width:100%"><tbody>'
    ListObjects = ''
    for item in allobjects:
        i = i + 1
        if ListObjects == '':
            ListObjects = ListObjects + item.AddressObject
        else:
            ListObjects = ListObjects + ', ' + item.AddressObject
        TableRowsObjects = TableRowsObjects + '<tr><td style="width:5%; text-align: center;">' + str(
            i) + '</td><td style="width:50%; text-align:right;">' + item.NameObject + ', ' + item.AddressObject + '</td><td style="width:15%; text-align:right;">' + str(
            datetime.today().strftime("%d.%m.%y")) + '</td><td style="width:15%; text-align:right;">' + str(
            item.max_time_arrival) + ' минут</td><td style="width:15%; text-align:right;">' + str(
            item.PriceNoDifferent) + '</td></tr>'
    TableRowsObjects = TableRowsObjects + '</tbody></table>'

    TotalSumm = allobjects.aggregate(Sum('PriceNoDifferent'))  # ,output_field=FloatField())

    tags = Context({
        'NumContract': subcontract.TechSecurityContract.NumContractInternal,
        'DateConclusion': subcontract.TechSecurityContract.DateConclusion,
        'City': subcontract.TechSecurityContract.ServingCompany.ServingCompany.Address_reg,
        'NumSubContract': subcontract.NumSubContract,
        'DateSubContract': subcontract.DateSubContract,
        'ServingCompanyName_full': subcontract.TechSecurityContract.ServingCompany.ServingCompany.NameCompany_full,
        'ServingCompanyName_short': subcontract.TechSecurityContract.ServingCompany.ServingCompany.NameCompany_short,
        'ServingCompanyManage_name': subcontract.TechSecurityContract.ServingCompany.ServingCompany.Management_name,
        'ServingCompanyManage_post': subcontract.TechSecurityContract.ServingCompany.ServingCompany.Management_post,
        'ServingCompanyPowersOffice_name': subcontract.TechSecurityContract.ServingCompany.PowersOffice_name,
        'ServingCompanyPowersOffice_number': subcontract.TechSecurityContract.ServingCompany.PowersOffice_number,
        'ServingCompanyAddress_reg': subcontract.TechSecurityContract.ServingCompany.ServingCompany.Address_reg,
        'ServingCompanyAddress_post': subcontract.TechSecurityContract.ServingCompany.Address_post,
        'ServingCompanyAddress_email': subcontract.TechSecurityContract.ServingCompany.Address_email,
        'ServingCompanyBank_RaschetSchet': subcontract.TechSecurityContract.ServingCompany.Bank_RaschetSchet,
        'ServingCompanyBank_Details': subcontract.TechSecurityContract.ServingCompany.Bank_Details,
        'ServingCompanyPhone_city': subcontract.TechSecurityContract.ServingCompany.Phone_city,
        'ServingCompanyPhone_fax': subcontract.TechSecurityContract.ServingCompany.Phone_fax,
        'BranchName': subcontract.TechSecurityContract.Branch.NameBranch,
        'BranchManagement_name': subcontract.TechSecurityContract.Branch.Management_name,
        'BranchManagement_post': subcontract.TechSecurityContract.Branch.Management_post,
        'BranchAddress_reg': subcontract.TechSecurityContract.Branch.Client.Address_reg,
        'BranchAddress_post': subcontract.TechSecurityContract.Branch.Address_post,
        'BranchAddress_email': subcontract.TechSecurityContract.Branch.Address_email,
        'BranchBank_RaschetSchet': subcontract.TechSecurityContract.Branch.Bank_RaschetSchet,
        'BranchBank_Details': subcontract.TechSecurityContract.Branch.Bank_Details,
        'BranchPhone_city': subcontract.TechSecurityContract.Branch.Phone_city,
        'BranchPhone_fax': subcontract.TechSecurityContract.Branch.Phone_fax,
        'ListObjects': ListObjects,
        'GenerateRowsObjects': TableRowsObjects,
        'TotalSumm': TotalSumm["PriceNoDifferent__sum"],
        'TotalSummText': decimal2text(TotalSumm["PriceNoDifferent__sum"], int_units=int_units, exp_units=exp_units)
    })

    text = text_template.render(tags)
    args['text'] = text
    return render(request, 'view_template.html', args)


@login_required
def view_police_notification_securchanges_template(request, scompany_id=None, date_start=None, date_end=None):
    args = {}
    i = 0
    list_objects_secur_start = ''
    list_objects_secur_end = ''

    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
    specialtools = ServingCompany_specialtools.objects

    logs_secur_start = logging.objects.filter(application=apps_name, date_event__range=(date_start, date_end),
                                              event_code=Event.objects.get(slug='change_activationSecur_object'))
    for object in logs_secur_start:
        object_data = TechSecurityObject.objects.get(id=object.id)
        if object_data == '':
            string_secur_start = 'Сообщаю, что организацией ' + object_data.TechSecurityContract.ServingCompany.NameBranch + ' на основании договора ' + object_data.TechSecurityContract.NumContractBranch + ' от ' + object_data.TechSecurityContract.DateConclusion.strftime(
                '%d.%m.%Y') + 'г., заключенного с ' + object_data.TechSecurityContract.Branch.NameBranch + ' ' + object_data.TechSecurityContract.Branch.Address_reg + ' взят под охрану c ' + object.event_date.strftime(
                '%d.%m.%Y') + ' объект ' + object_data.NameObject + ' расположенный по адресу ' + object_data.AddressObject + '.\par'
            i = i + 1
            if list_objects_secur_start == '':
                list_objects_secur_start = string_secur_start
            else:
                list_objects_secur_start = list_objects_secur_start + ', ' + string_secur_start

    logs_secur_end = logging.objects.filter(application=apps_name, date_event__range=(date_start, date_end),
                                            event_code=Event.objects.get(slug='change_deactivationSecur_object'))
    for object in logs_secur_end:
        object_data = TechSecurityObject.objects.get(id=object.id)
        if object_data == '':
            string_secur_end = 'Сообщаю, что ' + object_data.TechSecurityContract.ServingCompany.NameBranch + ' с ' + object.event_date.strftime(
                '%d.%m.%Y') + ' прекратила оказание охранных услуг по договору (приказу) ' + object_data.TechSecurityContract.NumContractBranch + ' от ' + object_data.TechSecurityContract.DateConclusion.strftime(
                '%d.%m.%Y') + 'г. c ' + object_data.TechSecurityContract.Branch.NameBranch + ' по адресу: ' + object_data.NameObject + ' ' + object_data.AddressObject + '.\par'
            if list_objects_secur_end == '':
                list_objects_secur_end = string_secur_end
            else:
                list_objects_secur_end = list_objects_secur_end + ', ' + string_secur_end

    text_template = Template(
        TechTemplateOtherDocuments.objects.get(slug='police_notification_securchanges').TextTemplate)

    tags = Context({
        'CurrentYear': datetime.today().year,
        'City': scompany_data.City,
        'PoliceList_recipients': '',

        'ServingCompanyINN': scompany_data.ServingCompany.INN,
        'ServingCompanyOGRN': scompany_data.ServingCompany.OGRN,
        'ServingCompanyKPP': scompany_data.KPP,

        'ServingCompanyName_full': scompany_data.ServingCompany.NameCompany_full,
        'ServingCompanyName_short': scompany_data.ServingCompany.NameCompany_short,

        'ServingCompanyManage_name': scompany_data.Management_name,
        'ServingCompanyManage_post': scompany_data.Management_post,

        'ServingCompanyAddress_reg': scompany_data.ServingCompany.Address_reg,
        'ServingCompanyAddress_post': scompany_data.Address_post,
        'ServingCompanyAddress_email': scompany_data.Address_email,

        'ServingCompanyRHI_number': scompany_data.ServingCompany.PowersOffice_name,
        'ServingCompanyRHI_dateissue': scompany_data.ServingCompany.PowersOffice_number,
        'ServingCompanyRHI_dateend': scompany_data.ServingCompany.PowersOffice_name,
        'ServingCompanyRHI_issuedby': scompany_data.ServingCompany.PowersOffice_number,
        'ServingCompanyRHI_specialtools': scompany_data.ServingCompany.PowersOffice_number,

        'ServingCompanyPhone_city': scompany_data.Phone_city,
        'ServingCompanyPhone_fax': scompany_data.Phone_fax,
        'ServingCompanyPhone_PCN': scompany_data.Phone_PCN,

        'ListObjects_secure_start': list_objects_secur_start,
        'ListObjects_secure_end': list_objects_secur_end,
    })

    text = text_template.render(tags)
    args['text'] = text
    return render(request, 'view_template.html', args)


def copy_objects(request, contract_id):
    contract_data = TechSecurityContract.objects.get(id=contract_id)
    objects = TechSecurityObject.objects.filter(TechSecurityContract=contract_data).order_by('StatusSecurity')

    form = form_copy_objects(request.POST or None,
                             instance=contract_id and TechSecurityContract.objects.get(id=contract_id))

    if request.POST:
        if form.is_valid():
            check_values = request.POST.getlist('tag[]')
            to_contract = form.cleaned_data['to_contract']
            types_contract = TypeDocument.objects.filter(type='contract')
            id_typedoc = to_contract.TypeDocument_id

            if types_contract.get(id=id_typedoc).slug == 'tech_security_contract':
                for item in check_values:
                    object = objects.get(id=item)
                    TechSecurityObject.objects.create(
                        TechSecurityContract=to_contract,
                        NumObjectPCN=object.NumObjectPCN,
                        TypeObject=object.TypeObject,
                        NameObject=object.NameObject,
                        AddressObject=object.AddressObject,
                        CityObject=object.CityObject,
                        Coordinates=object.Coordinates,
                        PaymentMethods=object.PaymentMethods,
                        ChgPriceDifferent=object.ChgPriceDifferent,
                        PriceNoDifferent=object.PriceNoDifferent,
                        max_time_arrival=object.max_time_arrival
                    )
                    logging_event('copy_objects', None,
                                  'Из договора %s №%s' % (contract_data.TypeDocument.Name, contract_data.NumContractInternal),
                                  "tech_security", request.user.username, 'tech_security_contract',
                                  contract_data.ServingCompany, contract_data.Branch.id, to_contract.id)

            else:
                for item in check_values:
                    object = objects.get(id=item)
                    MaintenanceServiceObject.objects.create(
                        TypeObject=object.TypeObject,
                        NameObject=object.NameObject,
                        AddressObject=object.AddressObject,
                        Coordinates=object.Coordinates,
                        PaymentMethods=object.PaymentMethods,
                        Price=0,
                        DateStart=datetime.today()
                    )
                    logging_event('add_object', None,
                                  'Из договора %s №%s' % (contract_data.TypeDocument.Name, contract_data.NumContractInternal),
                                  "maintenance_service", request.user.username, 'maintenance_service_contract',
                                  contract_data.ServingCompany, contract_data.Branch.id, to_contract.id)

    return render(request, 'copy_objects_tech_security.html', {
        'title': 'Копирование объектов ',
        'form': form,
        'contract_data': contract_data,
        'object_list': objects,
    })
