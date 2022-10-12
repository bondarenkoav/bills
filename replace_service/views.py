from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.db.models import Sum, FloatField
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_protect

from .apps import ReplaceServiceConfig
from accounting.models import credited_with_paid
from base.models import Branch, ServingCompany_settingsDocuments, logging, SectionsApp
from base.views import logging_event
from .forms import form_contract_replace_service, form_object_replace_service, form_act_replace_service
from reference_books.models import TypeDocument

from .models import ReplaceServiceObject, ReplaceServiceContract, ReplaceServiceAct

apps_name = ReplaceServiceConfig.name


@login_required
@permission_required('Replace_service.contract_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_contract(request, branch_id, contract_id=None):
    type_dct = 'replace_service_contract'
    SumPriceAllActs = 0
    contract_data = objects = acts = []

    branch_data = Branch.objects.get(id=branch_id)
    if contract_id:
        contract_data = ReplaceServiceContract.objects.get(id=contract_id)
        list_objects = ReplaceServiceObject.objects.filter(ReplaceServiceContract=contract_data)
        list_acts = ReplaceServiceAct.objects.filter(ReplaceServiceObject__in=list_objects)
        # Освоенная сумма
        SumPriceAllActs = list_acts.aggregate(price=Sum('Price', output_field=FloatField()))

        paginator = Paginator(list_acts, 15)
        page = request.GET.get('page')
        try:
            acts = paginator.page(page)
        except PageNotAnInteger:
            acts = paginator.page(1)
        except EmptyPage:
            acts = paginator.page(paginator.num_pages)

        paginator = Paginator(list_objects, 15)
        page = request.GET.get('page')
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)

    form = form_contract_replace_service(request.POST or None,
                                         instance=contract_id and ReplaceServiceContract.objects.get(id=contract_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if contract_id:
                old_data = ReplaceServiceContract.objects.get(id=contract_id)

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

                if old_data.NameOfService != form.cleaned_data['NameOfService']:
                    logging_event('change_nameOfService_contract', None, old_data.NameOfService, apps_name,
                                  request.user.username, type_dct, old_data.ServingCompany, branch_id, contract_id)

                scompany = old_data.ServingCompany
            else:
                scompany = form.cleaned_data.get('ServingCompany')

            num_last_contract = ServingCompany_settingsDocuments.objects. \
                get(TypeDocument=TypeDocument.objects.get(slug='replace_service_contract'), ServingCompanyBranch=scompany)
            NumContractInternal = str(num_last_contract.prefix_num) + str(num_last_contract.current_num + 1) + str(
                num_last_contract.postfix_num)

            new_contract = form.save(commit=False)
            if contract_id is None:
                new_contract.TypeDocument = TypeDocument.objects.get(slug='replace_service_contract')
                new_contract.Branch = Branch.objects.get(id=branch_id)
                new_contract.NumContractInternal = NumContractInternal
            else:
                new_contract.ServingCompany = old_data.ServingCompany
            new_contract.save()

            if contract_id is None:
                # Обновление номера следующего договора в таблице
                ServingCompany_settingsDocuments.objects. \
                    filter(TypeDocument=TypeDocument.objects.get(slug='replace_service_contract'),
                           ServingCompanyBranch=scompany). \
                    update(current_num=num_last_contract.current_num + 1)
                logging_event('add_contract', None, '', apps_name, request.user.username, type_dct,
                              new_contract.ServingCompany, branch_id, new_contract.id)

            return redirect('replace_service:addget_contract', branch_id=branch_id, contract_id=new_contract.id)

    return render(request, 'contract_replace_service.html', {
        'form': form,
        'branch_data': branch_data,
        'contract_data': contract_data,
        'SumPriceAllActs': SumPriceAllActs,
        'objects': objects,
        'acts': acts,
        'page_add': ((objects.number - 1) * 15 if objects else 0),
    })


@login_required
@permission_required('Replace_service.object_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_object(request, branch_id, contract_id, object_id=None):
    contract_data = ReplaceServiceContract.objects.get(id=contract_id)
    type_dct = TypeDocument.objects.get(slug='replace_service_contract')
    object_data = events = []

    if object_id:
        object_data = ReplaceServiceObject.objects.get(id=object_id)
        events = logging.objects.filter(app=SectionsApp.objects.get(slug='replace_service'),
                                        type_dct=type_dct, object_id=object_id).order_by('-id')

    form = form_object_replace_service(request.POST or None,
                                     instance=object_id and ReplaceServiceObject.objects.get(id=object_id))

    if request.POST:
        if form.is_valid():
            if object_id:
                old_data = ReplaceServiceObject.objects.get(id=object_id)
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

            new_object = form.save(commit=False)
            if object_id is None:
                new_object.ReplaceServiceContract = ReplaceServiceContract.objects.get(id=contract_id)
            new_object.save()
            form.save_m2m()

            if object_id is None:
                logging_event('add_object', None, '', apps_name, request.user.username, type_dct.slug,
                              contract_data.ServingCompany, branch_id, contract_id, new_object.id)

            return redirect('replace_service:addget_contract', branch_id=branch_id, contract_id=contract_id)

    return render(request, 'object_replace_service.html', {
        'form': form,
        'contract_data': contract_data,
        'object_data': object_data,
        'events': events
    })


@login_required
@permission_required('Replace_service.act_list_view', login_url=reverse_lazy('page_error403'))
@csrf_protect
def add_get_act(request, branch_id, act_id=None):
    type_dct = 'replace_service_act'
    act_data = []

    if act_id:
        act_data = ReplaceServiceAct.objects.get(id=act_id)

    form = form_act_replace_service(request.POST or None, instance=act_id and ReplaceServiceAct.objects.get(id=act_id))

    if request.POST:
        if form.is_valid():
            old_data = []
            if act_id:
                old_data = ReplaceServiceAct.objects.get(id=act_id)

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

                if old_data.CoWorkers != form.cleaned_data['CoWorkers']:
                    logging_event('change_CoWorker', None, old_data.CoWorker, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)

                if old_data.Descriptions != form.cleaned_data['Descriptions']:
                    logging_event('change_description', None, old_data.Descriptions, apps_name, request.user.username,
                                  type_dct, old_data.ServingCompany, branch_id, act_id)

            new_act = form.save(commit=False)

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

    return render(request, 'act_replace_service.html', {
        'form': form,
        'act_data': act_data,
        'branch_data': Branch.objects.get(id=branch_id)
    })
