from django.contrib import admin
from .models import MaintenanceServiceContract, MaintenanceServiceObject, MaintenanceTemplateDocuments, \
    MaintenancePereodicAccrual, MaintenancePereodicService


class MaintenanceServiceObjectAdmin(admin.ModelAdmin):
    model = MaintenanceServiceObject
    list_display = ['TypeObject', 'NameObject', 'AddressObject', 'Price']


class MaintenanceServiceContractObjectInline(admin.TabularInline):
    model = MaintenanceServiceObject
    extra = 0


class MaintenanceServiceContractAdmin(admin.ModelAdmin):
    list_display = ['NumContractInternal', 'DateConclusion', 'DateTermination', 'Branch', 'ServingCompany']
    list_filter = ['ServingCompany', 'DateConclusion', 'DateTermination']
    search_fields = ['NumContractInternal', 'NumContractBranch']
    inlines = [MaintenanceServiceContractObjectInline]
    model = MaintenanceServiceContract


class MaintenancePereodicAccrualAdmin(admin.ModelAdmin):
    list_display = ['NamePeriodic', 'slug']


class MaintenancePereodicServiceAdmin(admin.ModelAdmin):
    list_display = ['NamePeriodic', 'slug']


admin.site.register(MaintenanceServiceContract, MaintenanceServiceContractAdmin)
admin.site.register(MaintenanceTemplateDocuments)
admin.site.register(MaintenancePereodicAccrual, MaintenancePereodicAccrualAdmin)
admin.site.register(MaintenancePereodicService, MaintenancePereodicServiceAdmin)