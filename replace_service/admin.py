from django.contrib import admin

# Register your models here.
from replace_service.models import ReplaceServiceObject, ReplaceServiceContract, ReplaceServiceAct, \
    ReplaceTemplateDocuments


class ReplaceServiceObjectAdmin(admin.ModelAdmin):
    model = ReplaceServiceObject
    list_display = ['TypeObject', 'NameObject', 'AddressObject']


class ReplaceServiceActAdmin(admin.ModelAdmin):
    model = ReplaceServiceAct
    list_display = ['ReplaceServiceObject', 'DateWork', 'Price']


class ReplaceServiceContractObjectInline(admin.TabularInline):
    model = ReplaceServiceObject, ReplaceServiceAct
    extra = 0


class ReplaceServiceContractAdmin(admin.ModelAdmin):
    list_display = ['NumContractInternal', 'DateConclusion', 'DateTermination', 'Branch', 'ServingCompany']


admin.site.register(ReplaceServiceContract, ReplaceServiceContractAdmin)
admin.site.register(ReplaceServiceObject, ReplaceServiceObjectAdmin)
admin.site.register(ReplaceServiceAct)
admin.site.register(ReplaceTemplateDocuments)
