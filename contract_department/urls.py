from django.conf.urls import url

from base.views import addclient_worddata_company, addclient_worddata_branch, addclient_worddata_businessman, \
    addclient_worddata_physicalperson, addclient_check_client, select_type_client_add, addclient_contacts, \
    addclient_usernote, dlt_contact, client_PhysicalPerson_update, client_Company_update, client_Businessman_update
from contract_department.views import journal_events, journal_planned_actions, journals_term_contracts, \
    journal_notcomplete_contracts, journal_acts_period, get_quarterly_to_police, journal_action_objects, \
    report_assembly_production

__author__ = 'bondarenkoav'

app_name = 'contract_department'


urlpatterns = [
    # --------------- Организация ----------------
    url(r'^client_add/word/company/inn-(?P<inn>\w+)/kpp-(?P<kpp>\w+)/$',
        addclient_worddata_company, name='addclient_company_worddata_client'),
    url(r'^branch_add/word/company/client-(?P<client_id>\w+)/kpp-(?P<kpp>\w+)/$',
        addclient_worddata_branch, name='addclient_company_worddata_branch'),

    # ---------------- ИП ------------------------
    url(r'^client_add/word/businessman/(?:inn-(?P<inn>\d+)/)?$',
        addclient_worddata_businessman, name='addclient_businessman_worddata_client'),

    # -------------- Физлица ---------------------
    url(r'^client_add/word/physicalperson/(?:fio-(?P<fio>\w+)/passport-(?P<passport>\w+)/alien-(?P<alien>\w+)/)?$',
        addclient_worddata_physicalperson, name='addclient_physicalperson_worddata_client'),

    # ----------- Для всех типов -----------------
    # Проверка на дубликаты
    url(r'^client_add/check/(?P<type_client>\w+)/$', addclient_check_client,  name='addclient_check_client'),
    # Добавление контрагента: выбор типа клиента
    url(r'^client_add/$', select_type_client_add, name='addclient_change_type'),
    # Добавление-редактирование контактов контрагента
    url(r'^contact_add/branch-(?P<branch_id>\d+)/$', addclient_contacts, name='contact_add'),
    # Добавление-редактирование пользовательской информации
    url(r'^usernote_add/branch-(?P<branch_id>\d+)/(?:id-(?P<usernote_id>\d+)/)?$', addclient_usernote, name='usernote_add'),

    # Редактирование данных контрагента
    url(r'^update/clientcompany/branch-(?P<pk>\d+)/$', client_Company_update, name='client_company_update'),
    url(r'^update/clientbusinessman/branch-(?P<pk>\d+)/$', client_Businessman_update, name='client_businessman_update'),
    url(r'^update/clientphysicalperson/branch-(?P<pk>\d+)/$', client_PhysicalPerson_update, name='client_physicalperson_update'),

    # Удаление платежа
    url(r'^delete/contact-(?P<contact_id>\d+)/$', dlt_contact, name='delete_contact'),

    # --------------- Журналы --------------------
    # Вывод событий за период
    url(r'^events/$', journal_events, name='journal_events_period'),
    # Запланированные действия
    url(r'^planned_actions/$', journal_planned_actions, name='journal_planned_actions'),
    # Список срочных договоров
    url(r'^term_contract/$', journals_term_contracts, name='journal_termcontract'),
    # Не полные договора (не завершенные)
    url(r'^notcomplete_contracts/$', journal_notcomplete_contracts, name='journal_notcomplete_contracts'),
    # Вывод актов за период
    url(r'^acts_period/$', journal_acts_period, name='journal_acts_period'),
    # Список активных объектов
    url(r'^action_objects/$', journal_action_objects, name='journal_action_objects'),

    # -------------- Отчеты ----------------------
    # Квартальный отчет в полицию
    url(r'^quarterly_to_police/$', get_quarterly_to_police, name='report_quarterly_topolice'),
    # Производственный отчёт за месяц по монтажам
    url(r'^assembly-production/$', report_assembly_production, name='report-assembly-production'),
    # Недельный отчет в полицию
    #url(r'^weekly_to_police/', get_weekly_to_police, name='report_weekly_topolice'),
]