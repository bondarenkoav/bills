import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.template import Context, Template
from django.views.decorators.csrf import csrf_protect

from base.models import action_planned, allcontract_filter_term, logging
from base.templatetags.other_tags import get_count_days_of_month
from base.templatetags.personal_tags import get_shortfio
from build_service.models import BuildServiceAct
from contract_department.forms import form_quarterly_to_police, form_acts_period, forms_events_period, \
    form_term_contracts, form_maintenance_listObjects, form_assembly_production
from contract_department.models import all_activecontract_fulldata, allactive_securityobjects, CDTemplateDocuments, \
    allactive_maintenanceobjects, all_buildobjects
from maintenance_service.models import MaintenanceServiceAct
from reference_books.models import City

title_area = u'Договорной отдел'


@login_required
@csrf_protect
def journal_events(request):
    events = []
    scompany_data = None

    form = forms_events_period(request.POST or None)
    if request.POST:
        if form.is_valid():
            app_data = form.cleaned_data.get('filter_app')
            start_date = form.cleaned_data['filter_start_date']
            end_date = form.cleaned_data['filter_end_date']
            event = form.cleaned_data.get('filter_typeevent')
            scompany = form.cleaned_data.get('filter_scompany')

            events = logging.objects.filter(add_date__date__range=(start_date, end_date), app__in=app_data, scompany=scompany)
            if event:
                events = events.filter(event_code=event)

    return render(request, 'journal/events.html', {
        'form': form,
        'title': u'Произведенные операции',
        'area': title_area,
        'title_small': u'Журналы',
        'scompany': scompany_data,
        'list': events
    })


# Журнал - Запланированные операции
@login_required
def journal_planned_actions(request):
    action_list = action_planned.objects.filter(complete=False)
    paginator = Paginator(action_list, 20)
    page = request.GET.get('page')
    try:
        actions = paginator.page(page)
    except PageNotAnInteger:
        actions = paginator.page(1)
    except EmptyPage:
        actions = paginator.page(paginator.num_pages)

    return render(request, 'journal/planned.html', {
        'title': u'Запланированные операции',
        'area': title_area,
        'title_small': u'Журналы',
        'list': actions,
        'page': page
    })


# Журнал - Срочные договора
@login_required
def journals_term_contracts(request):
    contracts = {}
    form = form_term_contracts(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany_data = form.cleaned_data.get('scompany')
            typedoc_data = form.cleaned_data.get('typedoc')

            contracts = allcontract_filter_term.objects.filter(DateTermination__gte=datetime.datetime.today(),
                                                               ServingCompanyBranchName=scompany_data.NameBranch,
                                                               TypeDocumentName=typedoc_data.Name).order_by('DateTermination')

    return render(request, 'journal/term_contract.html', {
        'title': u'Срочные договора',
        'area': title_area,
        'title_small': u'Журналы',
        'list': contracts,
        'form': form
    })


# Журнал - Не полные договора (нет сканов)
@login_required
def journal_notcomplete_contracts(request):
    contracts = all_activecontract_fulldata.objects.all()
    paginator = Paginator(contracts, 20)
    page = request.GET.get('page')
    try:
        actions = paginator.page(page)
    except PageNotAnInteger:
        actions = paginator.page(1)
    except EmptyPage:
        actions = paginator.page(paginator.num_pages)

    return render(request, 'journal/notcomplete_contracts.html', {
        'title': u'Не полные договора',
        'area': title_area,
        'title_small': u'Журналы',
        'list': actions,
        'page': page
    })


# Журнал - Список объектов ТО (действующие)
@login_required
def journal_action_objects(request):
    objects_action = []
    form = form_maintenance_listObjects(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany_data = form.cleaned_data['scompany']
            objects_action = allactive_maintenanceobjects.objects.all()
            sortby_column = form.cleaned_data['sortby_column']

            if scompany_data:
                objects_action = objects_action.filter(scompany_id=scompany_data.id)
            city = form.cleaned_data['city']
            if city:
                objects_action = objects_action.filter(city_id=city.id)

            if sortby_column == 'name':
                objects_action = objects_action.order_by('name_client')
            elif sortby_column == 'city':
                objects_action = objects_action.order_by('city_id')
            else:
                objects_action = objects_action.order_by('date_end')

    return render(request, 'journal/action_objects.html', {
        'title': u'Список объектов ТО',
        'area': title_area,
        'title_small': u'Журналы',
        'list': objects_action,
        'form': form
    })


# Отчёт - Производственный отчет по монтажу(действующие)
@login_required
def report_assembly_production(request):
    build_objects = []
    form = form_assembly_production(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany_data = form.cleaned_data['scompany']
            filter_month = form.cleaned_data['filter_month']
            count_day_ofmonth = get_count_days_of_month(filter_month.year, filter_month.month)
            filter_firstday = datetime.datetime.strptime(filter_month.year.__str__() + '-' + filter_month.month.__str__() + '-01', '%Y-%m-%d')
            filter_lastday = datetime.datetime.strptime(filter_month.year.__str__() + '-' + filter_month.month.__str__() + '-' + count_day_ofmonth.__str__(), '%Y-%m-%d')
            # build_objects = all_buildobjects.objects.all()
            build_objects = all_buildobjects.objects.filter(scompany_id=scompany_data.id,
                                                            date_start__range=(filter_firstday, filter_lastday))

    return render(request, 'reports/assembly_production.html', {
        'title': u'Производственный отчет по монтажу',
        'area': title_area,
        'title_small': u'Отчёты',
        'list': build_objects,
        'form': form
    })


@login_required()
@csrf_protect
def journal_acts_period(request):
    acts_buildservice = acts_maintenanceservice = {}

    form = form_acts_period(request.POST or None)

    if request.POST:
        if form.is_valid():
            scompany_data = form.cleaned_data['scompany']
            filter_start_date = form.cleaned_data['filter_start_date']
            filter_end_date = form.cleaned_data['filter_end_date']
            if filter_end_date is None:
                filter_end_date = filter_start_date

            acts_buildservice = BuildServiceAct.objects.filter(ServingCompany=scompany_data,
                                                               datetime_add__date__gte=filter_start_date,
                                                               datetime_add__date__lte=filter_end_date)
            acts_maintenanceservice = MaintenanceServiceAct.objects.filter(ServingCompany=scompany_data,
                                                                           datetime_add__date__gte=filter_start_date,
                                                                           datetime_add__date__lte=filter_end_date)

    return render(request, 'journal/acst_period.html', {
        'title': u'Акты',
        'area': title_area,
        'title_small': u'Журналы',
        'form': form,
        'acts_build': acts_buildservice,
        'acts_maintenance': acts_maintenanceservice
    })


# Отчёт - Ежеквартальный отчет в полицию
@login_required
@csrf_protect
def get_quarterly_to_police(request):
    form = form_quarterly_to_police(request.POST or None)
    if request.POST:
        if form.is_valid():
            i = 0
            filter_scompany = form.cleaned_data['scompany']

            massive = '<table border="1" cellpadding="7" width="100%"><thead><tr><td style="width:3%;background-color:#FFDD4C;text-align:center;">№ п/п</td><td style="width:27%;background-color:#FFDD4C;text-align:center;">Контрагент</td><td style="width:37%;background-color:#FFDD4C;text-align:center;">Адрес</td><td style="width:18%;background-color:#FFDD4C;text-align:center;">Наименование объекта</td><td style="width:15%;background-color:#FFDD4C;text-align:center;">Договор</td></tr></thead><tbody>'

            cities = City.objects.all()
            for city in cities:
                objects = allactive_securityobjects.objects.filter(scompany_id=filter_scompany.id, city_id=city.id)

                if objects:
                    if objects.first():
                        massive = massive+'<tr><td colspan="5" style="background-color:#ccccff;text-align:center;text;"><span style="font-size:18px"><strong>'+city.CityName+'</strong></span></td></tr>'

                    for object in objects:
                        i = i+1

                        if object.name_branch:
                            name_client = object.name_branch
                        else:
                            name_client = object.name_client
                        name_client = name_client.replace('/','&#34')

                        if object.numcontract_external!='':
                            num_contract = object.numcontract_external
                        else:
                            num_contract = object.numcontract_internal

                        date_conclusion = datetime.datetime.strftime(object.date_conclusion, "%d.%m.%Y")

                        massive = massive+'<tr><td style="background-color:#ccccff;text-align:center;">'+i.__str__()+'</td><td>'+name_client+'</td><td>'+object.address_object+'</td><td>'+object.name_object+'</td><td>'+num_contract+' от '+date_conclusion+'</td></tr>'

            massive = massive+'</tbody></table>'

            text_template = Template(CDTemplateDocuments.objects.get(slug='report_quarterly_to_police').TextTemplate)

            tags = Context({
                'ServingCompany_name': filter_scompany.ServingCompany.NameCompany_short,
                'ServingCompany_city': filter_scompany.City,
                'TableMassive': massive,
                'ServingCompanyManagement_post': filter_scompany.ServingCompany.Management_post,
                'ServingCompanyManagement_name': filter_scompany.ServingCompany.Management_name,
            })
            text = text_template.render(tags)
            return render(request, 'view_template.html', {'text':text})
        else:
            return render(request, 'reports/quarterly_to_police.html', {'form': form,
                                                                    'title': u'Квартальный отчет в полицию',
                                                                    'area': title_area,
                                                                    'title_small': u'Отчеты'})
    else:
        return render(request, 'reports/quarterly_to_police.html', {'form': form,
                                                                    'title': u'Квартальный отчет в полицию',
                                                                    'area': title_area,
                                                                    'title_small': u'Отчеты'})


def get_headtext(contract):
    executor_headtext = contract.ServingCompany.head_text
    customer_headtext = contract.Branch.Client.TypeClient.head_text
    headtext = executor_headtext+customer_headtext
    text_template = Template(headtext)

    if contract.Branch.PowersOffice_date:
        powersofficedate = ' от '+contract.Branch.PowersOffice_date
    else:
        powersofficedate = ''

    tags = Context({
        'executor_NameCompany_full':    contract.ServingCompany.ServingCompany.NameCompany_full,
        'executor_NameCompany_short':   contract.ServingCompany.ServingCompany.NameCompany_short,
        'executor_Management_post':     contract.ServingCompany.ServingCompany.Management_post,
        'executor_Management_name':     contract.ServingCompany.ServingCompany.Management_name,
        'executor_PowersOffice_name':   contract.ServingCompany.PowersOffice_name,
        'executor_PowersOffice_number': contract.ServingCompany.PowersOffice_number,
        'customer_NameClient_full':     contract.Branch.Client.NameClient_full,
        'customer_Management_post':     contract.Branch.Management_post,
        'customer_Management_name':     contract.Branch.Management_name,
        'customer_PowersOffice_name':   contract.Branch.PowersOffice_name,
        'customer_PowersOffice_number': contract.Branch.PowersOffice_number,
        'customer_PowersOffice_date':   powersofficedate,
    })
    return text_template.render(tags)


def get_executor_details(contract):
    text_template = Template(contract.ServingCompany.details_text)
    tags = Context({
        'NameCompany_short':    contract.ServingCompany.ServingCompany.NameCompany_short,
        'Address_reg':          contract.ServingCompany.ServingCompany.Address_reg,
        'INN':                  contract.ServingCompany.ServingCompany.INN,
        'KPP':                  contract.ServingCompany.KPP,
        'Bank_RaschetSchet':    contract.ServingCompany.Bank_RaschetSchet,
        'Bank_Details':         contract.ServingCompany.Bank_Details,
        'Bank_BIK':             contract.ServingCompany.Bank_BIK,
        'Phone_city':           contract.ServingCompany.Phone_city,
        'Phone_fax':            contract.ServingCompany.Phone_fax,
        'Address_email':        contract.ServingCompany.Address_email,
    })
    return text_template.render(tags)


def get_customer_details(contract):
    text_template = Template(contract.Branch.Client.TypeClient.details_text)
    if contract.Branch.Client.TypeClient.slug == 'company':
        tags = Context({
            'NameBranch':       contract.Branch.NameBranch,
            'Address_reg':      contract.Branch.Client.Address_reg,
            'INN':              contract.Branch.Client.INN,
            'KPP':              contract.Branch.KPP,
            'Bank_RaschetSchet': contract.Branch.Bank_RaschetSchet,
            'Bank_Details':     contract.Branch.Bank_Details,
            'Bank_BIK':         contract.Branch.Bank_BIK,
            'Phone_city':       contract.Branch.Phone_city,
            'Phone_fax':        contract.Branch.Phone_fax,
            'Address_email':    contract.Branch.Address_email,
        })
    elif contract.Branch.Client.TypeClient.slug == 'businessman':
        tags = Context({
            'NameBranch':       contract.Branch.Client.NameClient_full,
            'Address_reg':      contract.Branch.Client.Address_reg,
            'INN':              contract.Branch.Client.INN,
            'Bank_RaschetSchet': contract.Branch.Bank_RaschetSchet,
            'Bank_Details':     contract.Branch.Bank_Details,
            'Bank_BIK':         contract.Branch.Bank_BIK,
            'Phone_mobile':     contract.Branch.Phone_mobile,
            'Phone_city':       contract.Branch.Phone_city,
            'Phone_fax':        contract.Branch.Phone_fax,
            'Address_email':    contract.Branch.Address_email,
            'PassportSerNum':   contract.Branch.Client.PassportSerNum,
            'DatePassport':     contract.Branch.Client.DatePassport,
            'IssuedByPassport': contract.Branch.Client.IssuedByPassport,
        })
    else:
        tags = Context({
            'NameBranch':       contract.Branch.Client.NameClient_full,
            'Address_reg':      contract.Branch.Client.Address_reg,
            'INN':              contract.Branch.Client.INN,
            'KPP':              contract.Branch.KPP,
            'Bank_RaschetSchet': contract.Branch.Bank_RaschetSchet,
            'Bank_Details':     contract.Branch.Bank_Details,
            'Bank_BIK':         contract.Branch.Bank_BIK,
            'Phone_mobile':     contract.Branch.Phone_mobile,
            'Address_email':    contract.Branch.Address_email,
            'PassportSerNum':   contract.Branch.Client.PassportSerNum,
            'DatePassport':     contract.Branch.Client.DatePassport,
            'IssuedByPassport': contract.Branch.Client.IssuedByPassport,
        })
    return text_template.render(tags)


def get_executor_signature(contract):
    text_template = Template(contract.ServingCompany.signature_text)
    tags = Context({
        'NameCompany_short': contract.ServingCompany.ServingCompany.NameCompany_short,
        'Management_post':   contract.ServingCompany.Management_post,
        'Management_name':   get_shortfio(contract.ServingCompany.Management_name),
    })
    return text_template.render(tags)


def get_customer_signature(contract):
    text_template = Template(contract.Branch.Client.TypeClient.signature_text)
    if contract.Branch.Client.TypeClient.slug == 'company':
        tags = Context({
            'NameBranch':       contract.Branch.NameBranch,
            'Management_post':  contract.Branch.Management_post,
            'Management_name':  contract.Branch.Management_name,
        })
    else:
        tags = Context({
            'NameClient_full':  contract.Branch.Client.NameClient_full,
        })
    return text_template.render(tags)


# # Отчёт - Ежеквартальный отчет в полицию
# @login_required
# @csrf_protect
# def get_weekly_to_police(request):
#     form = form_weekly_to_police(request.POST or None)
#     if request.POST:
#         if form.is_valid():
#             i = 0
#             filter_scompany = form.cleaned_data['scompany']
#
#             massive = '<table border="1" cellpadding="7" width="100%"><thead><tr><td style="width:3%;background-color:#FFDD4C;text-align:center;">№ п/п</td><td style="width:27%;background-color:#FFDD4C;text-align:center;">Контрагент</td><td style="width:37%;background-color:#FFDD4C;text-align:center;">Адрес</td><td style="width:18%;background-color:#FFDD4C;text-align:center;">Наименование объекта</td><td style="width:15%;background-color:#FFDD4C;text-align:center;">Договор</td></tr></thead><tbody>'
#
#             cities = City.objects.all()
#             for city in cities:
#                 objects = allactive_securityobjects.objects.filter(scompany_id=filter_scompany.id, city_id=city.id)
#
#                 if objects:
#                     if objects.first():
#                         massive = massive+'<tr><td colspan="5" style="background-color:#ccccff;text-align:center;text;"><span style="font-size:18px"><strong>'+city.CityName+'</strong></span></td></tr>'
#
#                     for object in objects:
#                         i = i+1
#
#                         if object.name_branch:
#                             name_client = object.name_branch
#                         else:
#                             name_client = object.name_client
#                         name_client = name_client.replace('/','&#34')
#
#                         if object.numcontract_external!='':
#                             num_contract = object.numcontract_external
#                         else:
#                             num_contract = object.numcontract_internal
#
#                         date_conclusion = datetime.datetime.strftime(object.date_conclusion, "%d.%m.%Y")
#
#                         massive = massive+'<tr><td style="background-color:#ccccff;text-align:center;">'+i.__str__()+'</td><td>'+name_client+'</td><td>'+object.address_object+'</td><td>'+object.name_object+'</td><td>'+num_contract+' от '+date_conclusion+'</td></tr>'
#
#             massive = massive+'</tbody></table>'
#
#             text_template = Template(CDTemplateDocuments.objects.get(slug='report_quarterly_to_police').TextTemplate)
#
#             tags = Context({
#                 'ServingCompany_name': filter_scompany.ServingCompany.NameCompany_short,
#                 'ServingCompany_city': filter_scompany.City,
#                 'TableMassive': massive,
#                 'ServingCompanyManagement_post': filter_scompany.ServingCompany.Management_post,
#                 'ServingCompanyManagement_name': filter_scompany.ServingCompany.Management_name,
#             })
#             text = text_template.render(tags)
#             return render(request, 'view_template.html', {'text':text})
#         else:
#             return render(request, 'reports/weekly_to_police.html', {'form': form,
#                                                                      'title': u'Недельный отчет в полицию',
#                                                                      'area': title_area,
#                                                                      'title_small': u'Отчеты'})
#     else:
#         return render(request, 'reports/weekly_to_police.html', {'form': form,
#                                                                  'title': u'Недельный отчет в полицию',
#                                                                  'area': title_area,
#                                                                  'title_small': u'Отчеты'})

# Отчёт - Еженедельный отчет в полицию
# @login_required
# @csrf_protect
# def get_weekly_to_police(request):
#     args = {}
#     args.update(csrf(request))
#     form = form_weekly_to_police(request.POST)
#
#     if request.POST:
#         if form.is_valid():
#             date_add = datetime.datetime.strptime(request.POST['filter_date'],"%d.%m.%Y").date()
#     return render(request, 'reports/weekly_to_police.html', {'objects':onoffobject_log.objects.all(), 'events': logging.objects.filter(add_date__date=date_add)})
#
#
# def get_weekly_to_police_print(request, branch_id=None, contract_id=None):
#     pass
#     args = {}
#
#     contract = TechSecurityContract.objects.get(id=contract_id)
#     text_template = Template(TechSecurityContract.objects.get(id=contract_id).TemplateDocuments.TextTemplate)
#
#     tags = Context({
#         'NumContract': contract.NumContractInternal,
#         'City': contract.ServingCompany.ServingCompany.Address_reg,
#         'DateConclusion': contract.DateConclusion,
#         'ServingCompanyName_full': contract.ServingCompany.ServingCompany.NameCompany_full,
#         'ServingCompanyName_short': contract.ServingCompany.ServingCompany.NameCompany_short,
#         'ServingCompanyManage_name': contract.ServingCompany.ServingCompany.Management_name,
#         'ServingCompanyManage_post': contract.ServingCompany.ServingCompany.Management_post,
#         'ServingCompanyPowersOffice_name': contract.ServingCompany.PowersOffice_name,
#         'ServingCompanyPowersOffice_number': contract.ServingCompany.PowersOffice_number,
#         'ServingCompanyAddress_reg': contract.ServingCompany.ServingCompany.Address_reg,
#         'ServingCompanyAddress_post': contract.ServingCompany.Address_post,
#         'ServingCompanyAddress_email': contract.ServingCompany.Address_email,
#         'ServingCompanyBank_RaschetSchet': contract.ServingCompany.Bank_RaschetSchet,
#         'ServingCompanyBank_Details': contract.ServingCompany.Bank_Details,
#         'BranchName': contract.Branch.NameBranch,
#         'BranchAddress_reg': contract.Branch.Client.Address_reg,
#         'BranchAddress_post': contract.Branch.Address_post,
#         'BranchAddress_email': contract.Branch.Address_email,
#         'BranchBank_RaschetSchet': contract.Branch.Bank_RaschetSchet,
#         'BranchBank_Details': contract.Branch.Bank_Details
#     })
#     text = text_template.render(tags)
#     args['text'] = text
#     return render(request, 'view_template.html', args)