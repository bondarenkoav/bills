# -*- coding: utf-8 -*-
from django.conf.urls import url

from tech_security.views import upload_object_pdf, add_get_object, equip_installed_object, rent_object, \
    connection_object, addget_subcontract_pdf, view_subcontract_template, add_get_subcontract, addget_contract_pdf, \
    view_checklist_contract, view_contract_template, add_get_contract, copy_objects, object_pricedifferent, \
    objects_deactivate, objects_activate
from tech_security import cron as ts_cron

__author__ = 'bondarenkoav'
app_name = 'tech_security'

urlpatterns = [
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/object/id-(?P<object_id>\d+)/scanfile/(?:id-(?P<file_id>\d+)/)?$',
        upload_object_pdf, name='addget_scan_certofownership'),
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/object/(?:id-(?P<object_id>\d+)/)?$',
        add_get_object, name='addget_object'),

    # Вкладки объекта
    url(r'^object-(?P<object_id>\d+)/equip_installed_object/$', equip_installed_object, name='equip_installed_object'),
    url(r'^object-(?P<object_id>\d+)/rent_object/$', rent_object, name='rent_object'),
    url(r'^object-(?P<object_id>\d+)/connection_object/$', connection_object, name='connection_object'),

    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/subcontract/id-(?P<subcontract_id>\d+)/scanfile/(?:id-(?P<file_id>\d+)/)?$',
        addget_subcontract_pdf, name='addget_scan_subcontract'),
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/subcontract/(?:id-(?P<subcontract_id>\d+)/)?',
        add_get_subcontract, name='addget_subcontract'),

    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/scanfile/(?:id-(?P<file_id>\d+)/)?$',
        addget_contract_pdf, name='addget_scan_contract'),

    url(r'^contract/id-(?P<contract_id>\d+)/checklist/$', view_checklist_contract, name='checklist_contract'),

    url(r'contract/id-(?P<contract_id>\d+)/objects-activate/$', objects_activate, name='objects_activate'),
    url(r'contract/id-(?P<contract_id>\d+)/objects-deactivate/$', objects_deactivate, name='objects_deactivate'),

    url(r'^contract/id-(?P<contract_id>\d+)/print/$', view_contract_template, name='print_contract'),
    url(r'^subcontract/id-(?P<subcontract_id>\d+)/print/', view_subcontract_template, name='print_subcontract'),

    url(r'^branch-(?P<branch_id>\d+)/contract/(?:id-(?P<contract_id>\d+)/)?$', add_get_contract, name='addget_contract'),

    url(r'^contract-(?P<contract_id>\d+)/copy_objects/$', copy_objects, name='copy_objects'),

    url(r'^object-(?P<object_id>\d+)/$', object_pricedifferent, name='change_pricedifferent'),
    # автоматическое начисление абонплаты на один объект
    url(r'^cron_charge_subscription_fees_one_object/$', ts_cron.cron_charge_subscription_fees_one_object),
    # автоматическое начисление абонплаты на все объекты в охране
    url(r'^charge_subscription_fees_full_month/$', ts_cron.cron_charge_subscription_fees_full_month_manual),
    #url(r'^charge_subscription_fees_full_month/(?P<scompany_id>\d+)/$', ts_cron.cron_charge_subscription_fees_full_month_manual),
]