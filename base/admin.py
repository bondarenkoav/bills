from django.contrib import admin
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin

from base.models import GroupClient, Client, Branch, ServingCompany, ServingCompanyBranch, \
    Contacts, SystemConstant, ServingCompany_settingsDocuments, ScannedDocuments, Menu, \
    logging, Event, TypeSubContract


class ClientAdmin(admin.ModelAdmin):
    model = Client
    list_display = ['TypeClient', 'NameClient_full', 'NameClient_short', 'INN', 'PassportSerNum', 'DatePassport']
    list_filter = ['TypeClient', 'GroupClient']
    search_fields = ['NameClient_short']


class ContactsInline(admin.StackedInline):
    model = Contacts
    extra = 1


class BranchAdmin(admin.ModelAdmin):
    list_display = ['Client', 'NameBranch', 'Management_post', 'Management_name', 'Address_post', 'Address_email',
                    'KPP', 'FormsSchet']
    inlines = [ContactsInline]
    search_fields = ['NameBranch']


class ServingCompanyBranchInline(admin.TabularInline):
    model = ServingCompanyBranch
    extra = 1


class ServingCompanyAdmin(admin.ModelAdmin):
    inlines = [ServingCompanyBranchInline]


class ScannedDocumentsAdmin(admin.ModelAdmin):
    list_display = ['NameDocument', 'Branch', 'TypeDocument', 'Document_id']


class ServingCompany_settingsDocumentsAdmin(admin.ModelAdmin):
    list_display = ['ServingCompanyBranch', 'TypeDocument', 'current_num', 'postfix_num']
    list_filter = ['ServingCompanyBranch']
    ordering = ['ServingCompanyBranch']


class TypeSubContractAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'slug']


class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'Name', 'slug', 'forfilter']


class CustomMPTTModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 20


admin.site.register(Menu, DraggableMPTTAdmin)
admin.site.register(logging)
admin.site.register(Event, EventAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(GroupClient)
admin.site.register(ServingCompany, ServingCompanyAdmin)
admin.site.register(ServingCompany_settingsDocuments, ServingCompany_settingsDocumentsAdmin)
admin.site.register(Contacts)
admin.site.register(SystemConstant)
admin.site.register(ScannedDocuments, ScannedDocumentsAdmin)
admin.site.register(TypeSubContract, TypeSubContractAdmin)
