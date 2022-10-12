from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from account.models import Profile
from base.models import Branch, alldocuments_fulldata
from reference_books.models import typeinvoices, TypeDocument
from trade.forms import form_invoice, form_invoices_period
from trade.models import invoice, import_invoices


@login_required()
@csrf_protect
def get_invoices_period(request):
    form = form_invoices_period(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany_data = form.cleaned_data['scompany']
            filter_start_date = form.cleaned_data['filter_start_date']
            filter_end_date = form.cleaned_data['filter_end_date']
            if filter_end_date is None:
                filter_end_date = filter_start_date

            invoices = invoice.objects.filter(ServingCompany=scompany_data,
                                              date_add__date__gte=filter_start_date,
                                              date_add__date__lte=filter_end_date)
            return render(request, 'journal/invoices_period.html', {'form': form,
                                                                    'list': invoices})
    else:
        return render(request, 'journal/invoices_period.html', {'form': form})


# Не закрытые накладные
@login_required()
def get_invoices_notrepaid(request):
    paginator = Paginator(invoice.objects.filter(parent__isnull=True, number_document__isnull=True).order_by('date_add'), 20)
    page = request.GET.get('page')
    try:
        invoice_list = paginator.page(page)
    except PageNotAnInteger:
        invoice_list = paginator.page(1)
    except EmptyPage:
        invoice_list = paginator.page(paginator.num_pages)

    return render(request, 'journal/invoices_notrepaid.html', {
        'title': u'Не закрытые накладные',
        'area': u'Склад',
        'list': invoice_list,
        'page': page
    })


@login_required()
@csrf_protect
def add_get_invoice_trade(request, branch_id, invoice_id=None):
    invoice_data = num_document = []
    if invoice_id:
        invoice_data = invoice.objects.get(id=int(invoice_id))
        num_document = invoice_data.number_document

    form = form_invoice(request.POST or None, branch=branch_id, document=num_document,
                        instance=invoice_id and invoice.objects.get(id=invoice_id))

    if request.POST:
        if form.is_valid():
            type_invoice = form.cleaned_data.get('type_invoice')
            summ = form.cleaned_data['price']
            new_invoice = form.save(commit=False)
            new_invoice.Branch = Branch.objects.get(id=int(branch_id))
            if type_invoice.slug == 'refund' and summ > 0:
                new_invoice.price = summ*(-1)
            new_invoice.save()
            form.save_m2m()
            return redirect('index:card_client', branch_id=branch_id)
    else:
        return render(request, 'trade_invoice.html', {
            'form': form,
            'invoice_data': invoice_data,
            'children_invoices': invoice.objects.filter(parent=invoice_id).order_by('date_add'),
            'branch_data': Branch.objects.get(id=branch_id),
        })


@login_required()
@csrf_protect
def import_invoices_from_1S(request):
    new_invoice = []
    scompany_default = Profile.objects.get(user=request.user).scompany_default
    if scompany_default is None:
        return redirect('page_error403')
    invoices = import_invoices.objects.filter(city=scompany_default.City.slug)

    if request.POST:
        for i, invoices_item in enumerate(invoices):
            if request.POST['client_' + (i + 1).__str__()] != 'none':
                type_docum = request.POST['client_' + (i + 1).__str__()]

                if invoices_item.type_invoice == 'Возврат':
                    if invoices_item.price > 0:
                        summ = invoices_item.price * (-1)
                    else:
                        summ = invoices_item.price

                    type_invoice = typeinvoices.objects.get(slug='refund')
                    parent_id = type_docum.split('-')[1]
                    parent_invoice = invoice.objects.get(id=parent_id)
                    new_invoice = invoice.objects.create(ServingCompany=parent_invoice.ServingCompany,
                                                         Branch=parent_invoice.Branch,
                                                         number=invoices_item.number_invoice,
                                                         date_invoice=invoices_item.date_invoice,
                                                         type_invoice=type_invoice,
                                                         price=summ, parent=parent_invoice)
                else:
                    type_invoice = typeinvoices.objects.get(slug='consumption')
                    if type_docum.startswith('contract'):
                        contract_id = type_docum.split('-')[1]
                        type_contract = TypeDocument.objects.get(Name=alldocuments_fulldata.objects.get(id=contract_id).TypeDocumentName)
                        new_invoice = invoice.objects.create(ServingCompany=scompany_default,
                                                             Branch=Branch.objects.get(id=alldocuments_fulldata.objects.get(id=contract_id).Branch_id),
                                                             number=invoices_item.number_invoice,
                                                             date_invoice=invoices_item.date_invoice,
                                                             type_invoice=type_invoice,
                                                             price=invoices_item.price, type_document=type_contract,
                                                             number_document=contract_id)
                    elif type_docum.startswith('branch'):
                        branch_id = type_docum.split('-')[1]
                        new_invoice = invoice.objects.create(ServingCompany=scompany_default,
                                                             Branch=Branch.objects.get(id=branch_id),
                                                             number=invoices_item.number_invoice,
                                                             date_invoice=invoices_item.date_invoice,
                                                             type_invoice=type_invoice, price=invoices_item.price)
                if new_invoice:
                    import_invoices.objects.filter(id=invoices_item.id).delete()
        return redirect('trade_department:import_invoices_from1S')

    return render(request, 'import_invoices.html', {'invoices': invoices, 'city': scompany_default.City.slug})


def clear_import_invoices(request, city):
    import_invoices.objects.filter(city=city).delete()
    return redirect('trade_department:import_invoices_from1S')
