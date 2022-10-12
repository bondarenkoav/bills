# -*- coding: utf-8 -*-
import sys
import locale

from django.contrib.auth.decorators import login_required
from django.core.exceptions import EmptyResultSet
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Sum, FloatField, Q
from datetime import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from base.models import Branch, ServingCompany_settingsDocuments, logging, SectionsApp
from base.numtostring import decimal2text
from base.views import logging_event
from contract_department.views import get_headtext, get_customer_details, get_executor_details, get_customer_signature, \
    get_executor_signature
from maintenance_service.apps import MaintenanceServiceAppConfig
from .models import MaintenanceServiceContract, MaintenanceServiceObject, MaintenanceServiceAct, \
    MaintenanceServiceSubContract, MaintenanceTemplateSubContract
from .forms import form_contract_maintenance_service, form_object_maintenance_service, form_subcontract, \
    form_act_maintenance_service, form_MaintenanceServiceContract_scan, form_MaintenanceServiceSubContract_scan, \
    form_copy_objects
from django.template import Template, Context
from reference_books.models import TypeDocument, City, OutputToAccounts

apps_name = MaintenanceServiceAppConfig.name


@login_required
@csrf_protect
def add_get_contract(request, branch_id, contract_id=None):
    type_dct = 'maintenance_service_contract'
    SumPriceAllObject = SumPriceServices = 0
    
    branch_data = Branch.objects.get(id=branch_id)
    if contract_id:
        contract_data = MaintenanceServiceContract.objects.get(id=contract_id)
        list_subcontract = MaintenanceServiceSubContract.objects.\
            filter(MaintenanceServiceContract=contract_data)

        SumPriceAllObject = MaintenanceServiceObject.objects.\
            filter(MaintenanceServiceContract=contract_data).\
            aggregate(price=Sum('Price', output_field=FloatField()))

        SumPriceServices = MaintenanceServiceObject.objects.\
            filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
                   DateStart__lte=datetime.today(),
                   MaintenanceServiceContract=contract_data).\
            aggregate(price=Sum('Price', output_field=FloatField()))

        list_objects = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=contract_id)

        paginator = Paginator(list_objects, 15)
        page = request.GET.get('page')
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
    else:
        contract_data = MaintenanceServiceContract.objects.none()
        objects = MaintenanceServiceObject.objects.none()
        list_subcontract = MaintenanceServiceSubContract.objects.none()

    form = form_contract_maintenance_service(request.POST or None, instance=contract_id and MaintenanceServiceContract.objects.get(id=contract_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if contract_id:
                old_data = MaintenanceServiceContract.objects.get(id=contract_id)
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
    
                if old_data.TemplateDocuments != form.cleaned_data.get('TemplateDocuments'):
                    logging_event('change_templateDocuments_contract', None, old_data.TemplateDocuments, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
    
                if old_data.PaymentDate != form.cleaned_data['PaymentDate']:
                    logging_event('change_paymentDate_contract', None, old_data.PaymentDate, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
    
                if old_data.PereodicAccrual != form.cleaned_data.get('PereodicAccrual'):
                    logging_event('change_pereodicAccrual_contract', None, old_data.PereodicAccrual, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
    
                if old_data.PereodicService != form.cleaned_data.get('PereodicService'):
                    logging_event('change_pereodicService_contract', None, old_data.PereodicService, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
    
                if old_data.NameOfService != form.cleaned_data['NameOfService']:
                    logging_event('change_nameOfService_contract', None, old_data.NameOfService, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)
            else:
                scompany_id = form.cleaned_data.get('ServingCompany')
    
            num_last_contract = ServingCompany_settingsDocuments.objects.\
                get(TypeDocument=TypeDocument.objects.get(slug='maintenance_service_contract'),
                    ServingCompanyBranch=scompany_id)
            NumContractInternal = str(num_last_contract.prefix_num)+str(num_last_contract.current_num+1)+str(num_last_contract.postfix_num)
    
            new_contract = form.save(commit=False)
            if contract_id is None:
                new_contract.TypeDocument = TypeDocument.objects.get(slug='maintenance_service_contract')
                new_contract.Branch = Branch.objects.get(id=branch_id)
                new_contract.NumContractInternal = NumContractInternal
                new_contract.PushToAccounts = OutputToAccounts.objects.get(slug='split_lines')
            else:
                new_contract.ServingCompany = old_data.ServingCompany
            new_contract.save()
            form.save_m2m()
    
            if contract_id is None:
                # Обновление номера следующего договора в таблице
                ServingCompany_settingsDocuments.objects.\
                    filter(TypeDocument=TypeDocument.objects.get(slug='maintenance_service_contract'),
                           ServingCompanyBranch=scompany_id).\
                    update(current_num=num_last_contract.current_num + 1)
                logging_event('add_contract', None, '', apps_name, request.user.username, type_dct,
                              new_contract.ServingCompany, branch_id, new_contract.id)
    
            return redirect('maintenance_service:addget_contract', branch_id=branch_id, contract_id=new_contract.id)

    return render(request, 'contract_maintenance_service.html', {
        'form': form,
        'form_scancontract': form_MaintenanceServiceContract_scan,
        'form_scansubcontract': form_MaintenanceServiceSubContract_scan,
        'branch_data': branch_data,
        'contract_data': contract_data,
        'objects': objects,
        'SumPriceAllObject': SumPriceAllObject,
        'SumPriceServices': SumPriceServices,
        'list_subcontract': list_subcontract,
        'page_add': ((objects.number-1)*15 if objects else 0),
    })


@login_required
@csrf_protect
def add_get_object(request, branch_id, contract_id, object_id=None):
    type_dct = TypeDocument.objects.get(slug='maintenance_service_contract')
    contract_data = MaintenanceServiceContract.objects.get(id=contract_id)
    object_data = events = []

    if object_id:
        object_data = MaintenanceServiceObject.objects.get(id=object_id)
        events = logging.objects.filter(app=SectionsApp.objects.get(slug='maintenance_service'),
                                        type_dct=type_dct, object_id=object_id).order_by('-id')

    form = form_object_maintenance_service(request.POST or None,
                                           instance=object_id and MaintenanceServiceObject.objects.get(id=object_id))

    if request.POST:
        if form.is_valid():
            if object_id is not None:
                old_data = MaintenanceServiceObject.objects.get(id=object_id)
                # смена типа объекта
                if old_data.TypeObject != form.cleaned_data['TypeObject']:
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
                                  contract_id, object_id
                    )
                # смена координат расположения объекта
                if old_data.Coordinates != form.cleaned_data['Coordinates']:
                    logging_event('change_coordinates_object', None, old_data.Coordinates, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена способа оплаты
                if old_data.PaymentMethods != form.cleaned_data['PaymentMethods']:
                    logging_event('change_paymentMethods_object', None, old_data.PaymentMethods, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена стоимости монтажа за 1 объект
                if old_data.Price != form.cleaned_data['Price']:
                    logging_event('change_priceNoDifferent_object', None, old_data.Price, apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # смена даты начала монтажа
                if old_data.DateStart != form.cleaned_data['DateStart']:
                    logging_event('change_DateStartService_object', None, old_data.DateStart.__str__(), apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany, branch_id,
                                  contract_id, object_id)
                # ввод или смена даты окончания монтажа
                if old_data.DateEnd != form.cleaned_data['DateEnd']:
                    logging_event('change_DateEndService_object', None, old_data.DateEnd.__str__(), apps_name,
                                  request.user.username, type_dct.slug, contract_data.ServingCompany,
                                  branch_id, contract_id, object_id)

            new_object = form.save(commit=False)
            if object_id is None:
                new_object.MaintenanceServiceContract = MaintenanceServiceContract.objects.get(id=contract_id)
                # new_object.TypeEquipInstalled = form.changed_data['TypeEquipInstalled']
            new_object.save()
            form.save_m2m()

            if object_id is None:
                logging_event('add_object', None, '', apps_name, request.user.username, type_dct.slug,
                              contract_data.ServingCompany, branch_id, contract_id, new_object.id)

            return redirect('maintenance_service:addget_object', branch_id=branch_id, contract_id=contract_id, object_id=new_object.id)

    return render(request, 'object_maintenance_service.html', {
        'form': form,
        'contract_data': contract_data,
        'object_data': object_data,
        'events': events
    })


@login_required
@csrf_protect
def add_get_act(request, branch_id, act_id=None):
    type_dct = 'maintenance_service_act'
    branch_data = Branch.objects.get(id=branch_id)

    if act_id is not None:
        act_data = MaintenanceServiceAct.objects.get(id=act_id)
    else:
        act_data = MaintenanceServiceAct.objects.none()

    form = form_act_maintenance_service(request.POST or None, branch=branch_id, instance=act_id and MaintenanceServiceAct.objects.get(id=act_id))

    if request.POST:
        if form.is_valid():
            if act_id is not None:
                old_data = MaintenanceServiceAct.objects.get(id=act_id)

                if old_data.Object != form.cleaned_data['Object']:
                    logging_event('change_Object_bd', None, old_data.Object, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)
                if old_data.DateWork != form.cleaned_data['DateWork']:
                    logging_event('change_DateWork_act', None, old_data.DateWork, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)
                if old_data.CoWorker != form.cleaned_data['CoWorker']:
                    logging_event('change_CoWorker', None, old_data.CoWorker, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)
                if old_data.Descriptions != form.cleaned_data['Descriptions']:
                    logging_event('change_description', None, old_data.Descriptions, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)

            new_act = form.save(commit=False)
            if act_id is None:
                new_act.TypeDocument = TypeDocument.objects.get(slug='maintenance_service_act')
                new_act.Branch = Branch.objects.get(id=branch_id)
                new_act.create_user = request.user
            else:
                new_act.update_user = request.user
            new_act.save()
            form.save_m2m()

            if act_id is None:
                logging_event('add_act', None, '', apps_name, request.user.username, type_dct, new_act.ServingCompany,
                              branch_id, new_act.id)
            return redirect('index:card_client', branch_id=branch_id)
        else:
            return render(request, 'act_maintenance_service.html', {'form': form,
                                                                    'branch_data': branch_data,
                                                                    'act_data': act_data})
    else:
        return render(request, 'act_maintenance_service.html', {'form': form,
                                                                'branch_data': branch_data,
                                                                'act_data': act_data})


@login_required
@csrf_protect
def add_get_subcontract(request, branch_id=None, contract_id=None, subcontract_id=None):
    type_dct = 'maintenance_service_contract'
    contract_data = MaintenanceServiceContract.objects.get(id=contract_id)

    if subcontract_id:
        subcontract_data = MaintenanceServiceSubContract.objects.get(id=subcontract_id)
    else:
        subcontract_data = MaintenanceServiceSubContract.objects.none()

    form = form_subcontract(request.POST or None, contract=contract_id, instance=subcontract_id and MaintenanceServiceSubContract.objects.get(id=subcontract_id))

    if request.POST:
        if form.is_valid():
            new_subcontract = form.save(commit=False)
            new_subcontract.MaintenanceServiceContract = contract_data
            new_subcontract.save()
            form.save_m2m()

            if subcontract_id is None:
                logging_event('add_subcontract', None, '', apps_name, request.user.username, type_dct,
                              contract_data.ServingCompany, branch_id, new_subcontract.id)

            return redirect('maintenance_service:addget_subcontract', branch_id=branch_id, contract_id=contract_id, subcontract_id=new_subcontract.id)
        else:
            return render(request, 'subcontract_maintenance_service.html', {'form':form,
                                                                            'contract_data': contract_data,
                                                                            'subcontract_data': subcontract_data})
    else:
        return render(request, 'subcontract_maintenance_service.html', {'form':form,
                                                                        'contract_data': contract_data,
                                                                        'subcontract_data': subcontract_data})


def upload_contract_pdf(request, branch_id=None, contract_id=None):
    if request.method=="POST":
        file = form_MaintenanceServiceContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = MaintenanceServiceContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return HttpResponseRedirect(reverse('tech_security:add&get_contract', args=[branch_id,contract_id]))


def upload_subcontract_pdf(request, branch_id=None, contract_id=None):
    if request.method=="POST":
        file = form_MaintenanceServiceContract_scan(request.POST, request.FILES)
        if file.is_valid():
            upload_scan = file.save(commit=False)
            upload_scan.TechSecurityContract = MaintenanceServiceContract.objects.get(id=contract_id)
            upload_scan.save()

            print("Договор подтвержден сканированным документом с печатями и подписями")
            return HttpResponseRedirect(reverse('tech_security:add&get_contract', args=[branch_id,contract_id]))


@login_required
def view_contract_template(request, branch_id, contract_id):
    list_objects = ''
    i = 0
    contract = MaintenanceServiceContract.objects.get(id=contract_id)
    text_template = Template(MaintenanceServiceContract.objects.get(id=contract_id).TemplateDocuments.TextTemplate)
    objects = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=contract)
    TotalPrice = objects.aggregate(price=Sum('Price',output_field=FloatField()))

    if objects:
        for object in objects:
            i = i+1
            str_list_type_ei = ''
            for type_ei in object.TypeEquipInstalled.all():
                if str_list_type_ei == '':
                    str_list_type_ei = type_ei.ShortType
                else:
                    str_list_type_ei = str_list_type_ei+', '+type_ei.ShortType

            adddress = object.NameObject + ' ' + object.AddressObject
            str_list_objects = '<tr><th>%d</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (i, adddress, object.Price.__str__(), object.DateStart.strftime("%d.%m.%Y"), str_list_type_ei, object.MaintenanceServiceContract.PereodicAccrual)
            if list_objects == '':
                list_objects = str_list_objects
            else:
                list_objects = list_objects+str_list_objects

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
        'Phone_stat': contract.ServingCompany.Phone_city+', '+contract.ServingCompany.Phone_PCN,
        'Phone_fax': contract.ServingCompany.Phone_fax,
        'Address_email': contract.ServingCompany.Address_email,
        'BranchName': contract.Branch.NameBranch,
        'BranchManager': contract.Branch.Management_name,
        'BranchManagerPost': contract.Branch.Management_post.__str__(),
        'Objects_address': list_objects,
        'PeriodicAccrual': contract.PereodicAccrual,
        'PereodicService': contract.PereodicService,
        'TotalPrice': str(TotalPrice['price'])+ ' ('+decimal2text(int(0 if TotalPrice['price'] is None else TotalPrice['price']), int_units=int_units, exp_units=exp_units)+')'
    })
    return render(request, 'view_template.html', {'text': text_template.render(tags)})


@login_required
def view_subcontract_template(request, subcontract_id=None):
    i=0
    int_units = ((u'рубль', u'рубля', u'рублей'), 'm')
    exp_units = ((u'копейка', u'копейки', u'копеек'), 'f')

    subcontract = MaintenanceServiceSubContract.objects.get(id=subcontract_id)
    text_template = Template(MaintenanceTemplateSubContract.objects.get(id=subcontract.Template.id).TextTemplate)

    allobjects = subcontract.MaintenanceServiceObject.all()

    TableRowsObjects = '<table border="1" cellpadding="5" cellspacing="0" style="width:100%"><tbody>'
    ListObjects = ''
    for item in allobjects:
        i = i+1
        if ListObjects == '':
            ListObjects = ListObjects+item.AddressObject
        else:
            ListObjects = ListObjects+', '+item.AddressObject
        TableRowsObjects = TableRowsObjects+'<tr><td style="width:5%; text-align: center;">'+str(i)+'</td><td style="width:50%; text-align:right;">'+item.NameObject+', '+item.AddressObject+'</td><td style="width:15%; text-align:right;">'+str(datetime.today().strftime("%d.%m.%y"))+'</td><td style="width:15%; text-align:right;">'+str(item.max_time_arrival)+' минут</td><td style="width:15%; text-align:right;">'+str(item.PriceNoDifferent)+'</td></tr>'
    TableRowsObjects = TableRowsObjects+'</tbody></table>'

    TotalSumm = allobjects.aggregate(Sum('PriceNoDifferent'))

    tags = Context({
        'NumContract': subcontract.MaintenanceServiceContract.NumContractInternal,
        'DateConclusion': subcontract.MaintenanceServiceContract.DateConclusion,
        'City': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.Address_reg,
        'NumSubContract': subcontract.NumSubContract,
        'DateSubContract': subcontract.DateSubContract,
        'ServingCompanyName_full': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.NameCompany_full,
        'ServingCompanyName_short': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.NameCompany_short,
        'ServingCompanyManage_name': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.Management_name,
        'ServingCompanyManage_post': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.Management_post,
        'ServingCompanyPowersOffice_name': subcontract.MaintenanceServiceContract.ServingCompany.PowersOffice_name,
        'ServingCompanyPowersOffice_number': subcontract.MaintenanceServiceContract.ServingCompany.PowersOffice_number,
        'ServingCompanyAddress_reg': subcontract.MaintenanceServiceContract.ServingCompany.ServingCompany.Address_reg,
        'ServingCompanyAddress_post': subcontract.MaintenanceServiceContract.ServingCompany.Address_post,
        'ServingCompanyAddress_email': subcontract.MaintenanceServiceContract.ServingCompany.Address_email,
        'ServingCompanyBank_RaschetSchet': subcontract.MaintenanceServiceContract.ServingCompany.Bank_RaschetSchet,
        'ServingCompanyBank_Details': subcontract.MaintenanceServiceContract.ServingCompany.Bank_Details,
        'ServingCompanyPhone_city': subcontract.MaintenanceServiceContract.ServingCompany.Phone_city,
        'ServingCompanyPhone_fax': subcontract.MaintenanceServiceContract.ServingCompany.Phone_fax,
        'BranchName': subcontract.MaintenanceServiceContract.Branch.NameBranch,
        'BranchManagement_name': subcontract.MaintenanceServiceContract.Branch.Management_name,
        'BranchManagement_post': subcontract.MaintenanceServiceContract.Branch.Management_post,
        'BranchAddress_reg': subcontract.MaintenanceServiceContract.Branch.Client.Address_reg,
        'BranchAddress_post': subcontract.MaintenanceServiceContract.Branch.Address_post,
        'BranchAddress_email': subcontract.MaintenanceServiceContract.Branch.Address_email,
        'BranchBank_RaschetSchet': subcontract.MaintenanceServiceContract.Branch.Bank_RaschetSchet,
        'BranchBank_Details': subcontract.MaintenanceServiceContract.Branch.Bank_Details,
        'BranchPhone_city': subcontract.MaintenanceServiceContract.Branch.Phone_city,
        'BranchPhone_fax': subcontract.MaintenanceServiceContract.Branch.Phone_fax,
        'ListObjects': ListObjects,
        'GenerateRowsObjects': TableRowsObjects,
        'TotalSumm': TotalSumm["PriceNoDifferent__sum"],
        'TotalSummText': decimal2text(TotalSumm["PriceNoDifferent__sum"], int_units=int_units, exp_units=exp_units)
    })
    return render(request, 'view_template.html', {'text': text_template.render(tags)})


def copy_objects(request, contract_id):
    new_object = []
    contract_data = MaintenanceServiceContract.objects.get(id=contract_id)
    objects = MaintenanceServiceObject.objects.filter(MaintenanceServiceContract=contract_data).order_by('DateEnd')

    form = form_copy_objects(request.POST or None,
                             instance=contract_id and MaintenanceServiceContract.objects.get(id=contract_id))
    if request.POST:
        if form.is_valid():
            check_values = request.POST.getlist('tag[]')

            to_contract = form.cleaned_data['to_contract']
            types_contract = TypeDocument.objects.filter(type='contract')
            id_typedoc = to_contract.TypeDocument_id

            if types_contract.get(id=id_typedoc).slug == 'maintenance_service_contract':
                for item in check_values:
                    object_item = objects.get(id=item)
                    new_object = MaintenanceServiceObject.objects.create(
                        MaintenanceServiceContract=MaintenanceServiceContract.objects.get(pk=to_contract.id),
                        TypeObject=object_item.TypeObject,
                        NameObject=object_item.NameObject,
                        AddressObject=object_item.AddressObject,
                        CityObject=object_item.CityObject,
                        Coordinates=object_item.Coordinates,
                        PaymentMethods=object_item.PaymentMethods,
                        Price=object_item.Price,
                        DateStart=datetime.now()
                    )
                    for item in object_item.TypeEquipInstalled.all():
                        new_object.TypeEquipInstalled.add(item)

                    logging_event('copy_objects', None,
                                  'Из договора %s №%s' % (contract_data.TypeDocument.Name,
                                                          contract_data.NumContractInternal),
                                  "maintenance_service", request.user.username, 'maintenance_service_contract',
                                  contract_data.ServingCompany, contract_data.Branch.id, to_contract.id)

                return redirect('maintenance_service:addget_contract', branch_id=contract_data.Branch.id,
                                contract_id=new_object.MaintenanceServiceContract.id)

            else:
                for item in check_values:
                    object = objects.get(id=item)
                    new_object = MaintenanceServiceObject.objects.create(
                        TypeObject=object.TypeObject,
                        NameObject=object.NameObject,
                        AddressObject=object.AddressObject,
                        Coordinates=object.Coordinates,
                        PaymentMethods=object.PaymentMethods,
                        Price=0,
                        DateStart=datetime.now()
                    )
                    logging_event('add_object', None,
                                  'Из договора %s №%s' % (contract_data.TypeDocument.Name, contract_data.NumContractInternal),
                                  "maintenance_service", request.user.username, 'maintenance_service_contract',
                                  contract_data.ServingCompany, contract_data.Branch.id, to_contract.id)

                return redirect('tech_security:addget_contract', branch_id=contract_data.Branch.id,
                                contract_id=new_object.TechSecurityContract.id)

    return render(request, 'copy_objects_maintenance_service.html', {
        'title': 'Копирование объектов ',
        'form': form,
        'contract_data': contract_data,
        'object_list': objects,
    })
