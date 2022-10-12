__author__ = 'bondarenkoav'

from django.conf.urls import url
from tasks.views import *

urlpatterns = [
    url(r'^page/(?P<page_id>\d+)/$', get_tasks),
    url(r'^item/None/$', get_task),
    url(r'^item/(?P<task_id>\d+)/$', get_task),
    url(r'^', get_tasks),
]