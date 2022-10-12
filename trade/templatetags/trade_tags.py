import re

from django.db.models import Q, Sum, FloatField, Count
from django import template

from base.models import Client, Branch, alldocuments_fulldata
from reference_books.models import typeinvoices, TypeDocument
from trade.models import invoice
from build_service.models import BuildServiceContract, BuildServiceAct
from maintenance_service.models import MaintenanceServiceContract
from tech_security.models import TechSecurityContract


__author__ = 'bondarenkoav'

register = template.Library()


def find_client_inn(inn, contract):
    branch_ = None
    if inn != '':
        branch = Branch.objects.filter(Client__in=Client.objects.filter(INN=inn))
        # Если филиалов больше 1, то пробуем уточнить по номеру договора
        if branch.count() > 1:
            found_contract = re.findall(r'\d{4,5}-\w+', contract)
            if found_contract:
                contract_data = alldocuments_fulldata.objects.filter(NumDocument__icontains=contract,
                                                                     Branch_id__in=branch.values_list('id'))
                if contract_data:
                    if contract_data.count > 0:
                        branch_ = Branch.objects.get(id=contract_data.Branch_id)
                    else:
                        branch_ = branch.last()
                else:
                    branch_ = branch
            else:
                branch_ = branch
        # Если филиал 1, выводим его
        elif branch.count() == 1:
            branch_ = branch
    return branch_


def find_client_name(name):
    branch_list = branch_ = []
    client_list = re.split(r' ', name, maxsplit=1)
    for client in client_list:
        if client.isalpha() and len(client) >= 4:
            branch = Branch.objects.filter(Client__in=Client.objects.filter(NameClient_full__icontains=client)).values_list('id')
            if branch:
                for item in branch:
                    branch_list.append(item[0])
    return Branch.objects.filter(id__in=branch_list)


def find_contract(contract):
    found_contract = re.findall(r'\d{4,5}-\w+', contract)
    for item in found_contract:
        contract_data = alldocuments_fulldata.objects.filter(NumDocument__icontains=item).last()
        if contract_data:
            if contract_data.TypeDocumentName == 'Договор монтажа':
                return BuildServiceContract.objects.get(id=contract_data.id)
            elif contract_data.TypeDocumentName == 'Договор технической охраны':
                return TechSecurityContract.objects.get(id=contract_data.id)
            elif contract_data.TypeDocumentName == 'Договор технического обслуживания':
                return MaintenanceServiceContract.objects.get(id=contract_data.id)


# Вывести parent расходжную накладную привязанную к договору, если есть
def find_parent_invoice(contract_data):
    invoice_ = invoice.objects.filter(parent__isnull=True, number_document=contract_data.id, Branch=contract_data.Branch)
    if invoice_:
        return invoice_.id


@register.inclusion_tag('templatetags/trade_parentinvoice_tags.html')
def trade_parentinvoice(invoice_, npp):
    num_parent_invoice = int(invoice_.parent_num_invoice.replace('УТ', ''))
    inv = invoice.objects.filter(number__endswith=num_parent_invoice,
                                 date_invoice__year=invoice_.parent_date_invoice.year,
                                 type_invoice=typeinvoices.objects.get(slug='consumption'))
    return {'parent_invoice': inv, 'npp': npp}


@register.inclusion_tag('templatetags/trade_importinvoice_tags.html')
def trade_importinvoice(invoice_, npp):
    found_branch = parent_invoice = free_parent_invoices = list_contract = []
    no_assignet = name_branch = False

    if invoice_.type_invoice == 'Реализация':
        if find_client_inn(invoice_.INN, invoice_.Contract1S):
            found_branch = find_client_inn(invoice_.INN, invoice_.Client)
        elif find_client_name(invoice_.Client):
            found_branch = find_client_name(invoice_.Client)
        elif find_contract(invoice_.Contract1S):
            found_branch = find_contract(invoice_.Contract1S)

    if found_branch:
        if invoice_.type_invoice == 'Реализация':
            if invoice_.Contract1S != '':
                found_contract = find_contract(invoice_.Contract1S)
                if found_contract:
                    found_parent_invoices = invoice.objects.filter(parent__isnull=True,
                                                                   Branch=found_contract.Branch,
                                                                   number_document=found_contract.id)
                    if found_parent_invoices:
                        parent_invoice = found_parent_invoices
                    else:
                        free_parent_invoices = invoice.objects.filter(parent__isnull=True,
                                                                      Branch=found_contract.Branch,
                                                                      number_document__isnull=True)
                        if free_parent_invoices.count() == 0:
                            list_contract = found_contract
                elif invoice_.Contract1S != 'акт':
                    list_contract = alldocuments_fulldata.objects.filter(Branch_id__in=found_branch.values_list('id'))
            else:
                no_assignet = True
        else:
            parent_invoice = invoice.objects.filter(parent__isnull=True, Branch__in=found_branch)

    return {'parent_invoice': parent_invoice, 'free_parent_invoices': free_parent_invoices,
            'list_contract': list_contract, 'no_assignet': no_assignet, 'branch_list': found_branch, 'npp': npp}


@register.filter
def get_contract_data(type_document, contract_id):
    document = TechSecurityContract.objects.none()
    if type_document == 'tech_security_contract':
        document = TechSecurityContract.objects.get(id=contract_id)
    elif type_document == 'build_service_contract':
        document = BuildServiceContract.objects.get(id=contract_id)
    elif type_document == 'maintenance_service_contract':
        document = MaintenanceServiceContract.objects.get(id=contract_id)
    if document:
        return document.NumContractInternal+'('+document.NumContractBranch+')'+' от '+document.DateConclusion.strftime("%d.%m.%Y")
    else:
        return 'ошибка получения данных'


@register.simple_tag()
def get_cost_equipment(type_document, document_id):
    if type_document and document_id:
        cost = invoice.objects.filter(type_document=TypeDocument.objects.get(slug=type_document),
                                      number_document=document_id).aggregate(Count('price'))
        return cost['price__count']
    else:
        return 'ошибка получения данных'


@register.filter
def total_invoice(invoice_id):
    list_invoice = invoice.objects.filter(Q(id=invoice_id)|Q(parent=invoice.objects.get(id=invoice_id)))
    total_invoices = list_invoice.aggregate(summ=Sum('price', output_field=FloatField()))
    summ = abs(total_invoices['summ']) if total_invoices['summ'] else 0
    return summ


@register.filter
def count_child_invoice(invoice_id):
    list_child = invoice.objects.filter(parent=invoice_id)
    return list_child.count
