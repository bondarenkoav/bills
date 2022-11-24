# -*- coding: utf-8 -*-
import datetime
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django_currentuser.middleware import get_current_user

from account.models import Profile
from base.models import Client, Branch, Contacts, logging, Event, action_planned, allviews_forsearch, SectionsApp, \
    UserNote
from base.suggest import dadataapi_getdata_party, test_access_url, dadataapi_getdata_banki
from build_service.models import BuildServiceContract
from contract_department.models import allactive_securityobjects
from maintenance_service.models import MaintenanceServiceContract
from reference_books.models import TypesClient, TypeDocument, ListPosts
from base.forms import branch_form_company, search_form, \
    check_for_duplicate_company, check_for_duplicate_businessman, check_for_duplicate_physical_person, \
    client_form_company, client_form_businessman, client_form_physicalperson, get_forchange_scompany, \
    ContactsFormSet, form_additional_info, usernote_form, \
    ClientCompanyUpdateForm, BranchCompanyUpdateForm, \
    ClientBusinessmanUpdateForm, BranchBusinessmanUpdateForm, \
    ClientPhysicalPersonUpdateForm, BranchPhysicalPersonUpdateForm, search_filter_form
from tech_security.models import TechSecurityContract


inform_panels = [
    ['new_messages', 'Новых сообщений'],
    ['new_task', 'Новых задач'],
    ['new_notifications', 'Напоминания'],
    ['new_errors', 'Ошибок']
]


@login_required()
@csrf_protect
def dashboard(request):
    # args['new_tasks'] = user_task.objects.filter(read=False, responsible=request.user).count()
    # args['new_notifications'] = notification.objects.filter(read=False, responsible=request.user).count()
    group_list = request.user.groups.values_list('name', flat=True)
    return render(request, 'index.html', {
        'form': search_form(),
        'group': list(group_list),
        'currentmonth': datetime.datetime.today().month,
        'new_messages': 0,
        'new_errors': 0
    })


def get_bank_ofdadata(bik):
    bank_details = ''
    if bik and test_access_url is not False:
        if len(bik) == 9:
            suggest = dadataapi_getdata_banki(bik)
            data_bank = suggest.get('suggestions')[0]['data']
            if data_bank['name']:
                if data_bank['name']['payment']:
                    bank_details = data_bank['name']['payment']
            if data_bank['correspondent_account']:
                bank_details = bank_details + "\nКор.счет: " + data_bank['correspondent_account']
            if data_bank['address']['unrestricted_value']:
                bank_details = bank_details + "\nАдрес нахождения: " + data_bank['address']['unrestricted_value']
    return bank_details


@login_required()
@csrf_protect
def get_scompany(request, app=None, save_url=None, return_url=None):
    form = get_forchange_scompany(request.POST, user=request.user)

    if request.POST:
        scompany_id = int(request.POST['scompany'])
        if form.is_valid:
            return redirect(app + ':' + return_url, args=[scompany_id])
    else:
        save_url = app + ':' + save_url
        return render(request, 'get_scompany.html', {'form': form, 'save_url': save_url})


def save_numberphone(phone):
    str = phone.replace(' ', '')
    str = str.replace('-', '')
    str = str.replace('(', '')
    str = str.replace(')', '')
    return str


def get_post(name):
    obj, created = ListPosts.objects.get_or_create(
        NamePost__iexact=name,
        defaults={'NamePost': name.capitalize()},
    )
    return obj


def get_scompany_foruser():
    try:
        profile = Profile.objects.get(user=get_current_user()).scompany.all()
    except:
        return redirect('login')
    return profile


@login_required()
@csrf_protect
def get_client(request, branch_id=None):
    branch = Branch.objects.get(id=branch_id)

    form = form_additional_info(request.POST or None, instance=branch_id and Branch.objects.get(id=branch_id))
    if request.POST:
        if form.is_valid():
            form.save()
            return redirect('index:card_client', branch_id=branch_id)

    return render(request, 'client.html', {
        'form_additional_info': form,
        'tech_contracts': TechSecurityContract.objects.filter(Branch=branch),
        'build_contracts': BuildServiceContract.objects.filter(Branch=branch),
        'maintenance_contracts': MaintenanceServiceContract.objects.filter(Branch=branch),
        'list_scompany': get_scompany_foruser(),
        'branch_data': branch
    })


# -------------------------------------------- Организация ------------------------------------------------------------
@login_required()
@csrf_protect
def addclient_worddata_company(request, inn=None, kpp=None):
    if request.POST:
        form = client_form_company(request.POST)

        if form.is_valid():
            kpp = request.POST['kpp']
            new_client = Client.objects.create(
                TypeClient=TypesClient.objects.get(slug='company'),
                OKOPF=form.cleaned_data['OKOPF'],
                NameClient_full=form.cleaned_data['NameClient_full'],
                NameClient_short=form.cleaned_data['NameClient_short'],
                Management_post=form.cleaned_data['Management_post'],
                Management_name=form.cleaned_data['Management_name'],
                Address_reg=form.cleaned_data['Address_reg'],
                INN=form.cleaned_data['INN'],
                OGRN=form.cleaned_data['OGRN'],
                OKVED=form.cleaned_data['OKVED'])
            return redirect('contract_department:addclient_company_worddata_branch', client_id=new_client.id, kpp=kpp)
    else:
        if test_access_url is not False:
            suggest = dadataapi_getdata_party(inn)  # inn
            flag = suggest['suggestions']
            if len(flag) == 0:
                # dataClient = Client.objects.filter(INN=inn, id__in=Branch.objects.filter(KPP=kpp).values('Client'))
                # form = client_form_company(data={
                #     'INN': inn, 'kpp': kpp,
                #     'NameClient_full': dataClient.NameClient_full,
                #     'NameClient_short': dataClient.NameClient_short,
                #     'Address_reg': dataClient.Address_reg,
                #     'OGRN': dataClient.OGRN,
                #     'OKVED': dataClient.OKVED,
                #     'OKOPF': dataClient.OKOPF,
                #     'Management_post': dataClient.Management_post,
                #     'Management_name': dataClient.Management_name
                # })
                # messages.warning(request, u'Вы находитесь в "ручном режиме" редактирования. Ответственность за верность данных несёте Вы')
                # messages.info(request, u'Поля помеченные "звёздочкой" - обязательны для заполнения')
                return redirect('error_testclient')
            else:
                data = suggest.get('suggestions')[0]['data']
                messages.info(request, u'Поля помеченные "звёздочкой" - обязательны для заполнения')

                form = client_form_company(data={
                    'INN': data['inn'], 'kpp': kpp,
                    'NameClient_full': data['name']['full_with_opf'],
                    'NameClient_short': data['name']['short_with_opf'],
                    'Address_reg': data['address']['data']['source'],
                    'OGRN': data['ogrn'],
                    'OKVED': data['okved'],
                    'OKOPF': str('' if data['opf'] is None else data['opf']['code']),
                    'Management_post': str('' if data['management'] is None else data['management']['post']),
                    'Management_name': str('' if data['management'] is None else data['management']['name'])
                })
        else:
            return redirect('service_unavailable')

    return render(request, 'addclient/new_client.html', {
        'title': 'Шаг №3',
        'title_area': 'Новый контрагент',
        'title_small': 'Получение данных по ИНН',
        'form': form,
        'type': 'company',
        'inn': inn,
        'kpp': kpp,
    })


@login_required()
@csrf_protect
def addclient_worddata_branch(request, client_id=None, kpp=None):
    client_data = Client.objects.get(id=int(client_id))

    if request.POST:
        form = branch_form_company(request.POST)

        if form.is_valid():
            if form.cleaned_data['Bank_BIK']:
                suggest = dadataapi_getdata_banki(form.cleaned_data['Bank_BIK'])
                data = suggest.get('suggestions')[0]['data']
                bank_details = data['name']['payment'] + "\nКор.счет: " + \
                               str("" if data['correspondent_account'] is None
                                   else data['correspondent_account']) + "\nАдрес нахождения: " + \
                               data['address']['unrestricted_value']
            else:
                bank_details = ''

            new_branch = Branch.objects.create(
                Client=Client.objects.get(id=int(form.cleaned_data['Client'])),
                NameBranch=form.cleaned_data['NameBranch'],
                Management_post=form.cleaned_data['Management_post'],
                Management_name=form.cleaned_data['Management_name'],
                Management_data='',
                PowersOffice_name=form.cleaned_data['PowersOffice_name'],
                PowersOffice_number=form.cleaned_data['PowersOffice_number'],
                PowersOffice_date=form.cleaned_data['PowersOffice_date'],
                Address_reg=form.cleaned_data['Address_reg'],
                Address_post=form.cleaned_data['Address_post'],
                Address_email=form.cleaned_data['Address_email'],
                KPP=form.cleaned_data['KPP'],
                Phone_city=save_numberphone(form.cleaned_data['Phone_city']),
                Phone_mobile=save_numberphone(form.cleaned_data['Phone_mobile']),
                Phone_fax=save_numberphone(form.cleaned_data['Phone_fax']),
                Phone_SMS=save_numberphone(form.cleaned_data['Phone_sms']),
                Bank_BIK=form.cleaned_data['Bank_BIK'],
                Bank_RaschetSchet=form.cleaned_data['Bank_RaschetSchet'],
                EDO=form.cleaned_data['EDO'],
                Bank_Details=bank_details
            )
            return redirect('contract_department:contact_add', branch_id=new_branch.id)
    else:
        if client_data.NameClient_short is not None:
            namebranch = client_data.NameClient_short
        else:
            namebranch = client_data.NameClient_full

        form = branch_form_company(data={
            'KPP': kpp,
            'Client': client_data.id,
            'NameBranch': namebranch,
            'Management_name': client_data.Management_name,
            'Management_post': get_post(client_data.Management_post),
            'Address_reg': client_data.Address_reg,
            'Address_post': client_data.Address_reg
        })

    return render(request, 'addclient/new_branch.html', {
        'title': 'Шаг №4',
        'title_area': 'Новый контрагент',
        'title_small': 'Ввод нового филиала организации',
        'form': form,
        'client_id': client_data.id,
        'kpp': kpp,
    })


# ---------------------------------------- Индивидуальный предприниматель ---------------------------------------------
@login_required()
@csrf_protect
def addclient_worddata_businessman(request, inn=None, kpp=None):
    if request.POST:
        form = client_form_businessman(request.POST)

        if form.is_valid():
            new_client = Client.objects.create(
                TypeClient=TypesClient.objects.get(slug='businessman'),
                OKOPF='50102',
                NameClient_full=form.cleaned_data['NameClient_full'],
                Address_reg=form.cleaned_data['Address_reg'],
                INN=form.cleaned_data['INN'],
                OGRN=form.cleaned_data['OGRN'],
                OKVED=form.cleaned_data['OKVED'],
                PassportSerNum=form.cleaned_data['PassportSerNum'],
                DatePassport=form.cleaned_data['DatePassport'],
                IssuedByPassport=form.cleaned_data['IssuedByPassport']
            )

            if form.cleaned_data['Bank_BIK'] != '':
                suggest = dadataapi_getdata_banki(form.cleaned_data['Bank_BIK'])
                data = suggest.get('suggestions')[0]['data']
                bank_details = data['name']['payment'] + "\nКор.счет: " + data[
                    'correspondent_account'] + "\nАдрес нахождения: " + data['address']['unrestricted_value']
            else:
                bank_details = ''

            new_branch = Branch.objects.create(
                Client=Client.objects.get(id=new_client.id),
                Address_email=form.cleaned_data['Address_email'],
                Bank_BIK=form.cleaned_data['Bank_BIK'],
                Bank_RaschetSchet=form.cleaned_data['Bank_RaschetSchet'],
                Bank_Details=bank_details,
                Phone_city=save_numberphone(form.cleaned_data['Phone_city']),
                Phone_mobile=save_numberphone(form.cleaned_data['Phone_mobile']),
                Phone_fax=save_numberphone(form.cleaned_data['Phone_fax']),
                Phone_SMS=save_numberphone(form.cleaned_data['Phone_sms']),
                EDO=form.cleaned_data['EDO']
            )
            return redirect('contract_department:contact_add', branch_id=new_branch.id)

    else:
        form = client_form_businessman()
        if test_access_url is not False:
            suggest = dadataapi_getdata_party(inn)  # inn
            try:
                data = suggest.get('suggestions')[0]['data']
                messages.info(request, u'Поля помеченные "звёздочкой" - обязательны для заполнения')
                form = client_form_businessman(data={
                    'INN': data['inn'], 'kpp': kpp,
                    'NameClient_full': data['name']['full'],
                    'Address_reg': (data['address']['value'] if data['address'] else 'Ошибка получения адреса. '
                                                                                     'Введите адрес вручную.'),
                    'OGRN': data['ogrn'],
                    'OKVED': data['okved'],
                    'OKOPF': data['opf']['code']
                })
            except:
                messages.error(request, u'Контрагент с данным ИНН не найден')
        else:
            return redirect('service_unavailable')

    return render(request, 'addclient/new_client.html', {
        'title': 'Шаг №3',
        'title_area': 'Новый контрагент',
        'title_small': 'Ввод данных физическом лице',
        'form': form,
        'type': 'businessman',
        'inn': inn,
    })


# ---------------------------------------------- Физическое лицо -----------------------------------------------------
@login_required()
@csrf_protect
def addclient_worddata_physicalperson(request, fio=None, passport=None, alien=False):
    if request.POST:
        form = client_form_physicalperson(request.POST)

        if form.is_valid():
            new_client = Client.objects.create(
                TypeClient=TypesClient.objects.get(slug='physical_person'),
                NameClient_full=form.cleaned_data['NameClient_full'],
                Address_reg=form.cleaned_data['Address_reg'],
                INN=form.cleaned_data['INN'],
                PassportSerNum=form.cleaned_data['PassportSerNum'],
                DatePassport=form.cleaned_data['DatePassport'],
                IssuedByPassport=form.cleaned_data['IssuedByPassport'],
                Alien=form.cleaned_data['Alien']
            )
            new_branch = Branch.objects.create(
                Client=Client.objects.get(id=new_client.id),
                Address_email=form.cleaned_data['Address_email'],
                Bank_BIK=form.cleaned_data['Bank_BIK'],
                Bank_RaschetSchet=form.cleaned_data['Bank_RaschetSchet'],
                Bank_Details=get_bank_ofdadata(form.cleaned_data['Bank_BIK']),
                Phone_city=save_numberphone(form.cleaned_data['Phone_city']),
                Phone_mobile=save_numberphone(form.cleaned_data['Phone_mobile']),
                Phone_SMS=save_numberphone(form.cleaned_data['Phone_sms']),
                EDO=form.cleaned_data['EDO']
            )
            return redirect('contract_department:contact_add', branch_id=new_branch.id)

    else:
        messages.info(request, u'Поля помеченные "звёздочкой" - обязательны для заполнения')
        if alien == 'False':
            document = passport[:4] + ' ' + passport[4:]
        else:
            document = passport
        form = client_form_physicalperson(data={'NameClient_full': fio.replace('_', ' '),
                                                'PassportSerNum': document, 'Alien': alien})

    return render(request, 'addclient/new_client.html', {
        'title': 'Шаг №3',
        'title_area': 'Новый контрагент',
        'title_small': 'Ввод данных о физическом лице',
        'form': form,
        'type': 'physicalperson'
    })


# ---------------------------------------------- Для всех типов  ------------------------------------------------------
@login_required()
@csrf_protect
def addclient_check_client(request, type_client):
    if request.POST:
        if type_client == 'company':
            form = check_for_duplicate_company(request.POST)
        elif type_client == 'businessman':
            form = check_for_duplicate_businessman(request.POST)
        else:
            form = check_for_duplicate_physical_person(request.POST)

        if form.is_valid():
            if type_client == 'company':
                inn = form.cleaned_data['inn']
                kpp = form.cleaned_data['kpp']

                if form.get_client():
                    if form.get_branch():
                        return redirect('index:card_client', branch_id=form.get_branch().id)
                    else:
                        return redirect('contract_department:addclient_company_worddata_branch',
                                        client_id=form.get_client().id, kpp=kpp)
                else:
                    return redirect('contract_department:addclient_company_worddata_client', inn=inn, kpp=kpp)

            elif type_client == 'businessman':
                if form.get_client():
                    return redirect('index:card_client', branch_id=form.get_client().id)
                else:
                    return redirect('contract_department:addclient_businessman_worddata_client',
                                    inn=form.cleaned_data['inn'])

            else:
                if form.get_client():
                    return redirect('index:card_client', branch_id=form.get_client().id)
                else:
                    fio = form.cleaned_data['full_name'].replace(' ', '_')
                    passport = form.cleaned_data['passport_sernum'].replace(' ', '')
                    alien = form.cleaned_data['alien']
                    return redirect('contract_department:addclient_physicalperson_worddata_client',
                                    fio=fio, passport=passport, alien=alien)
    else:
        if type_client == 'company':
            form = check_for_duplicate_company()
        elif type_client == 'businessman':
            form = check_for_duplicate_businessman()
        else:
            form = check_for_duplicate_physical_person()

    return render(request, 'addclient/check_client.html', {
        'title': 'Шаг №2',
        'title_area': 'Новый контрагент',
        'title_small': 'Проверка контрагента на дублирование',
        'form': form,
        'type': type_client,
    })


# ------------------------------------------------------------------------------------------------------------------
#                             Изменение данных контрагента
# ------------------------------------------------------------------------------------------------------------------
@login_required()
@csrf_protect
def client_Company_update(request, pk):
    branch = Branch.objects.get(id=pk)
    ClientForm = ClientCompanyUpdateForm(request.POST or None, instance=branch.Client.pk and branch.Client)
    BranchForm = BranchCompanyUpdateForm(request.POST or None, instance=pk and branch)

    if request.POST:
        if ClientForm.is_valid() and BranchForm.is_valid():
            ClientForm.save()
            BranchForm.save()
            return redirect('index:card_client', branch_id=branch.pk)
    else:
        messages.info(request, u'Клиент добавлен: %s / %s' % (branch.Client.datetime_add.strftime("%d.%m.%Y %H:%M"),
                                                            branch.Client.Create_user))
        if branch.Client.datetime_add != branch.Client.datetime_update:
            messages.info(request, u'Последнее изменение: %s / %s' % (branch.Client.datetime_update.strftime("%d.%m.%Y %H:%M"),
                                                                    branch.Update_user))

        if test_access_url is not False:
            suggest = dadataapi_getdata_party(branch.Client.INN)  # inn
            flag = suggest['suggestions']
            if len(flag) == 0:
                messages.warning(request, u'Вы находитесь в "РУЧНОМ РЕЖИМЕ" редактирования. '
                                          u'Ответственность за ввод не корректных данных в данном режиме, несёте Вы лично.')
            else:
                data = suggest.get('suggestions')[0]['data']
                Client.objects.filter(id=branch.Client.pk).update(
                    OGRN=data['ogrn'], OKVED=data['okved'],
                    NameClient_full=data['name']['full_with_opf'],
                    NameClient_short=data['name']['short_with_opf'],
                    Address_reg=data['address']['data']['source'],
                    OKOPF=str('' if data['opf'] is None else data['opf']['code']),
                    Management_post=str('' if data['management'] is None else data['management']['post']),
                    Management_name=str('' if data['management'] is None else data['management']['name'])
                )
                messages.info(request, 'Обновление основных данных контрагента прошло успешно')
        else:
            messages.error(request, 'Проблема с обновлением данных онлайн')

    return render(request, "addclient/change_client.html", {
        'title': 'Изменение данных контрагента',
        'title_area': 'Контрагент',
        'title_small': 'Данные',
        'branch_data': branch,
        'form_client': ClientForm,
        'form_branch': BranchForm,
        'url_': reverse('contract_department:client_company_update', kwargs={'pk': pk})
    })


@login_required()
@csrf_protect
def client_Businessman_update(request, pk):
    branch = Branch.objects.get(id=pk)
    ClientForm = ClientBusinessmanUpdateForm(request.POST or None, instance=branch.Client.pk and branch.Client)
    BranchForm = BranchBusinessmanUpdateForm(request.POST or None, instance=pk and branch)

    if request.POST:
        if ClientForm.is_valid() and BranchForm.is_valid():
            ClientForm.save()
            BranchForm.save()
            return redirect('index:card_client', branch_id=branch.pk)

    return render(request, "addclient/change_client.html", {
        'title': 'Изменение данных контрагента',
        'title_area': 'Контрагент',
        'title_small': 'Данные',
        'branch_data': branch,
        'form_client': ClientForm,
        'form_branch': BranchForm,
        'url_': reverse('contract_department:client_businessman_update', kwargs={'pk': pk})
    })


@login_required()
@csrf_protect
def client_PhysicalPerson_update(request, pk):
    branch = Branch.objects.get(id=pk)
    ClientForm = ClientPhysicalPersonUpdateForm(request.POST or None, instance=branch.Client.pk and branch.Client)
    BranchForm = BranchPhysicalPersonUpdateForm(request.POST or None, instance=pk and branch)

    if request.POST:
        if ClientForm.is_valid() and BranchForm.is_valid():
            ClientForm.save()
            BranchForm.save()
            return redirect('index:card_client', branch_id=branch.pk)

    return render(request, "addclient/change_client.html", {
        'title': 'Изменение данных контрагента',
        'title_area': 'Контрагент',
        'title_small': 'Данные',
        'branch_data': branch,
        'form_client': ClientForm,
        'form_branch': BranchForm,
        'url_': reverse('contract_department:client_physicalperson_update', kwargs={'pk': pk})
    })


# ------------------------------------------------------------------------------------------------------------------
#                             Изменение контактов
# ------------------------------------------------------------------------------------------------------------------
@login_required()
@csrf_protect
def addclient_contacts(request, branch_id):
    branch_data = Branch.objects.get(id=branch_id)
    formset = ContactsFormSet(queryset=Contacts.objects.filter(Branch=branch_data))

    if request.POST:
        formset = ContactsFormSet(data=request.POST)
        for form in formset:
            if form.is_valid():
                if form.cleaned_data['Person_FIO']:
                    new_contact = form.save(commit=False)
                    new_contact.Branch = branch_data
                    new_contact.save()
                form.save()
                messages.success(request, u'Успешно обновлено: %s' % form.cleaned_data['Person_FIO'])

    return render(request, "addclient/new_contacts.html", {
        'title': 'Шаг №5',
        'title_area': 'Новый контрагент',
        'title_small': 'Ввод контактных лиц',
        'branch_id': branch_id,
        'formset': formset})



@login_required()
@csrf_protect
def addclient_usernote(request, branch_id, usernote_id=None):
    if usernote_id:
        usernote_data = UserNote.objects.get(id=usernote_id)
    else:
        usernote_data = []

    form = usernote_form(request.POST or None, instance=usernote_id and usernote_data)

    if request.POST:
        if form.is_valid():
            new_note = form.save(commit=False)
            new_note.Branch = Branch.objects.get(id=branch_id)
            new_note.user = request.user
            new_note.save()
            return redirect('index:card_client', branch_id=branch_id)

    return render(request, "usernote.html", {
        'title': ('Новая' if usernote_id is None else 'Запись №%s' % usernote_id),
        'title_area': 'Запись',
        'title_small': 'Данные контрагента',
        'branch_id': branch_id,
        'usernote_data': usernote_data,
        'form': form}
                  )


# ------------------------------------------------------------------------------------------------------------------
#                                 Удаление контакта
# ------------------------------------------------------------------------------------------------------------------
@login_required()
def dlt_contact(contact, **kwargs):
    contact_id = kwargs['contact_id']
    get_contact = Contacts.objects.get(id=contact_id)
    text = get_contact.Person_post + ' ' + get_contact.Person_FIO + ' ' + get_contact.Address_residence + ' ' + get_contact.Phone_city + ' ' + get_contact.Phone_mobile
    try:
        get_contact.delete()
        logging_event('delete_contact', None, text, 'system', '', None, get_contact.Branch.id)
        return redirect('contract_department:changedata_contacts', args=[get_contact.branch.id])
    except:
        return redirect('contract_department:changedata_contacts', args=[get_contact.branch.id])


@login_required()
def select_type_client_add(request):
    return render(request, 'addclient/select_type.html', {
        'title': 'Шаг №1',
        'title_area': 'Новый контрагент',
        'title_small': 'Выбор типа',
        'type_client': TypesClient.objects.all(),
    })


def logging_event(code_event, code_date=None, old_value='', app='base', cowork='system', type_dct=None,
                  scompany=None, id_branch=None, id_contract=None, id_object=None, id_act=None):

    logging.objects.create(app=SectionsApp.objects.get(slug=app), scompany=scompany,
                           type_dct=TypeDocument.objects.get(slug=type_dct),
                           event_code=Event.objects.get(slug=code_event), event_date=code_date,
                           user=User.objects.get(username=cowork), old_value=old_value,
                           branch_id=(int(id_branch) if id_branch else 0),
                           contract_id=(int(id_contract) if id_contract else 0),
                           object_id=(int(id_object) if id_object else 0),
                           act_id=(int(id_act) if id_act else 0))


def action_planned_base(app, date_event, code_event, value, branch=None, contract=None, object=None, scompany=None,
                        author=None):
    if author is None:
        author = User.objects.get(username='system')
    action_planned.objects.create(application=app, branch_id=branch, contract_id=contract, object_id=object,
                                  scompany_id=scompany,
                                  event_date=date_event, event_code=code_event, event_value=value, user=author)


@login_required()
def index(request):
    return render(request, 'index.html')


@login_required()
def search(request):
    results = []
    if request.is_ajax():
        q = request.GET.get('q')
        if q is not None:
            results = allviews_forsearch.objects.filter(
                Q(NameClient_full__icontains=q) |
                Q(NameClient_short__icontains=q) |
                Q(NameBranch__icontains=q) |
                Q(INN__icontains=q) |
                Q(Contract_internal__icontains=q) |
                Q(Contract_external__icontains=q) |
                Q(Object__icontains=q) |
                Q(Object_address__icontains=q)).distinct('id')[:10]
        # else:
        #     results = allviews_forsearch.objects.none()
        return render(request, 'results.html', {'results': results})


# def search(text):
#     results = allviews_forsearch.objects.none()
#     # Поиск по адресу
#     adrobject_rev = ''
#     for i in list(reversed(re.split(r'\s', text))):
#         if adrobject_rev != '':
#             adrobject_rev = adrobject_rev + ' ' + i
#         else:
#             adrobject_rev = i
#     search_regex_asc = r"%s" % re.sub(r'\s', '.+', text)
#     search_regex_desc = r"%s" % re.sub(r'\s', '.+', adrobject_rev)
#
#     if len(text) > 2:
#         results = allviews_forsearch.objects.filter(
#             Q(scompany_id__in=get_scompany_foruser()) | Q(scompany_id=0)
#         ).filter(
#             Q(NameClient_full__icontains=text) |
#             Q(NameClient_short__icontains=text) |
#             Q(NameBranch__icontains=text) |
#             Q(INN__icontains=text) |
#             Q(Contract_internal__icontains=text) |
#             Q(Contract_external__icontains=text) |
#             Q(Object__icontains=text) |
#             Q(Object_address__iregex=search_regex_asc) |
#             Q(Object_address__iregex=search_regex_desc)).distinct('id')
#
#     return results




@login_required()
@csrf_exempt
def advanced_search(request):
    text = ''
    results = []
    form = search_filter_form(request.POST)

    if request.GET:
        clear_string = re.sub(r'\s+', ' ', request.GET['search_text'])
        text = clear_string.strip()
        field = request.GET['field_search']
        try:
            active_object = request.GET['active_object']
        except:
            active_object = None
        # ----------  Поиск по адресу  ------------------------
        adrobject_rev = ''
        for i in list(reversed(re.split(r'\s', text))):
            if adrobject_rev != '':
                adrobject_rev = adrobject_rev + ' ' + i
            else:
                adrobject_rev = i
        search_regex_asc = r"%s" % re.sub(r'\s', '.+', text)
        search_regex_desc = r"%s" % re.sub(r'\s', '.+', adrobject_rev)
        # ----------------------------------------------------
        results = allviews_forsearch.objects.filter(
            Q(scompany_id__in=get_scompany_foruser()) | Q(scompany_id=0)
        )
        if field == "name_client":
            results = results.filter(
                Q(NameClient_full__icontains=text) |
                Q(NameClient_short__icontains=text) |
                Q(NameBranch__icontains=text))
        elif field == "name_object":
            results = results.filter(
                Q(Object__icontains=text))
        elif field == "address_object":
            results = results.filter(
                Q(Object_address__iregex=search_regex_asc) |
                Q(Object_address__iregex=search_regex_desc))
        elif field == "num_contract":
            results = results.filter(
                Q(Contract_internal__icontains=text) |
                Q(Contract_external__icontains=text))
        elif field == "inn":
            results = results.filter(Q(INN__icontains=text))
        else:
            results = results.filter(
                Q(NameClient_full__icontains=text) |
                Q(NameClient_short__icontains=text) |
                Q(NameBranch__icontains=text) |
                Q(INN__icontains=text) |
                Q(Contract_internal__icontains=text) |
                Q(Contract_external__icontains=text) |
                Q(Object__icontains=text) |
                Q(Object_address__iregex=search_regex_asc) |
                Q(Object_address__iregex=search_regex_desc))

        results = results.order_by('NameClient_short').distinct('id', 'NameClient_short')

        if field == "name_object" or field == "address_object":
            if active_object == 'on':
                results = results.filter(Object_status='active')

    return render(request, 'advanced_search.html', {
        'title': 'Поиск',
        'text_search': text,
        'search_filter_form': form,
        'title_area': 'Базовый',
        'title_small': 'Результаты поиска',
        'results': results
    })


# @login_required()
# @csrf_protect
# def advanced_search(request):
#     if request.POST:
#         form = advanced_search_form(request.POST)
#
#         if form.is_valid():
#             client      = request.POST['client']
#             inn         = request.POST['inn']
#             contract    = request.POST['contract']
#             num_object  = request.POST['num_object']
#             adr_object  = request.POST['adr_object']
#             results     = allviews_forsearch.objects.none()
#
#             if client:
#                 search_regex = r"%s" % re.sub(r'\s','.+',client)
#                 results = allviews_forsearch.objects.filter(
#                     Q(NameClient_full__iregex=search_regex) |
#                     Q(NameClient_short__iregex=search_regex) |
#                     Q(NameBranch__iregex=search_regex))
#             elif inn:
#                 inn = re.sub(r'\s','',inn)
#                 results = allviews_forsearch.objects.filter(INN__exact=inn)[:15]
#             elif contract:
#                 search_regex = r"%s" % contract.replace(' ','.+')
#                 results = allviews_forsearch.objects.filter(Q(Contract_internal__iregex=search_regex) | Q(Contract_external__iregex=search_regex))[:15]
#             elif num_object:
#                 num_object = re.sub(r'\s','',num_object)
#                 results = allviews_forsearch.objects.filter(Object__icontains=num_object)[:15]
#             elif adr_object:
#                 adr_object_rev = ''
#                 for i in list(reversed(re.split(r'\s', adr_object))):
#                     if adr_object_rev != '':
#                         adr_object_rev = adr_object_rev + ' ' + i
#                     else:
#                         adr_object_rev = i
#                 search_regex_asc = r"%s" % re.sub(r'\s','.+',adr_object)
#                 search_regex_desc = r"%s" % re.sub(r'\s','.+',adr_object_rev)
#                 results = allviews_forsearch.objects.filter(Q(Object_address__iregex=search_regex_asc) | Q(Object_address__iregex=search_regex_desc))[:15]
#
#             form = advanced_search_form(data={'client': client, 'inn': inn, 'contract': contract, 'num_object': num_object, 'adr_object': adr_object})
#
#             return render(request, 'advanced_search.html', {'form': form, 'results': results})
#         else:
#             return render(request, 'advanced_search.html', {'form': form})
#     else:
#         return render(request, 'advanced_search.html', {'form': advanced_search_form()})


def save_changedata_branch(request, branch_id):
    if request.POST:
        type_client = Branch.objects.get(id=branch_id).Client.TypeClient.slug

        if type_client == 'company':
            form = branch_form_company(request.POST or None, instance=branch_id and Branch.objects.get(id=branch_id))

        if form.is_valid():
            new_branch = form.save(commit=False)
            new_branch.Bank_BIK = ''
            new_branch.save()
            return redirect('index:card_client', args=[branch_id])


settings_send = {
    ('text_message', u'Ваш долг состовляет %s. Подробно по телефону (3537)26-54-45'),
}


#
# @login_required()
# def getlist_debtors(request, scompany_id):
#     args = {}
#     i = 0
#     args.update(csrf(request))
#     scompany = ServingCompanyBranch.objects.get(id=scompany_id).NameBranch
#
#     if request.POST:
#         smsc = SMSC()
#         check_values = request.POST.getlist('tag[]')
#
#         for item in check_values:
#             branch_id = int(request.POST['client_%d' % int(item)])
#             phone = request.POST['phone_%d' % int(item)]
#             summ = request.POST['summdebt_%d' % int(item)]
#
#             sms_str = smsc.send_sms('7%s' % phone, u'Ваш долг %s %s. Подробно по телефону (3537)26-54-45' % scompany,
#                                     summ, sender="amuletpco")
#             logging_sms.objects.create(client_id=Branch.objects.get(id=branch_id), phone=phone,
#                                        summ_debt=Decimal(summ.replace(',', '.')), sms_id=int(sms_str[0]),
#                                        price_sms=Decimal(sms_str[2]))
#
#         time.sleep(60)
#         return render(request, 'send_sms.html', {'logs': logging_sms.objects.filter(status_sms__isnull=True)})
#     else:
#         return render(request, 'send_sms.html', args)


# def copy_dataclient_other_type(request, branch_id):
#     branch_data = Branch.objects.get(id=branch_id)
#     new_client = Client.objects.create(TypeClient, OKOPF, GroupClient, NameClient_full = models.CharField(u'Полное наименование', max_length=300)
#     NameClient_short = models.CharField(u'Краткое наименование', max_length=300, blank=True)
#     Management_post = models.CharField(u'Должность руководителя', max_length=100, blank=True)
#     Management_name = models.CharField(u'ФИО руководителя', max_length=50, blank=True)
#     Address_reg = models.CharField(u'Адрес', max_length=300)
#     INN = models.CharField(u'ИНН', max_length=12, blank=True)
#     OGRN = models.CharField(u'ОГРН', max_length=20, blank=True)
#     OKPO = models.CharField(u'ОКПО', max_length=20, blank=True)
#     OKVED = models.CharField(u'ОКВЭД', max_length=20, blank=True)
#     PassportSerNum = models.CharField(u'Серия и номер паспорта', max_length=12, null=True, blank=True)
#     DatePassport = models.DateField(u'Дата выдачи паспорта', null=True, blank=True)
#     IssuedByPassport = models.TextField(u'Кем выдан пасспорт', null=True, blank=True)
#     Alien = models.BooleanField(u'Не является гражданином РФ', default=False, blank=True))