__author__ = 'bondarenkoav'

from django.conf.urls import url
from notifications.views import *

urlpatterns = [
    #url(r'^page/(?P<page_id>\d+)/$', get_notifications),
    url(r'^item/None/$', get_notification),
    url(r'^item/(?P<notification_id>\d+)/$', get_notification),
    url(r'^', get_notifications),
]