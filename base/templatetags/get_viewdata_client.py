from django import template
from django.db.models import Sum, FloatField, Q
from datetime import datetime

from accounting.models import start_balance, credited_with_paid, saldotoday
from base.models import Contacts, logging, action_planned, alldocuments_fulldata, UserNote
from build_service.models import BuildServiceObject, BuildServiceContract
from maintenance_service.models import MaintenanceServiceObject, MaintenanceServiceContract
from reference_books.models import TypeDocument, StatusSecurity
from tech_security.models import TechSecurityContract, TechSecurityObject
from trade.models import invoice

__author__ = 'bondarenkoav'

register = template.Library()


@register.inclusion_tag('templatetags/client_contracts_tabpane.html')
def client_viewdata_contracts(branch, list_scompany, typedocument):
    type_documents = TypeDocument.objects.get(slug=typedocument)
    list = alldocuments_fulldata.objects.filter(
        Branch_id=branch, ServingCompany_id__in=list_scompany, TypeDocument_id=type_documents.id)
    addget_url = type_documents.app.slug+':addget_contract'
    return {'type_documents': type_documents, 'documents': list, 'branch': branch, 'addget_url': addget_url}


@register.inclusion_tag('templatetags/client_acts_tabpane.html')
def client_viewdata_acts(branch, list_scompany, typedocument):
    type_documents = TypeDocument.objects.get(slug=typedocument)
    list = alldocuments_fulldata.objects.filter(
        Branch_id=branch, ServingCompany_id__in=list_scompany, TypeDocument_id=type_documents.id)
    addget_url = type_documents.app.slug+':addget_act'
    return {'type_documents': type_documents, 'documents': list, 'branch': branch, 'addget_url': addget_url}


@register.inclusion_tag('templatetags/client_trade_tabpane.html')
def client_viewdata_invoices(branch, list_scompany, typedocuments):
    type_document = invoices_not_assigned = invoices_assigned = []

    invoices = invoice.objects.filter(Branch=branch, ServingCompany__in=list_scompany)
    if typedocuments != 'not_assigned':
        type_document = TypeDocument.objects.get(slug=typedocuments)
        invoices_assigned = invoices.filter(type_document=type_document)
    else:
        invoices_not_assigned = invoices.\
            filter(Q(ServingCompany__isnull=True)|Q(type_document__isnull=True)|Q(number_document__isnull=True))
    return {'branch_id': branch.id, 'type_document': type_document,
            'invoices_assigned': invoices_assigned, 'invoices_not_assigned': invoices_not_assigned}


@register.simple_tag()
def saldo_scompany(branch_id, scompany_id):
    try:
        return saldotoday.objects.get(id=branch_id, scompany_id=scompany_id).saldo_today
    except:
        return 0


@register.inclusion_tag('templatetags/client_viewdata_client.html')
def client_viewdata_client(branch_data):
    return {'branch': branch_data}


@register.inclusion_tag('templatetags/client_viewdata_branch.html')
def client_viewdata_branch(branch_data):
    return {'branch': branch_data}


@register.inclusion_tag('templatetags/client_viewdata_bank.html')
def client_viewdata_bank(branch_data):
    return {'branch': branch_data}


@register.inclusion_tag('templatetags/client_viewdata_contacts.html')
def client_viewdata_contacts(branch_data):
    contacts_data = Contacts.objects.filter(Branch=branch_data.id)
    return {'contacts': contacts_data}


@register.inclusion_tag('templatetags/client_viewdata_usernote.html')
def client_viewdata_usernote(request, branch_data):
    info_data = UserNote.objects.filter(Branch=branch_data.id)
    return {'user_note': info_data, 'branch_id': branch_data.id, 'user': request.user}


@register.inclusion_tag('templatetags/client_inform_tabpane_events.html')
def client_viewdata_inform_tabpane_events(branch_id):
    return {'events': logging.objects.filter(branch_id=branch_id).reverse()[:5]}


@register.inclusion_tag('templatetags/client_inform_tabpane_planned.html')
def client_viewdata_inform_tabpane_planned(branch_id):
    return {'planned': action_planned.objects.filter(branch_id=branch_id).reverse()}


@register.inclusion_tag('templatetags/client_inform_tabpane_accounting.html')
def client_viewdata_inform_tabpane_accounting(branch, scompany):
    start_saldo = cur_saldo = 0
    saldo_start = start_balance.objects.filter(branch=branch,scompany=scompany).aggregate(summ=Sum('summ', output_field=FloatField()))
    saldo_cur = credited_with_paid.objects.filter(branch=branch,scompany=scompany).aggregate(summ=Sum('summ', output_field=FloatField()))
    if saldo_start['summ']:
        start_saldo = float(saldo_start['summ'])
    if saldo_cur['summ']:
        cur_saldo = float(saldo_cur['summ'])
    return {'NameBranch':scompany.NameBranch, 'sum_itogo':start_saldo + cur_saldo}


@register.simple_tag()
def get_countdocumets(branch_id, typedocument_id):
    return alldocuments_fulldata.objects.filter(Branch_id=branch_id, TypeDocument_id=typedocument_id).count()


@register.simple_tag()
def get_techsecurity_countactionobj(contract_id):
    return TechSecurityObject.objects.\
        filter(TechSecurityContract=TechSecurityContract.objects.get(id=contract_id),
               StatusSecurity=StatusSecurity.objects.get(slug='active')).count()


@register.simple_tag()
def get_techsecurity_countobj(contract_id):
    return TechSecurityObject.objects.\
        filter(TechSecurityContract=TechSecurityContract.objects.get(id=contract_id)).count()


@register.simple_tag()
def get_buildservice_countfinishedobj(contract_id):
    return BuildServiceObject.objects.\
        filter(BuildServiceContract=BuildServiceContract.objects.get(id=contract_id),
               DateEnd__lte=datetime.today()).count()


@register.simple_tag()
def get_buildservice_countobj(contract_id):
    return BuildServiceObject.objects.filter(
        BuildServiceContract=BuildServiceContract.objects.get(id=contract_id)).count()


@register.simple_tag()
def get_maintenanceservice_countactionobj(contract_id):
    return MaintenanceServiceObject.objects.\
        filter(Q(DateEnd__gte=datetime.today())|Q(DateEnd__isnull=True),
               MaintenanceServiceContract=MaintenanceServiceContract.objects.get(id=contract_id)).count()


@register.simple_tag()
def get_maintenanceservice_countobj(contract_id):
    return MaintenanceServiceObject.objects.\
        filter(MaintenanceServiceContract=MaintenanceServiceContract.objects.get(id=contract_id)).count()