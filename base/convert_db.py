import pymysql.cursors
import datetime
import re

from django.contrib.auth.models import User
from django.db.models import Sum, FloatField
from django.http import HttpResponseRedirect

from accounting.models import credited_with_paid, start_balance
from base.models import Client, Branch, ServingCompanyBranch, Event, SectionsApp, logging, Contacts
from build_service.models import BuildTemplateDocuments, BuildServiceContract, BuildServiceAct, BuildServiceObject
from maintenance_service.models import MaintenanceTemplateDocuments, MaintenancePereodicAccrual, \
    MaintenancePereodicService, MaintenanceServiceObject, \
    MaintenanceServiceContract
from reference_books.models import TypesClient, FormsSchet, TypeDocument, TypeObject, PaymentMethods, StatusSecurity, \
    ListPosts, PowersOfficeActs, City, TypeWork
from tech_security.models import TechSecurityContract, TechTemplateDocuments, TechSecurityObject, \
    TechSecurityObjectPeriodSecurity

__author__ = 'bondarenkoav'

list_city = ['oren']


def get_post(string):
    posts = ListPosts.objects.all()
    if 'иректор' in string:
        if 'инанс' in string:
            post = posts.get(NamePost='Финансовый директор')
        elif 'енерал' in string:
            post = posts.get(NamePost='Генеральный директор')
        elif 'аместит' in string:
            post = posts.get(NamePost='Заместитель директора')
        elif 'егион' in string:
            post = posts.get(NamePost='Региональный директор')
        elif 'сполнит' in string:
            post = posts.get(NamePost='Исполнительный директор')
        else:
            post = posts.get(NamePost='Директор')
    elif 'правляющ' in string:
        if 'аместит' in string:
            post = posts.get(NamePost='Заместитель управляющего')
        else:
            post = posts.get(NamePost='Управляющий')
    elif 'врач' in string:
        if 'лавн' in string:
            post = posts.get(NamePost='Главный врач')
        else:
            post = posts.get(NamePost='Другое')
    elif 'редседател' in string:
        if 'равлен' in string:
            post = posts.get(NamePost='Председатель Правления')
        else:
            post = posts.get(NamePost='Другое')
    else:
        post = posts.get(NamePost='Другое')
    return post


def get_powersoffice(string):
    powersofficeacts = PowersOfficeActs.objects.all()
    if 'Устав' in string or 'устав' in string:
        powersoffice = powersofficeacts.get(NameActs='Устава')
    elif 'оверенност' in string:
        powersoffice = powersofficeacts.get(NameActs='доверенности')
    elif 'Положени' in string or 'положени' in string:
        powersoffice = powersofficeacts.get(NameActs='положения')
    else:
        powersoffice = powersofficeacts.get(NameActs='Другое')


def get_pass(passdata, type):
    if passdata != '':
        if type == 'sernum_pass':
            string = passdata.split('/')
            return string[0]
        elif type == 'date_pass':
            string = passdata.split('/')
            if string[1] == '' or datetime.datetime.strptime(string[1], "%d.%m.%Y") == False:
                return datetime.datetime.strptime('01.01.2010', "%d.%m.%Y")
            else:
                return datetime.datetime.strptime(string[1], "%d.%m.%Y")
        elif type == 'issuedby_pass':
            string = passdata.split('/')
            return string[2]


def replace_symbol(string):
    clear_string = string.replace('/', '"')
    clear_string = clear_string.replace('«', '"')
    clear_string = clear_string.replace('»', '"')
    clear_string = re.sub(r'\s+', ' ', clear_string)
    clear_string = clear_string.strip()
    return clear_string


def phone_clean(string):
    # clear_string = re.sub(r'^?[8]', '', string)
    clear_string = string.replace('.', '')
    clear_string = clear_string.replace(',', '')
    clear_string = clear_string.replace('-', '')
    clear_string = re.sub(r'\s+', '', clear_string)
    return clear_string


def get_start_balance(branch_id, scompany_id):
    date_startbalance = datetime.date(2018, 1, 1)
    scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
    branch_data = Branch.objects.get(id=branch_id)
    summ_startbalance = credited_with_paid.objects. \
        filter(branch=branch_data, scompany=scompany_data, date_event__lt=date_startbalance). \
        aggregate(summ=Sum('summ', output_field=FloatField()))
    return summ_startbalance


def convertbd(request):
    conn = ''
    try:
        conn = pymysql.connect(host='192.168.41.232',
                               user='root',
                               password='080967',
                               database='client',
                               charset="utf8",
                               cursorclass=pymysql.cursors.DictCursor)

    except pymysql.Error as err:
        conn.close()
        return HttpResponseRedirect('/')

    cur = conn.cursor(pymysql.cursors.DictCursor)

    query_string_clients = "SELECT IDNameClient,TypeClient,Naimenovanie,FullNaimenovanie,YurAdress,Email,OGRN," \
                           "BankClient,Passport,VistovlenieSchetov,INN,EDO FROM get_client_copy ORDER BY Naimenovanie ASC"

    cur.execute(query_string_clients)
    client = cur.fetchall()

    sections_app = SectionsApp.objects.all()
    type_dct = TypeDocument.objects.all()
    events = Event.objects.all()
    user = User.objects.get(username='system')
    type_payment = PaymentMethods.objects.all()
    typeobj = TypeObject.objects.get(slug="room")

    for row1 in client:
        PostAdress = KPP = SMSNumber = VistavlSchetov = Sobstvennik = OrgPoluch = type_oplata = ''
        edo = False
        IDNC = row1['IDNameClient']
        Naimenovanie = replace_symbol(row1['Naimenovanie'])[:299]
        FullNaimenovanie = replace_symbol(row1['FullNaimenovanie'])[:299]

        if row1['TypeClient'] == 'yurlico':
            typeclient = TypesClient.objects.get(slug="company")
        elif row1['TypeClient'] == 'ip':
            typeclient = TypesClient.objects.get(slug="businessman")
        else:
            typeclient = TypesClient.objects.get(slug="physical_person")

        if row1['TypeClient'] == 'yurlico':
            query_client = Client.objects.create(
                TypeClient=typeclient,
                INN=row1['INN'][:12],
                OGRN=row1['OGRN'][:20],
                NameClient_short=Naimenovanie[:299],
                NameClient_full=FullNaimenovanie[:299],
                Address_reg=replace_symbol(row1['YurAdress'])[:299]
            )
        else:
            pass_data = row1['Passport']
            pass_data = pass_data.strip()
            pass_data = re.sub(r"\s{2,}", ' ', pass_data)
            m = re.match(r"\d{4}\s{1}\d{6}\/\d{2}\.\d{2}\.\d{4}/.*", pass_data)

            if m:
                PassportSerNum = get_pass(pass_data, 'sernum_pass')
                DatePassport = get_pass(pass_data, 'date_pass')
                IssuedByPassport = get_pass(pass_data, 'issuedby_pass')

                query_client = Client.objects.create(
                    TypeClient=typeclient,
                    INN=row1['INN'][:12],
                    OGRN=row1['OGRN'][:20],
                    NameClient_short=Naimenovanie,
                    NameClient_full=FullNaimenovanie,
                    Address_reg=replace_symbol(row1['YurAdress'])[:299],
                    PassportSerNum=PassportSerNum,
                    DatePassport=DatePassport,
                    IssuedByPassport=IssuedByPassport.strip()
                )
            else:
                query_client = Client.objects.create(
                    TypeClient=typeclient,
                    INN=row1['INN'][:12],
                    OGRN=row1['OGRN'][:20],
                    NameClient_short=Naimenovanie,
                    NameClient_full=FullNaimenovanie,
                    Address_reg=replace_symbol(row1['YurAdress'])[:299]
                )

        for cur_city in list_city:
            query_string_clients_subdata = "SELECT %s_PostAdress as PostAdress, %s_KPP as KPP, %s_SMSNumber as SMSNumber, " \
                                           "%s_VistavlSchetov as VistavlSchetov, %s_Sobstvennik as Sobstvennik, " \
                                           "%s_OrgPoluch as OrgPoluch, EDO FROM billing_tmp WHERE IDNameClient = %d" % (
                                               cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, IDNC)
            cur.execute(query_string_clients_subdata)
            client_subdata = cur.fetchall()

            for row2 in client_subdata:
                PostAdress = row2['PostAdress']
                KPP = row2['KPP']
                SMSNumber = row2['SMSNumber']
                VistavlSchetov = row2['VistavlSchetov']
                OrgPoluch = row2['OrgPoluch']
                Sobstvennik = row2['Sobstvennik']

            if OrgPoluch != '':
                if VistavlSchetov == 'obj':
                    formsschet = FormsSchet.objects.get(slug="form_object")
                else:
                    formsschet = FormsSchet.objects.get(slug="form_contract")

                if row2['EDO'] == 1:
                    edo = True

                if row1['TypeClient'] == 'yurlico':
                    query_branch = Branch.objects.create(
                        Client=query_client,
                        NameBranch=Naimenovanie.strip()[:199],
                        PowersOffice_name=get_powersoffice(Sobstvennik),
                        Management_post=get_post(Sobstvennik),
                        Management_data=Sobstvennik,
                        Address_post=PostAdress,
                        KPP=KPP,
                        Phone_SMS=SMSNumber,
                        Bank_Details=row1['BankClient'],
                        FormsSchet=formsschet,
                        EDO=edo
                    )
                else:
                    query_branch = Branch.objects.create(
                        Client=query_client,
                        Phone_SMS=SMSNumber,
                        Bank_Details=row1['BankClient'],
                        FormsSchet=formsschet,
                        EDO=edo
                    )
                # -------------------------------------------- Контакты -----------------------------------------------
                query_string_contacts = "SELECT fullname, trash FROM %s_contacts WHERE IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_contacts)
                contacts = cur.fetchall()

                for row3 in contacts:
                    email_list = re.findall(r'[\w\.-]+@[\w\.-]+', row3['trash'])
                    email = (email_list[0] if len(email_list) > 0 else None)

                    city_list = re.findall(r'[,]?[\s]?[2-6]{1}\d{5}', row3['trash'])
                    if len(city_list) == 0:
                        city_list = re.findall(r'^[2-7]{1}\d{5}', row3['trash'])
                    if len(city_list) > 0:
                        p = city_list[0]
                        city = (phone_clean(city_list[0]))
                    else:
                        city = None

                    mobile_list = re.findall(r'[9]{1}\d{9}', row3['trash'])
                    if len(mobile_list) == 0:
                        mobile_list = re.findall(r'^\d{11}', row3['trash'])
                    if len(mobile_list) > 0:
                        mobile = (phone_clean(mobile_list[0]))
                    else:
                        mobile = None

                    Contacts.objects.create(
                        Branch=query_branch,
                        Person_FIO=row3['fullname'],
                        Phone_mobile=mobile,
                        Phone_city=city,
                        Email=email
                    )

                # -------------------------------------------- Техническая охрана -------------------------------------
                typedoc_techsecur = TypeDocument.objects.get(slug="tech_security_contract")
                scompany_techsecur = ServingCompanyBranch.objects.get(id=15)

                query_string_contract = "select distinct `%s_dogovor`.`ID` AS `ID`, `nDogovor`, `nDogovorClient`, " \
                                        "`DataZakl`, `DataRastor` " \
                                        "from ((`%s_object` " \
                                        "join `%s_vipiska` on((`%s_vipiska`.`IDObject` = `%s_object`.`IDObject`))) " \
                                        "join `%s_dogovor` on((`%s_dogovor`.`ID` = `%s_object`.`IDClient`))) " \
                                        "where `%s_vipiska`.`Date` >= '2018-01-01' AND  %s_dogovor.IDNameClient = %d " \
                                        "ORDER BY `ID` Asc " % (cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, IDNC)

                cur.execute(query_string_contract)
                techsecur_contract = cur.fetchall()

                for row4 in techsecur_contract:
                    IDContractTech = row4['ID']
                    template_techsecur = TechTemplateDocuments.objects.get(id=1)

                    query_techsecur_contract = TechSecurityContract.objects.create(
                        TypeDocument=typedoc_techsecur,
                        Branch=query_branch,
                        ServingCompany=scompany_techsecur,
                        NumContractInternal=row4['nDogovor'][:29],
                        NumContractBranch=row4['nDogovorClient'][:29],
                        DateConclusion=row4['DataZakl'],
                        DateTermination=row4['DataRastor'],
                        TemplateDocuments=template_techsecur,
                        PaymentDate=0, ResponsibilityCost=0, PaymentAfter=False
                    )

                    query_string_object = "SELECT * FROM %s_object WHERE IDClient = %d" % (cur_city, IDContractTech)

                    cur.execute(query_string_object)
                    techsecur_object = cur.fetchall()

                    for row5 in techsecur_object:
                        IDObjectTech = row5['IDObject']
                        if row5['FormaOplat'] == 1:
                            formpayment = PaymentMethods.objects.get(slug="bank")
                        elif row5['FormaOplat'] == 3:
                            formpayment = PaymentMethods.objects.get(slug="offsetting")
                        else:
                            formpayment = PaymentMethods.objects.get(slug="сheckout")

                        if row5['vOhrane'] == 1:
                            status = StatusSecurity.objects.get(slug="active")
                        else:
                            status = StatusSecurity.objects.get(slug="noactive")
                        city_data = City.objects.get(slug=cur_city)

                        query_techsecur_object = TechSecurityObject.objects.create(
                            TechSecurityContract=query_techsecur_contract,
                            NumObjectPCN=row5['nObject'],
                            TypeObject=typeobj,
                            NameObject=row5['nameObject'][:99],
                            AddressObject=row5['AdresObj'][:300],
                            PaymentMethods=formpayment,
                            PriceNoDifferent=row5['abonplata'],
                            StatusSecurity=status,
                        )

                        # -------------------  Получаем периоды охраны и абонентскую по техохране  -----
                        query_string_abonplata = "SELECT * FROM %s_abonplata WHERE marker<>10 AND IDObject = %d" % (
                            cur_city, IDObjectTech)
                        cur.execute(query_string_abonplata)
                        techsecur_abon = cur.fetchall()
                        event = None

                        for row6 in techsecur_abon:
                            if row6['marker'] == 3:
                                if row6['upd_marker'] == 0:
                                    event = Event.objects.get(
                                        slug='change_activationSecur_object')  # постановка в охрану
                                elif row6['upd_marker'] == 2:
                                    event = Event.objects.get(
                                        slug='change_numObjectPCN_object')  # сменился номер объекта
                            elif row6['marker'] == 4:
                                event = Event.objects.get(slug='change_activationSecur_object')  # снятие с охраны
                            else:
                                event = Event.objects.get(slug='unknown_event')  # все события которые не попали в if

                            if event:
                                TechSecurityObjectPeriodSecurity.objects.create(
                                    TechSecurityObject=query_techsecur_object,
                                    PeriodPrice=row6['abonplat'],
                                    DateStart=row6['DateOn'],
                                    DateEnd=row6['DateOff'],
                                    event_code=event
                                )

                        # -----------------------  Получаем начисления по объекту --------------------------
                        query_string_credits = "SELECT Date, Nach " \
                                               "FROM %s_vipiska " \
                                               "WHERE Date>='2018-01-01' AND IDObject = %d" % (
                            cur_city, IDObjectTech)
                        cur.execute(query_string_credits)
                        techsecur_nach = cur.fetchall()

                        for row7 in techsecur_nach:
                            credited_with_paid.objects.create(
                                object=query_techsecur_object.id,
                                dct=query_techsecur_contract.id,
                                type_dct=typedoc_techsecur,
                                branch=query_branch,
                                scompany=scompany_techsecur,
                                date_event=row7['Date'],
                                summ=row7['Nach'],
                                Create_user=user,
                                Update_user=user
                            )

                        # -------------------  Получаем события по объекту --------------------------
                        query_string_events = "SELECT DatavOhrane, marker, old_znach, " \
                                              "Date FROM %s_status_dog " \
                                              "WHERE DatavOhrane > '2018-01-01' AND IDObject = %d" % (
                            cur_city, IDObjectTech)
                        cur.execute(query_string_events)
                        techsecur_event = cur.fetchall()

                        for row8 in techsecur_event:
                            if row8['marker'] == 6:  # смена № объекта
                                logging.objects.create(app=sections_app.get(slug='tech_security'),
                                                       branch_id=query_branch.id,
                                                       type_dct=type_dct.get(slug='tech_security_contract'),
                                                       contract_id=query_techsecur_contract.id,
                                                       object_id=query_techsecur_object.id,
                                                       event_code=events.get(slug='change_numObjectPCN_object'),
                                                       event_date=row8['DatavOhrane'],
                                                       add_date=row8['Date'],
                                                       old_value=row8['old_znach'], user=user)

                            if row8['marker'] == 8:  # смена способа оплаты
                                logging.objects.create(app=sections_app.get(slug='tech_security'),
                                                       branch_id=query_branch.id,
                                                       type_dct=type_dct.get(slug='tech_security_contract'),
                                                       contract_id=query_techsecur_contract.id,
                                                       object_id=query_techsecur_object.id,
                                                       event_code=events.get(slug='change_paymentMethods_object'),
                                                       event_date=row8['DatavOhrane'],
                                                       add_date=row8['Date'],
                                                       old_value=row8['old_znach'], user=user)

                            if row8['marker'] == 3:  # смена стоимости охраны
                                logging.objects.create(app=sections_app.get(slug='tech_security'),
                                                       branch_id=query_branch.id,
                                                       type_dct=type_dct.get(slug='tech_security_contract'),
                                                       contract_id=query_techsecur_contract.id,
                                                       object_id=query_techsecur_object.id,
                                                       event_code=events.get(slug='change_priceNoDifferent_object'),
                                                       event_date=row8['DatavOhrane'],
                                                       add_date=row8['Date'],
                                                       old_value=row8['old_znach'], user=user)

                            if row8['marker'] == 4:  # ставим в охрану
                                logging.objects.create(app=sections_app.get(slug='tech_security'),
                                                       branch_id=query_branch.id,
                                                       type_dct=type_dct.get(slug='tech_security_contract'),
                                                       contract_id=query_techsecur_contract.id,
                                                       object_id=query_techsecur_object.id,
                                                       event_code=events.get(slug='change_activationSecur_object'),
                                                       event_date=row8['DatavOhrane'],
                                                       add_date=row8['Date'],
                                                       old_value=row8['old_znach'], user=user)

                            if row8['marker'] == 5:  # снимаем с охраны
                                logging.objects.create(app=sections_app.get(slug='tech_security'),
                                                       branch_id=query_branch.id,
                                                       type_dct=type_dct.get(slug='tech_security_contract'),
                                                       contract_id=query_techsecur_contract.id,
                                                       object_id=query_techsecur_object.id,
                                                       event_code=events.get(slug='change_deactivationSecur_object'),
                                                       event_date=row8['DatavOhrane'],
                                                       add_date=row8['Date'],
                                                       old_value=row8['old_znach'], user=user)
                #
                # # ----------------------------- Оплаты по техохране -------------------------------------------------
                query_string_paids = "SELECT Date, Itogo_uplach, typeOplata " \
                                     "FROM %s_vipiska_log " \
                                     "WHERE Date >= '2018-01-01' AND Itogo_uplach>0 AND IDNameClient = %d" % (cur_city, IDNC)
                cur.execute(query_string_paids)
                techsecur_paid = cur.fetchall()
                first_techsecur_contract = TechSecurityContract.objects.filter(Branch=query_branch).last()

                if first_techsecur_contract:
                    for row9 in techsecur_paid:
                        if row9['typeOplata'] == 'bank':
                            type_oplata = type_payment.get(slug='bank')
                        elif row9['typeOplata'] == 'kassa':
                            type_oplata = type_payment.get(slug='сheckout')
                        else:
                            type_oplata = None

                        credited_with_paid.objects.create(
                            dct=first_techsecur_contract.id,
                            type_dct=typedoc_techsecur,
                            branch=query_branch,
                            scompany=scompany_techsecur,
                            date_event=row9['Date'],
                            summ=row9['Itogo_uplach'] * (-1),
                            payment_methods=type_oplata,
                            Create_user=user,
                            Update_user=user
                        )

                # ---------------------------- Стартовое сальдо ------------------------------------------------------
                query_string_startsaldo_2011 = "SELECT SUM(%s_SummaOhrana) as start_saldo " \
                                               "FROM billing " \
                                               "WHERE IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_2011)
                dict_techsecur_startsaldo_2011 = cur.fetchone()
                if dict_techsecur_startsaldo_2011['start_saldo']:
                    techsecur_startsaldo_2011 = dict_techsecur_startsaldo_2011['start_saldo']
                else:
                    techsecur_startsaldo_2011 = 0

                query_string_startsaldo_credits = "SELECT SUM(Nach) as sum_credits " \
                                                  "FROM %s_vipiska " \
                                                  "WHERE Date < '2018-01-01' AND IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_credits)
                dict_techsecur_startsaldo_credits = cur.fetchone()
                if dict_techsecur_startsaldo_credits['sum_credits']:
                    techsecur_startsaldo_credits = dict_techsecur_startsaldo_credits['sum_credits']
                else:
                    techsecur_startsaldo_credits = 0

                query_string_startsaldo_paids = "SELECT SUM(Itogo_uplach) as sum_paids " \
                                                "FROM %s_vipiska_log " \
                                                "WHERE Date < '2018-01-01' AND IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_paids)
                dict_techsecur_startsaldo_paids = cur.fetchone()
                if dict_techsecur_startsaldo_paids['sum_paids']:
                    techsecur_startsaldo_paids = dict_techsecur_startsaldo_paids['sum_paids']
                else:
                    techsecur_startsaldo_paids = 0

                secure_summ_startsaldo = float(techsecur_startsaldo_2011) * (-1) + float(
                    techsecur_startsaldo_credits) + float(techsecur_startsaldo_paids) * (-1)

                start_balance.objects.create(
                    branch=query_branch,
                    scompany=scompany_techsecur,
                    date_saldo=datetime.date(2018, 1, 1),
                    summ=secure_summ_startsaldo,
                    city=cur_city
                )

                # --------------------------- Монтаж -----------------------------------------------------------------
                typedoc_build = type_dct.get(slug="build_service_contract")
                scompany_build = ServingCompanyBranch.objects.get(id=3)

                # cowork = CoWorkers.objects.get(id=3)

                query_string_contract_build = "SELECT DISTINCT IDService, nDogovorService, DataZaklService, " \
                                              "Summa_montag, FormaOplat, Montagnik1, Montagnik2, Montagnik3, " \
                                              "Montagnik4, Montagnik5, IDNumNakladRashod, Data " \
                                              "FROM %s_dogovor_service " \
                                              "INNER JOIN %s_vipiska_service ON %s_dogovor_service.IDService = %s_vipiska_service.cod_doc " \
                                              "WHERE YEAR(%s_vipiska_service.`Data`) = YEAR(CURDATE()) AND %s_vipiska_service.IDNameClient = %d " \
                                              "ORDER BY DataZaklService ASC" % (
                    cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, IDNC)
                cur.execute(query_string_contract_build)
                build_contract = cur.fetchall()

                for row10 in build_contract:
                    template_build = BuildTemplateDocuments.objects.get(id=1)

                    if row10['FormaOplat'] == 1:
                        formpayment = PaymentMethods.objects.get(slug="bank")
                    elif row10['FormaOplat'] == 2:
                        formpayment = PaymentMethods.objects.get(slug="сheckout")
                    else:
                        formpayment = PaymentMethods.objects.get(slug="offsetting")

                    query_build_contract = BuildServiceContract.objects.create(
                        TypeDocument=typedoc_build,
                        Branch=query_branch,
                        ServingCompany=scompany_techsecur,
                        NumContractInternal=row10['nDogovorService'][:29],
                        DateConclusion=row10['DataZaklService'],
                        TemplateDocuments=template_build
                    )

                    query_string_object_build = "SELECT * FROM %s_object_service WHERE IDClientService = '%d'" % (
                        cur_city, row10['IDService'])
                    cur.execute(query_string_object_build)
                    build_object = cur.fetchall()

                    for row11 in build_object:
                        BuildServiceObject.objects.create(
                            BuildServiceContract=query_build_contract,
                            TypeObject=typeobj,
                            NameObject=row11['nameObject'][:99],
                            AddressObject=row11['AdresObjService'][:300],
                            PaymentMethods=formpayment,
                            Price=row11['summa_montag'],
                            DateStart=row11['DataStart'],
                            DateEnd=row11['DataEnd']
                        )

                    # ----------------------  Получаем начисления по договору -----------------------------------------
                    query_string_credits_build = "SELECT Data, Summa_nachisl " \
                                                 "FROM %s_vipiska_service " \
                                                 "WHERE Data >= '2019-01-01' AND type_doc='dog' AND cod_doc = '%d'" % (
                        cur_city, row10['IDService'])
                    cur.execute(query_string_credits_build)
                    build_nach = cur.fetchall()

                    for row12 in build_nach:
                        credited_with_paid.objects.update_or_create(
                            dct=query_build_contract.id,
                            type_dct=typedoc_build,
                            branch=query_branch,
                            date_event=row12['Data'],
                            scompany=scompany_build,
                            summ=row12['Summa_nachisl'],
                            Create_user=user,
                            Update_user=user
                        )

                # ------------------------------------ Акты ----------------------------------------------------------
                cur.execute(
                    "SELECT ID,DataRabot,NaimenovanieRabot,Stoimost,PS,IDzayavka,AdressRabot,VidRabot "
                    "FROM %s_akt "
                    "INNER JOIN vid_rabot ON vid_rabot.IDRabot = %s_akt.IDVidRabot "
                    "WHERE DataRabot >= '2019-01-01' AND %s_akt.IDNameClient='%d'" % (
                        cur_city, cur_city, cur_city, IDNC))
                build_akt = cur.fetchall()
                typework = ''

                for row13 in build_akt:
                    if TypeWork.objects.filter(Name__contains=row13['VidRabot']):
                        typework = TypeWork.objects.filter(Name__contains=row13['VidRabot']).first().Name

                    BuildServiceAct.objects.create(
                        TypeDocument=TypeDocument.objects.get(slug="build_service_act"),
                        Branch=query_branch,
                        ServingCompany=scompany_build,
                        AddressObject=row13['AdressRabot'],
                        DateWork=row13['DataRabot'],
                        TypeWork_descript=typework + ' ' + row13['NaimenovanieRabot'],
                        Price=row13['Stoimost'],
                        Descriptions=row13['PS']
                    )

                    # ----------------------  Получаем начисления по объекту -----------------------------------------
                    cur.execute(
                        "SELECT Data, Summa_nachisl "
                        "FROM %s_vipiska_service "
                        "WHERE Data >= '2019-01-01' AND type_doc='act' AND cod_doc = '%d'" % (
                            cur_city, row13['ID']))
                    build_nach_act = cur.fetchall()

                    for row14 in build_nach_act:
                        credited_with_paid.objects.update_or_create(
                            dct=query_build_contract.id,
                            type_dct=type_dct.get(slug="build_service_act"),
                            branch=query_branch,
                            date_event=row14['Data'],
                            scompany=scompany_build,
                            summ=row14['Summa_nachisl'],
                            Create_user=user,
                            Update_user=user
                        )

                # ------------------------------------- ТО -----------------------------------------------------------
                typedoc_maintenance = TypeDocument.objects.get(slug="maintenance_service_contract")
                scompany_maintenance = ServingCompanyBranch.objects.get(id=3)

                # query_string_contract_maintenance = "SELECT DISTINCT IDTO, nDogovorTO, DataZaklTO, DataRastorTO, " \
                #                                     "SummaTO, FormaOplat, PeriodicObsluj, PeriodicOplaty " \
                #                                     "FROM %s_dogovor_to " \
                #                                     "INNER JOIN %s_vipiska_service ON %s_dogovor_to.IDTO = %s_vipiska_service.cod_doc " \
                #                                     "WHERE YEAR(%s_vipiska_service.`Data`) = YEAR(CURDATE()) AND %s_vipiska_service.IDNameClient = %d " \
                #                                     "ORDER BY DataZaklTO ASC" % (cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, IDNC)

                query_string_contract_maintenance = "SELECT DISTINCT IDTO, nDogovorTO, DataZaklTO, DataRastorTO, " \
                                                    "SummaTO, FormaOplat, PeriodicObsluj, PeriodicOplaty " \
                                                    "FROM %s_dogovor_to " \
                                                    "INNER JOIN %s_object_to ON %s_dogovor_to.IDTO = %s_object_to.IDClientTO " \
                                                    "WHERE (%s_dogovor_to.DataRastorTO > CURDATE() OR %s_dogovor_to.DataRastorTO = '0001-01-01') AND " \
                                                    "(%s_object_to.DataEnd > CURDATE() OR oren_object_to.DataEnd = '0001-01-01') AND " \
                                                    "%s_dogovor_to.IDNameClient = %d " \
                                                    "ORDER BY DataZaklTO ASC" % (cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, cur_city, IDNC)

                cur.execute(query_string_contract_maintenance)
                maintenance_contract = cur.fetchall()

                for r, row15 in enumerate(maintenance_contract):
                    template_maintenance = MaintenanceTemplateDocuments.objects.get(id=1)

                    if row15['PeriodicObsluj'] == 'mesyac':
                        pereodicservice = MaintenancePereodicService.objects.get(slug='monthly')
                    elif row15['PeriodicObsluj'] == 'poluyear':
                        pereodicservice = MaintenancePereodicService.objects.get(slug='halfyear')
                    else:
                        pereodicservice = MaintenancePereodicService.objects.get(slug='quarterly')

                    if row15['PeriodicOplaty'] == 'mesyac':
                        pereodicaccrual = MaintenancePereodicAccrual.objects.get(slug='monthly')
                    elif row15['PeriodicOplaty'] == 'poluyear':
                        pereodicaccrual = MaintenancePereodicAccrual.objects.get(slug='halfyear')
                    else:
                        pereodicaccrual = MaintenancePereodicAccrual.objects.get(slug='quarterly')

                    if row15['FormaOplat'] == 1:
                        formpayment = PaymentMethods.objects.get(slug="bank")
                    elif row15['FormaOplat'] == 2:
                        formpayment = PaymentMethods.objects.get(slug="сheckout")
                    else:
                        formpayment = PaymentMethods.objects.get(slug="offsetting")

                    query_maintenance_contract = MaintenanceServiceContract.objects.create(
                        TypeDocument=typedoc_maintenance,
                        Branch=query_branch,
                        ServingCompany=scompany_maintenance,
                        NumContractInternal=row15['nDogovorTO'][:29],
                        DateConclusion=row15['DataZaklTO'],
                        DateTermination=row15['DataRastorTO'],
                        TemplateDocuments=template_maintenance,
                        NameOfService='',
                        PereodicAccrual=pereodicaccrual,
                        PereodicService=pereodicservice
                    )

                    query_string_object_maintenance = "SELECT * FROM %s_object_to WHERE IDClientTO = '%d'" % (
                        cur_city, row15['IDTO'])
                    cur.execute(query_string_object_maintenance)
                    build_object = cur.fetchall()

                    for row16 in build_object:
                        MaintenanceServiceObject.objects.create(
                            MaintenanceServiceContract=query_maintenance_contract,
                            TypeObject=typeobj,
                            NameObject=row16['nameObjectTO'][:99],
                            AddressObject=row16['AdresObjTO'][:300],
                            PaymentMethods=formpayment,
                            Price=row16['summa_to'],
                            DateStart=row16['DataStart'],
                            DateEnd=row16['DataEnd']
                        )

                    # ------------------------  Получаем начисления по договору ---------------------------------------
                    cur.execute(
                        "SELECT Data, Summa_nachisl "
                        "FROM %s_vipiska_service "
                        "WHERE Data >= '2019-01-01' And type_doc='to' AND cod_doc = '%d'" % (
                            cur_city, row15['IDTO']))
                    build_nach = cur.fetchall()

                    for row17 in build_nach:
                        credited_with_paid.objects.update_or_create(
                            dct=query_maintenance_contract.id,
                            type_dct=typedoc_maintenance,
                            branch=query_branch,
                            date_event=row17['Data'],
                            scompany=scompany_maintenance,
                            summ=row17['Summa_nachisl'],
                            Create_user=user,
                            Update_user=user
                        )

                # -------------------------------------------- Оплаты ------------------------------------------------
                cur.execute(
                    "SELECT Data, Summa_oplata, typeOplata "
                    "FROM %s_vipiska_service "
                    "WHERE Data >= '2019-01-01' And Summa_oplata>0 and IDNameClient = '%d'" % (
                        cur_city, IDNC))
                build_uplach = cur.fetchall()

                last_service_contract = []
                last_build_contract = BuildServiceContract.objects.filter(Branch=query_branch).last()
                last_maintenance_contract = MaintenanceServiceContract.objects.filter(Branch=query_branch).last()

                if last_build_contract or last_maintenance_contract:
                    if last_build_contract:
                        last_service_contract = last_build_contract
                        typedoc = typedoc_build
                    else:
                        last_service_contract = last_maintenance_contract
                        typedoc = typedoc_maintenance

                if last_service_contract:
                    for row18 in build_uplach:
                        if row18['typeOplata'] == 'bank':
                            type_oplata = type_payment.get(slug='bank')
                        elif row18['typeOplata'] == 'kassa':
                            type_oplata = type_payment.get(slug='сheckout')
                        else:
                            type_oplata = None

                        if row18['Summa_oplata'] > 0:
                            credited_with_paid.objects.update_or_create(
                                dct=last_service_contract.id,
                                type_dct=typedoc,
                                branch=query_branch,
                                date_event=row18['Data'],
                                scompany=scompany_build,
                                summ=row18['Summa_oplata'] * (-1),
                                payment_methods=type_oplata,
                                Create_user=user,
                                Update_user=user
                            )

                # -------------------------------------------- Стартовое сальдо ---------------------------------------
                query_string_startsaldo_2011 = "SELECT SUM(%s_SummaService) as start_saldo " \
                                               "FROM billing " \
                                               "WHERE IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_2011)
                dict_buildservice_startsaldo_2011 = cur.fetchone()
                if dict_buildservice_startsaldo_2011['start_saldo']:
                    buildservice_startsaldo_2011 = dict_buildservice_startsaldo_2011['start_saldo']
                else:
                    buildservice_startsaldo_2011 = 0

                query_string_startsaldo_credits = "SELECT SUM(Summa_nachisl) as sum_credits " \
                                                  "FROM %s_vipiska_service " \
                                                  "WHERE Data < '2019-01-01' AND IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_credits)
                dict_buildservice_startsaldo_credits = cur.fetchone()
                if dict_buildservice_startsaldo_credits['sum_credits']:
                    buildservice_startsaldo_credits = dict_buildservice_startsaldo_credits['sum_credits']
                else:
                    buildservice_startsaldo_credits = 0

                query_string_startsaldo_paids = "SELECT SUM(Summa_oplata) as sum_paids " \
                                                "FROM %s_vipiska_service " \
                                                "WHERE Data < '2019-01-01' AND IDNameClient = %d" % (
                    cur_city, IDNC)
                cur.execute(query_string_startsaldo_paids)
                dict_buildservice_startsaldo_paids = cur.fetchone()
                if dict_buildservice_startsaldo_paids['sum_paids']:
                    buildservice_startsaldo_paids = dict_buildservice_startsaldo_paids['sum_paids']
                else:
                    buildservice_startsaldo_paids = 0

                service_summ_startsaldo = float(buildservice_startsaldo_2011) * (-1) + float(
                    buildservice_startsaldo_credits) + float(buildservice_startsaldo_paids) * (-1)

                start_balance.objects.create(
                    branch=query_branch,
                    scompany=scompany_build,
                    date_saldo=datetime.date(2019, 1, 1),
                    summ=service_summ_startsaldo,
                    city=cur_city
                )

    return HttpResponseRedirect('/')
