# -*- coding: utf-8 -*-
from django.conf.urls import url

from maintenance_service.views import add_get_object, upload_subcontract_pdf, add_get_subcontract, \
    view_subcontract_template, upload_contract_pdf, view_contract_template, add_get_contract, add_get_act, copy_objects
from maintenance_service.cron import cron_charge_subscription_contract_manual

__author__ = 'bondarenkoav'
app_name = 'maintenance_service'

urlpatterns = [
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/object/(?:id-(?P<object_id>\d+)/)?$', add_get_object, name='addget_object'),

    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/subcontract/id-(?P<subcontract_id>\d+)/(?:scanfile-(?P<file_id>\d+)/)?$', upload_subcontract_pdf, name='addget_scan_subcontract'),
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/subcontract(?:id-(?P<subcontract_id>\d+)/)?', add_get_subcontract, name='addget_subcontract'),
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/subcontract/id-(?P<subcontract_id>\d+)/print/', view_subcontract_template, name='print_subcontract'),

    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/scanfile(?:id-(?P<file_id>\d+)/)?$', upload_contract_pdf, name='addget_scan_contract'),
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/print/$', view_contract_template, name='print_contract'),

    url(r'^branch-(?P<branch_id>\d+)/contract/(?:id-(?P<contract_id>\d+)/)?$', add_get_contract, name='addget_contract'),

    url(r'^branch-(?P<branch_id>\d+)/act/(?:id-(?P<act_id>\d+)/)?$', add_get_act, name='addget_act'),

    url(r'^contract-(?P<contract_id>\d+)/copy_objects/$', copy_objects, name='copy_objects'),

    # Cron
    url(r'^cron_charge_subscription_contract/', cron_charge_subscription_contract_manual),
]