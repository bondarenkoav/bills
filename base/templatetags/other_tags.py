import calendar
import re

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.template.defaultfilters import stringfilter, time

from accounting.models import credited_with_paid
from base.models import Branch, ServingCompanyBranch, ServingCompany, allviews_forsearch_addfields, Client
from build_service.models import BuildServiceContract, BuildServiceAct, BuildServiceObject
from maintenance_service.models import MaintenanceServiceContract, MaintenanceServiceAct, MaintenanceServiceObject
from reference_books.models import TypeDocument, City, App, TypesClient
from tech_security.models import TechSecurityContract, TechSecurityObject, TechSecurityContract_scan

register = template.Library()

__author__ = 'bondarenkoav'


def clear_type_client(name):
    name = name.replace('ООО', '')
    name = name.replace('ЗАО', '')
    name = name.replace('ПАО', '')
    name = name.replace('АО', '')
    name = name.replace('НП', '')
    name = name.replace('НКО', '')
    name = name.replace('НПО', '')
    name = name.replace('ТСЖ', '')
    name = name.replace('АНО', '')
    name = name.replace('"', '')
    name = name.strip()
    return name


@register.simple_tag()
def get_nameclient(branch_id):
    nameClient = typeClient = ''
    if branch_id:
        try:
            branch = Branch.objects.get(id=branch_id)
            typeClient = branch.Client.TypeClient.ShortTypeClient
            if branch.NameBranch:
                nameClient = branch.NameBranch
            else:
                if branch.Client.NameClient_short:
                    nameClient = branch.Client.NameClient_short
                else:
                    nameClient = branch.Client.NameClient_full
        except ObjectDoesNotExist:
            nameClient = 'ошибка'
    return typeClient + ' ' + nameClient


@register.simple_tag()
def get_namecity(city_id):
    return City.objects.get(id=city_id)


@register.simple_tag()
def get_typesystem_build(object_id):
    str_type = ''
    list_typeequipment = BuildServiceObject.objects.filter(pk=object_id).TypeEquipInstalled
    for item in list_typeequipment:
        if str_type == '':
            str_type = item
        else:
            str_type = str_type + ', ' + item
    return str_type


@register.simple_tag()
def get_typesystem_build(object_id):
    str_type = ''
    list_typeequipment = BuildServiceObject.objects.get(pk=object_id).TypeEquipInstalled.all()
    for item in list_typeequipment:
        if str_type == '':
            str_type = item.ShortType
        else:
            str_type = str_type + ', ' + item.ShortType
    return str_type


@register.simple_tag()
def getlist_NumContracts(branch_id):
    result = allviews_forsearch_addfields.objects.filter(pk=branch_id).values_list('Contract_internal', flat=True)
    return list(result)


@register.simple_tag()
def getlist_AddrObjects(branch_id):
    result = allviews_forsearch_addfields.objects.filter(pk=branch_id).values_list('Object_address', flat=True)
    return list(result)


@register.simple_tag()
def get_payment_build_contract(object_id):
    # appname = App.objects.filter(slug='build_service')
    typedoc = TypeDocument.objects.filter(app=App.objects.get(slug='build_service'))
    paid = credited_with_paid.objects.filter(object=object_id, type_dct__in=typedoc, summ__lt=0).aggregate(Count('summ'))
    return paid['summ__count']


@register.simple_tag()
def get_namescompany(scompany_id):
    return ServingCompanyBranch.objects.get(id=int(scompany_id)).NameBranch


@register.simple_tag()
def get_scompanybranch_name_byINNandCity(inn, city):
    try:
        return ServingCompanyBranch.objects.get(ServingCompany=ServingCompany.objects.get(INN=inn),
                                                City=City.objects.get(slug=city)).NameBranch
    except:
        return 'Ошибка получения наименования'


@register.simple_tag()
def get_phone_clean(string):
    # clear_string = re.sub(r'^?[8]', '', string)
    clear_string = string.replace('.', '')
    clear_string = clear_string.replace(',', '')
    clear_string = clear_string.replace('-', '')
    clear_string = clear_string.replace('(', '')
    clear_string = clear_string.replace(')', '')
    clear_string = re.sub(r'\s+', '', clear_string)
    return clear_string


@register.filter
def get_dct_info(id_dct, type_dct_slug):
    text = ''
    type_dct = TypeDocument.objects.get(slug=type_dct_slug)

    try:
        if type_dct.type == 'contract':
            if type_dct.app.slug == 'tech_security':
                document = TechSecurityContract.objects.get(id=id_dct)
            elif type_dct.app.slug == 'build_service':
                document = BuildServiceContract.objects.get(id=id_dct)
            elif type_dct.app.slug == 'maintenance_service':
                document = MaintenanceServiceContract.objects.get(id=id_dct)

            if document:
                text = document.TypeDocument.Name + ' №' + document.NumContractInternal.__str__() + '(' + \
                       document.NumContractBranch.__str__() + ')' + ' от ' + document.DateConclusion.strftime("%d.%m.%Y")
        else:
            if type_dct.app.slug == 'build_service':
                document = BuildServiceAct.objects.get(id=id_dct)
            elif type_dct.app.slug == 'maintenance_service':
                document = MaintenanceServiceAct.objects.get(id=id_dct)

            if document:
                text = document.TypeDocument.Name + ' №' + document.id.__str__() + ' от ' + document.DateWork.strftime(
                    "%d.%m.%Y")
    except ObjectDoesNotExist:
        pass
    return text


@register.filter
def get_obj_info(id_obj, type_dct_slug):
    text = ''
    type_dct = TypeDocument.objects.get(slug=type_dct_slug)

    if type_dct.app.slug == 'tech_security':
        object = TechSecurityObject.objects.get(id=id_obj)
        if object: text = object.NumObjectPCN + ' (' + object.AddressObject + ')'
    elif type_dct.app.slug == 'build_service':
        object = BuildServiceObject.objects.get(id=id_obj)
        if object: text = object.AddressObject + ')'
    elif type_dct.app.slug == 'maintenance_service':
        object = MaintenanceServiceObject.objects.get(id=id_obj)
        if object: text = object.AddressObject + ')'
    return text


@register.inclusion_tag('templatetags/event_table.html')
def event_tags(event):
    object = contract = []
    branch = get_nameclient(event.branch_id)

    if event.contract_id:
        if event.app.slug == 'tech_security':
            contract = TechSecurityContract.objects.get(id=event.contract_id)
            if event.object_id:
                object = TechSecurityObject.objects.get(id=event.object_id)
        elif event.app.slug == 'build_service':
            contract = BuildServiceContract.objects.get(id=event.contract_id)
            if event.object_id:
                object = BuildServiceObject.objects.get(id=event.object_id)
        elif event.app.slug == 'maintenance_service':
            contract = MaintenanceServiceContract.objects.get(id=event.contract_id)
            if event.object_id:
                object = MaintenanceServiceObject.objects.get(id=event.object_id)

    return {'event': event, 'branch': branch, 'contract': contract, 'object': object}


@register.filter
@stringfilter
def error_contracts(id, type):
    error_text = ""
    type_document = TypeDocument.objects.get(id=type)

    if type_document.slug == 'tech_security_contract':
        contract = TechSecurityContract.objects.get(id=id)
        if TechSecurityContract_scan.objects.filter(TechSecurityContract=contract):
            error_text = error_text
        else:
            error_text = error_text + 'Не приложена копия договора'

        # objects = TechSecurityObject.objects.filter(TechSecurityContract=contract)
        # for noscan in objects:
        #     if TechSecurityObject_scan.objects.filter(TechSecurityObject__in=noscan):
        #         error_text = error_text
        #     else:
        #         error_text = error_text+'<br/>Не приложена копия свидетельства на собственность '+noscan.AddressObject

        # subcontracts = TechSecuritySubContract.objects.filter(TechSecurityContract=contract)
        # for noscan in subcontracts:
        #     if TechSecuritySubContract_scan.objects.filter(TechSecurityObject__in=noscan):
        #         error_text = error_text
        #     else:
        #         error_text = error_text+'<br/>Не приложена копия доп.соглашения '+noscan.NumSubContract.__str__()

    elif type_document.slug == 'build_service_contract':
        contract = BuildServiceContract.objects.get(id=id)
        error_text = "Временно не доступно"
    elif type_document.slug == 'maintenance_service_contract':
        contract = MaintenanceServiceContract.objects.get(id=id)
        error_text = "Временно не доступно"
    else:
        error_text = "Не удалось определить тип договора"
    return error_text


@register.filter()
def to_int(value):
    return int(value)


@register.filter
def get_user_publics(user):
    if user:
        return user.last_name + ' ' + user.first_name[:1] + '.'
    else:
        return 'нет'


@register.simple_tag()
def get_count_days_of_month(year, month):
    if calendar.isleap(year) is True and month == 2:
        return calendar.mdays[month] + 1
    else:
        return calendar.mdays[month]


@register.simple_tag()
def replace_nametypedoc(name):
    name = name.replace('Договор', 'Договоры')
    name = name.replace('Акт', 'Акты')
    return name
#
#
# @register.simple_tag()
# def queryset_to_dict(qs, fields=None, exclude=None):
#     my_array=[]
#     for x in qs:
#         my_array.append(model_to_dict(x, fields=fields,exclude=exclude))
#     return my_array


@register.simple_tag()
def cut_typename_client(branch_id):
    try:
        name = get_nameclient(branch_id)
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'Индивидуальный предприниматель', 'ИП', name)
        name = re.sub(r'Общество с ограниченной ответственностью', 'ООО', name)
        name = re.sub(r'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ', 'ООО', name)
        name = re.sub(r'Акционерное общество', 'АО', name)
        return name[:50]
    except:
        return 'error'


@register.simple_tag()
def check_add_typeclient(branch_id):
    branch_data = Branch.objects.get(id=branch_id)
    if branch_data.Client.TypeClient.slug == 'businessman' and branch_data.Client.PassportSerNum:
        list_physicalperson = Branch.objects.filter(
            Client__in=Client.objects.filter(
                NameClient_full__icontains=branch_data.Client.NameClient_full,
                PassportSerNum=branch_data.Client.PassportSerNum,
                TypeClient=TypesClient.objects.get(slug='physical_person')))
        if list_physicalperson.count() == 0:
            return True

    elif branch_data.Client.TypeClient.slug == 'physical_person' and branch_data.Client.INN:
        list_businessman = Branch.objects.filter(
            Client__in=Client.objects.filter(
                INN=branch_data.Client.INN,
                TypeClient=TypesClient.objects.get(slug='businessman')))
        if list_businessman.count() == 0:
            return True
    else:
        return False