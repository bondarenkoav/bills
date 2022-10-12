# -*- coding: utf-8 -*-

import os
import sys
import locale

from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum, FloatField
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect
from accounting.models import credited_with_paid
from base.models import Branch, ServingCompany_settingsDocuments, ServingCompanyBranch, logging, SectionsApp
from base.numtostring import decimal2text
from base.views import logging_event
from bills import settings
from build_service.apps import BuildServiceAppConfig
from contract_department.views import get_headtext, get_customer_details, get_executor_details, \
    get_customer_signature, get_executor_signature
from .models import BuildServiceObject, BuildServiceContract, BuildServiceAct, BuildServiceSubContract, \
    BuildTemplateSubContract, BuildServiceContract_scan
from .forms import form_contract_build_service, form_object_build_service, form_subcontract, form_act_build_service, \
    form_BuildServiceContract_scan, form_BuildServiceSubContract_scan
from django.template import Template, Context
from reference_books.models import TypeDocument
from trade.models import invoice

apps_name = BuildServiceAppConfig.name


def calculation_contract(user, contract, type_document, branch, scompany):
    objects = BuildServiceObject.objects.filter(BuildServiceContract=contract)
    SumPriceAllObject = objects.aggregate(price=Sum('Price', output_field=FloatField()))
    obj, created = credited_with_paid.objects.update_or_create(dct=contract.id, type_dct=type_document,
                                                               branch=branch, scompany=scompany,
                                                               defaults={'summ': float(SumPriceAllObject['price'])})
    if created:
        credited_with_paid.objects.filter(id=obj.id).update(Create_user=user)
        logging_event('auto_calculation_cost_services_object', None, '', apps_name, user,
                      'build_service_contract', scompany, branch.id, contract.id)
    else:
        credited_with_paid.objects.filter(id=obj.id).update(Update_user=user)
        logging_event('auto_recalculation_cost_services_object', None, '', apps_name, user,
                      'build_service_contract', scompany, branch.id, contract.id)


@login_required
@permission_required('build_service.contract_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_contract(request, branch_id, contract_id=None):
    type_dct = 'build_service_contract'
    SumPriceAllObject = SumPriceMounted = 0
    contract_data = objects = []

    branch_data = Branch.objects.get(id=branch_id)
    if contract_id:
        contract_data = BuildServiceContract.objects.get(id=contract_id)
        SumPriceAllObject = BuildServiceObject.objects.filter(BuildServiceContract=contract_data).aggregate(
            price=Sum('Price', output_field=FloatField()))
        SumPriceMounted = BuildServiceObject.objects.filter(BuildServiceContract=contract_data,
                                                            DateEnd__isnull=False).aggregate(
            price=Sum('Price', output_field=FloatField()))

        list_objects = BuildServiceObject.objects.filter(BuildServiceContract=contract_id)
        paginator = Paginator(list_objects, 15)
        page = request.GET.get('page')
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)

    form = form_contract_build_service(request.POST or None,
                                       instance=contract_id and BuildServiceContract.objects.get(id=contract_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if contract_id:
                old_data = BuildServiceContract.objects.get(id=contract_id)

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

                if old_data.TemplateDocuments != form.cleaned_data.get('TemplateDocuments'):
                    logging_event('change_templateDocuments_contract', None, old_data.TemplateDocuments, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.PaymentDate != form.cleaned_data['PaymentDate']:
                    logging_event('change_paymentDate_contract', None, old_data.PaymentDate, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                if old_data.NameOfService != form.cleaned_data['NameOfService']:
                    logging_event('change_nameOfService_contract', None, old_data.NameOfService, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                scompany = old_data.ServingCompany
            else:
                scompany = form.cleaned_data.get('ServingCompany')

            num_last_contract = ServingCompany_settingsDocuments.objects. \
                get(TypeDocument=TypeDocument.objects.get(slug='build_service_contract'),
                    ServingCompanyBranch=scompany)
            NumContractInternal = str(num_last_contract.prefix_num) + str(num_last_contract.current_num + 1) + str(
                num_last_contract.postfix_num)

            new_contract = form.save(commit=False)
            if contract_id is None:
                new_contract.TypeDocument = TypeDocument.objects.get(slug='build_service_contract')
                new_contract.Branch = Branch.objects.get(id=branch_id)
                new_contract.NumContractInternal = NumContractInternal
            else:
                new_contract.ServingCompany = old_data.ServingCompany
            new_contract.save()

            if contract_id is None:
                # Обновление номера следующего договора в таблице
                ServingCompany_settingsDocuments.objects. \
                    filter(TypeDocument=TypeDocument.objects.get(slug='build_service_contract'),
                           ServingCompanyBranch=scompany). \
                    update(current_num=num_last_contract.current_num + 1)
                logging_event('add_contract', None, '', apps_name, request.user.username, type_dct,
                              new_contract.ServingCompany, branch_id, new_contract.id)

            return redirect('build_service:addget_contract', branch_id=branch_id, contract_id=new_contract.id)

    return render(request, 'contract_build_service.html', {
        'form': form,
        'branch_data': branch_data,
        'contract_data': contract_data,
        'form_scancontract': form_BuildServiceContract_scan,
        'form_scansubcontract': form_BuildServiceSubContract_scan,
        'SumPriceAllObject': SumPriceAllObject,
        'SumPriceMounted': SumPriceMounted,
        'objects': objects,
        'page_add': ((objects.number - 1) * 15 if objects else 0),
    })


@login_required
@permission_required('build_service.object_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_object(request, branch_id, contract_id, object_id=None):
    contract_data = BuildServiceContract.objects.get(id=contract_id)
    type_dct = TypeDocument.objects.get(slug='build_service_contract')
    object_data = events = []

    if object_id:
        object_data = BuildServiceObject.objects.get(id=object_id)
        events = logging.objects.filter(app=SectionsApp.objects.get(slug='build_service'),
                                        type_dct=type_dct, object_id=object_id).order_by('-id')

    form = form_object_build_service(request.POST or None,
                                     instance=object_id and BuildServiceObject.objects.get(id=object_id))

    if request.POST:
        if form.is_valid():
            if object_id:
                old_data = BuildServiceObject.objects.get(id=object_id)
                # смена типа объекта
                if old_data.TypeObject != form.cleaned_data.get('TypeObject'):
                    logging_event('change_typeObject_object', None, old_data.TypeObject, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена наименования объекта
                if old_data.NameObject != form.cleaned_data['NameObject']:
                    logging_event('change_nameObject_object', None, old_data.NameObject, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена адреса объекта
                if old_data.AddressObject != form.cleaned_data['AddressObject']:
                    logging_event('change_addressObject_object', None, old_data.AddressObject, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена координат расположения объекта
                if old_data.Coordinates != form.cleaned_data['Coordinates']:
                    logging_event('change_coordinates_object', None, old_data.Coordinates, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена способа оплаты
                if old_data.PaymentMethods.id != form.cleaned_data.get('PaymentMethods'):
                    logging_event('change_paymentMethods_object', None, old_data.PaymentMethods, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена стоимости монтажа за 1 объект
                if old_data.Price != form.cleaned_data['Price']:
                    logging_event('change_priceNoDifferent_object', None, old_data.Price, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany,
                                  branch_id, contract_id, object_id)
                    # если дата окончания монтажа вносится или была внесена ранее
                    if old_data.DateEnd != None or form.cleaned_data['DateEnd'] != '':
                        # считаем сумму по договору и обновляем начисленную сумму(если начислялось ранее) или начисляем новую
                        calculation_contract(request.user, contract_data, type_dct, Branch.objects.get(id=branch_id),
                                             ServingCompanyBranch.objects.get(
                                                 id=BuildServiceContract.objects.get(id=contract_id).ServingCompany.id))
                # смена даты начала монтажа
                if old_data.DateStart != form.cleaned_data['DateStart']:
                    logging_event('change_DateStartMounting_object', None, old_data.DateStart.__str__(),
                                  apps_name, request.user.username, type_dct.slug, contract_data.ServingCompany,
                    branch_id, contract_id, object_id)
                # ввод или смена даты окончания монтажа
                if old_data.DateEnd != form.cleaned_data['DateEnd']:
                    logging_event('change_DateEndMounting_object', None, old_data.DateEnd.__str__(),
                                  apps_name, request.user.username, type_dct.slug, contract_data.ServingCompany,
                                  branch_id, contract_id, object_id)
                    # проверка начисления суммы по договору (если вводят дату окончания, надо проверить было ли
                    # начисление по этому контракту, если нет, то посчитать все объекты и начислить)
                    calculation_contract(request.user, contract_data, type_dct, Branch.objects.get(id=branch_id),
                                         ServingCompanyBranch.objects.get(
                                             id=BuildServiceContract.objects.get(id=contract_id).ServingCompany.id)
                                         )

            new_object = form.save(commit=False)
            if object_id is None:
                new_object.BuildServiceContract = BuildServiceContract.objects.get(id=contract_id)
            new_object.save()
            form.save_m2m()

            if object_id is None:
                logging_event('add_object', None, '', apps_name, request.user.username, type_dct.slug,
                              contract_data.ServingCompany, branch_id, contract_id, new_object.id)

            return redirect('build_service:addget_contract', branch_id=branch_id, contract_id=contract_id)

    return render(request, 'object_build_service.html', {
        'form': form,
        'contract_data': contract_data,
        'object_data': object_data,
        'events': events
    })


@login_required
@permission_required('build_service.act_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_act(request, branch_id, act_id=None):
    type_dct = 'build_service_act'
    act_data = parent_invoice = list_children_invoice = []
    total_invoices = 0

    if act_id:
        act_data = BuildServiceAct.objects.get(id=act_id)
        parent_invoice = invoice.objects.filter(Branch=branch_id, number_document=act_id).last()

        if parent_invoice:
            list_children_invoice = invoice.objects.filter(parent=parent_invoice)
            total_chld_invoices = list_children_invoice.aggregate(summ=Sum('price', output_field=FloatField()))
            total_invoices = float(parent_invoice.price) + float(
                0 if total_chld_invoices['summ'] is None else total_chld_invoices['summ'])

    form = form_act_build_service(request.POST or None, branch=branch_id, instance=act_id and BuildServiceAct.objects.get(id=act_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if act_id:
                old_data = BuildServiceAct.objects.get(id=act_id)

                if old_data.AddressObject != form.cleaned_data['AddressObject']:
                    logging_event('change_addressObject_object', None, old_data.AddressObject, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, act_id)

                if old_data.DateWork != form.cleaned_data['DateWork']:
                    logging_event('change_DateWork_act', None, old_data.DateWork, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)
                # смена стоимости монтажа за 1 объект
                if old_data.Price != form.cleaned_data['Price']:
                    logging_event('change_priceNoDifferent_object', None, old_data.Price, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, act_id)

                if old_data.Object != form.cleaned_data.get('TypeWork'):
                    logging_event('change_typeWork', None, old_data.Object, apps_name, request.user.username, type_dct,
                                  old_data.ServingCompany, branch_id, act_id)

                if old_data.Descriptions != form.cleaned_data['TypeWork_descript']:
                    logging_event('change_typeWork_descript', None, old_data.TypeWork_descript, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, act_id)

                if old_data.CoWorker != form.cleaned_data['CoWorker']:
                    logging_event('change_CoWorker', None, old_data.CoWorker, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)

                if old_data.Descriptions != form.cleaned_data['Descriptions']:
                    logging_event('change_description', None, old_data.Descriptions, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)

            new_act = form.save(commit=False)

            try:
                parent_invoice = form.cleaned_data['parent_invoice']
            except:
                parent_invoice = None

            if act_id:
                new_act.ServingCompany = old_data.ServingCompany
                new_act.Object = old_data.Object
                new_act.update_user = request.user
            else:
                new_act.TypeDocument = TypeDocument.objects.get(slug=type_dct)
                new_act.Branch = Branch.objects.get(id=branch_id)
                new_act.create_user = request.user
            new_act.save()
            form.save_m2m()

            # Обновим данные о накладной
            if parent_invoice:
                invoice.objects.filter(id=parent_invoice.id). \
                    update(type_document=TypeDocument.objects.get(slug=type_dct),
                           number_document=new_act.id)
            else:
                invoices = invoice.objects.filter(Branch=branch_id, number_document=new_act.id)
                if invoices.count() > 0:
                    invoice.objects.filter(id=invoices.first().id). \
                        update(type_document=None, number_document=None)

            if act_id is None:
                logging_event('add_act', None, '', apps_name, request.user.username, type_dct, new_act.ServingCompany,
                              branch_id, new_act.id)

            obj, created = credited_with_paid.objects.update_or_create(dct=new_act.id,
                                                                       date_event=new_act.datetime_add,
                                                                       type_dct=TypeDocument.objects.get(slug=type_dct),
                                                                       branch=new_act.Branch,
                                                                       scompany=new_act.ServingCompany,
                                                                       defaults={'summ': new_act.Price})
            if created:
                logging_event('auto_calculation_cost_services_act', None, '', apps_name, request.user.username,
                              type_dct, new_act.ServingCompany, branch_id, new_act.id)
            else:
                logging_event('auto_recalculation_cost_services_act', None, '', apps_name, request.user.username,
                              type_dct, new_act.ServingCompany, branch_id, new_act.id)

            return redirect('index:card_client', branch_id=branch_id)

    return render(request, 'act_build_service.html', {
        'form': form,
        'act_data': act_data,
        'branch_data': Branch.objects.get(id=branch_id),
        'invoice': parent_invoice,
        'children_invoice': list_children_invoice,
        'total_invoices': total_invoices
    })


@login_required
@permission_required('build_service.subcontract_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_subcontract(request, branch_id=None, contract_id=None, subcontract_id=None):
    contract = BuildServiceContract.objects.get(id=contract_id)

    if subcontract_id:
        subcontract_data = BuildServiceSubContract.objects.get(id=subcontract_id)
    else:
        subcontract_data = BuildServiceSubContract.objects.none()

    form = form_subcontract(request.POST or None, contract=contract_id,
                            instance=subcontract_id and BuildServiceSubContract.objects.get(id=subcontract_id))

    if request.POST:
        if form.is_valid():
            new_subcontract = form.save(commit=False)
            new_subcontract.BuildServiceContract = contract
            new_subcontract.save()
            form.save_m2m()

            if subcontract_id is None:
                logging_event('add_subcontract', None, '', apps_name, request.user.username, 'build_service_contract',
                              contract.ServingCompany, branch_id, new_subcontract.id)

            return redirect('tech_security:addget_subcontract', branch_id=branch_id, contract_id=contract_id,
                            subcontract_id=new_subcontract.id)
        else:
            render(request, 'subcontract_build_service.html', {'form': form,
                                                               'contract_data': contract,
                                                               'subcontract_data': subcontract_data})
    else:
        return render(request, 'subcontract_build_service.html', {'form': form,
                                                                  'contract_data': contract,
                                                                  'subcontract_data': subcontract_data})


def addget_contract_pdf(request, branch_id, contract_id, file_id=None):
    if request.POST:
        file = form_BuildServiceContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = BuildServiceContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return redirect('tech_security:get_contract', branch_id=branch_id, contract_id=contract_id)
    else:
        fname = BuildServiceContract_scan.objects.get(id=file_id).ScanFile.path
        path = os.path.join(settings.MEDIA_ROOT, fname)
        response = FileResponse(open(path, 'rb'), content_type="application/pdf")
        response["Content-Disposition"] = "filename={}".format(fname)
        return response


def addget_subcontract_pdf(request, branch_id=None, contract_id=None, file_id=None):
    if request.POST:
        file = form_BuildServiceSubContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = BuildServiceContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return redirect('tech_security:get_contract', branch_id=branch_id, contract_id=contract_id)
    else:
        fname = BuildServiceContract_scan.objects.get(id=file_id).ScanFile.path
        path = os.path.join(settings.MEDIA_ROOT, fname)
        response = FileResponse(open(path, 'rb'), content_type="application/pdf")
        response["Content-Disposition"] = "filename={}".format(fname)
        return response


def view_contract_template(request, branch_id, contract_id):
    str_list_objects = ''
    contract = BuildServiceContract.objects.get(id=contract_id)
    text_template = Template(BuildServiceContract.objects.get(id=contract_id).TemplateDocuments.TextTemplate)
    objects = BuildServiceObject.objects.filter(BuildServiceContract=contract)
    TotalPrice = objects.aggregate(price=Sum('Price', output_field=FloatField()))

    if objects:
        for object in objects:
            adddress = object.AddressObject
            if str_list_objects == '':
                str_list_objects = adddress
            else:
                str_list_objects = str_list_objects + ', ' + adddress

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
        'BranchManagerPost': contract.Branch.Management_post.__str__(),
        'Objects_address': str_list_objects,
        'TotalPrice': str(TotalPrice['price']) + ' (' + decimal2text(
            int(0 if TotalPrice['price'] is None else TotalPrice['price']), int_units=int_units,
            exp_units=exp_units) + ')'
    })
    return render(request, 'view_template.html', {'text': text_template.render(tags)})


def view_subcontract_template(request, branch_id=None, contract_id=None, subcontract_id=None):
    args = {}
    i = 0
    int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
    exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')

    subcontract = BuildServiceSubContract.objects.get(id=subcontract_id)
    text_template = Template(BuildTemplateSubContract.objects.get(id=subcontract.Template.id).TextTemplate)

    allobjects = subcontract.BuildServiceObject.all()

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
        'NumContract': subcontract.BuildServiceContract.NumContractInternal,
        'DateConclusion': subcontract.BuildServiceContract.DateConclusion,
        'City': subcontract.BuildServiceContract.ServingCompany.ServingCompany.Address_reg,
        'NumSubContract': subcontract.NumSubContract,
        'DateSubContract': subcontract.DateSubContract,
        'ServingCompanyName_full': subcontract.BuildServiceContract.ServingCompany.ServingCompany.NameCompany_full,
        'ServingCompanyName_short': subcontract.BuildServiceContract.ServingCompany.ServingCompany.NameCompany_short,
        'ServingCompanyManage_name': subcontract.BuildServiceContract.ServingCompany.ServingCompany.Management_name,
        'ServingCompanyManage_post': subcontract.BuildServiceContract.ServingCompany.ServingCompany.Management_post,
        'ServingCompanyPowersOffice_name': subcontract.BuildServiceContract.ServingCompany.PowersOffice_name,
        'ServingCompanyPowersOffice_number': subcontract.BuildServiceContract.ServingCompany.PowersOffice_number,
        'ServingCompanyAddress_reg': subcontract.BuildServiceContract.ServingCompany.ServingCompany.Address_reg,
        'ServingCompanyAddress_post': subcontract.BuildServiceContract.ServingCompany.Address_post,
        'ServingCompanyAddress_email': subcontract.BuildServiceContract.ServingCompany.Address_email,
        'ServingCompanyBank_RaschetSchet': subcontract.BuildServiceContract.ServingCompany.Bank_RaschetSchet,
        'ServingCompanyBank_Details': subcontract.BuildServiceContract.ServingCompany.Bank_Details,
        'ServingCompanyPhone_city': subcontract.BuildServiceContract.ServingCompany.Phone_city,
        'ServingCompanyPhone_fax': subcontract.BuildServiceContract.ServingCompany.Phone_fax,
        'BranchName': subcontract.BuildServiceContract.Branch.NameBranch,
        'BranchManagement_name': subcontract.BuildServiceContract.Branch.Management_name,
        'BranchManagement_post': subcontract.BuildServiceContract.Branch.Management_post,
        'BranchAddress_reg': subcontract.BuildServiceContract.Branch.Client.Address_reg,
        'BranchAddress_post': subcontract.BuildServiceContract.Branch.Address_post,
        'BranchAddress_email': subcontract.BuildServiceContract.Branch.Address_email,
        'BranchBank_RaschetSchet': subcontract.BuildServiceContract.Branch.Bank_RaschetSchet,
        'BranchBank_Details': subcontract.BuildServiceContract.Branch.Bank_Details,
        'BranchPhone_city': subcontract.BuildServiceContract.Branch.Phone_city,
        'BranchPhone_fax': subcontract.BuildServiceContract.Branch.Phone_fax,
        'ListObjects': ListObjects,
        'GenerateRowsObjects': TableRowsObjects,
        'TotalSumm': TotalSumm["PriceNoDifferent__sum"],
        'TotalSummText': decimal2text(TotalSumm["PriceNoDifferent__sum"], int_units=int_units, exp_units=exp_units)
    })

    text = text_template.render(tags)

    args['text'] = text
    return render(request, 'view_template.html', args)
