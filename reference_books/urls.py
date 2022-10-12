from django.conf.urls import url

from reference_books.views import addget_group, getlist_group, addget_scompany, getlist_scompany, addget_equipment, \
    getlist_equipment, addget_typesobject, getlist_typesobject, addget_typeswork, getlist_typeswork, addget_post, \
    getlist_post, addget_coworker, getlist_coworker, getlist_clients

__author__ = 'bondarenkoav'
app_name = 'reference_books'

urlpatterns = [
    url(r'^group/item/(?:(?P<group_id>\d+)/)?$', addget_group, name='addget_group'),
    url(r'^group/$', getlist_group, name='getlist_group'),

    url(r'^scompany/item/(?:(?P<scompany_id>\d+)/)?$', addget_scompany, name='addget_scompany'),
    url(r'^scompany/$', getlist_scompany, name='getlist_scompany'),

    url(r'^equipment/item/(?:(?P<equipment_id>\d+)/)?$', addget_equipment, name='addget_equipment'),
    url(r'^equipment/$', getlist_equipment, name='getlist_equipment'),

    url(r'^typesobject/item/(?:(?P<typesobject_id>\d+)/)?$', addget_typesobject, name='addget_typesobject'),
    url(r'^typesobject/$', getlist_typesobject, name='getlist_typesobject'),

    url(r'^typeswork/item/(?:(?P<typeswork_id>\d+)/)?$', addget_typeswork, name='addget_typeswork'),
    url(r'^typeswork/$', getlist_typeswork, name='getlist_typeswork'),

    url(r'^post/item/(?:(?P<post_id>\d+)/)?$', addget_post, name='addget_post'),
    url(r'^post/$', getlist_post, name='getlist_post'),

    url(r'^cowork/item/(?:(?P<coworker_id>\d+)/)?$', addget_coworker, name='addget_coworker'),
    url(r'^cowork/$', getlist_coworker, name='getlist_coworker'),

    url(r'^client/$', getlist_clients, name='getlist_client'),
]