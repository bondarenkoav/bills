from django.conf.urls import url

from base.merging_customer_data import merging_data
from base.views import save_changedata_branch, get_client, dashboard

from base.convert_db import convertbd

__author__ = 'bondarenkoav'
app_name = 'index'

urlpatterns = [
    # ------------------------ Открытие и добавление клиента, филиала, группы -----------------------------------
    # Изменение данных клиента
    url(r'^client_change/branch-(?P<branch_id>\d+)/$', save_changedata_branch, name='save_changedata_branch'),
    # Открыть карточку клиента
    url(r'^client/branch-(?P<branch_id>\d+)/$', get_client, name='card_client'),
    url(r'^convertbd/$', convertbd, name='convertbd'),
    url(r'^mergingbd/(?P<source_id>\d+)-to-(?P<destination_id>\d+)/$', merging_data),
    # url(r'^advanced_search/$', advanced_search, name='advanced_search'),
    url(r'^', dashboard, name='dashboard')
]