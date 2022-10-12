# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import add_get_object, add_get_contract, add_get_act

__author__ = 'bondarenkoav'
app_name = 'replace_service'

urlpatterns = [
    url(r'^branch-(?P<branch_id>\d+)/contract/id-(?P<contract_id>\d+)/object/(?:id-(?P<object_id>\d+)/)?$',
        add_get_object, name='addget_object'),
    url(r'^branch-(?P<branch_id>\d+)/contract/(?:id-(?P<contract_id>\d+)/)?$',
        add_get_contract, name='addget_contract'),
    url(r'^branch-(?P<branch_id>\d+)/act/(?:id-(?P<act_id>\d+)/)?$', add_get_act, name='addget_act'),
]