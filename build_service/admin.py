from django.contrib import admin

from .models import BuildServiceContract, BuildServiceObject, BuildTemplateDocuments, BuildServiceAct


class BuildServiceObjectAdmin(admin.ModelAdmin):
    model = BuildServiceObject
    list_display = ['TypeObject', 'NameObject', 'AddressObject', 'Price']


class BuildServiceContractObjectInline(admin.TabularInline):
    model = BuildServiceObject
    extra = 0


class BuildServiceContractAdmin(admin.ModelAdmin):
    list_display = ['NumContractInternal', 'DateConclusion', 'DateTermination', 'Branch', 'ServingCompany']


admin.site.register(BuildServiceContract, BuildServiceContractAdmin)
admin.site.register(BuildServiceObject, BuildServiceObjectAdmin)
admin.site.register(BuildServiceAct)
admin.site.register(BuildTemplateDocuments)