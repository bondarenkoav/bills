from django.contrib import admin

from .models import TechSecurityContract, TechSecurityObject, TechSecurityObjectPeriodSecurity, TechTemplateDocuments, \
    ListRentedEquipment, TechTemplateSubContract, TechSecuritySubContract, TechTemplateOtherDocuments


class TechSecurityObjectAdmin(admin.ModelAdmin):
    model = TechSecurityObject
    list_display = ['NumObjectPCN', 'TypeObject', 'NameObject', 'AddressObject', 'PriceNoDifferent', 'StatusSecurity']


class DogTechOhranaObjectInline(admin.TabularInline):
    model = TechSecurityObject
    extra = 0


class TechSecurityContractAdmin(admin.ModelAdmin):
    list_display = ['NumContractInternal', 'NumContractBranch', 'DateConclusion', 'DateTermination', 'Branch',
                    'ServingCompany']
    list_filter = ['ServingCompany', 'DateConclusion', 'DateTermination']
    search_fields = ['NumContractInternal', 'NumContractBranch']
    inlines = [DogTechOhranaObjectInline]
    model = TechSecurityContract


class TechTemplateDocumentsAdmin(admin.ModelAdmin):
    list_display = ['CategoryObjects', 'NameTemplate']
    list_filter = ['CategoryObjects']


admin.site.register(TechSecurityContract, TechSecurityContractAdmin)
admin.site.register(TechSecurityObjectPeriodSecurity)
admin.site.register(TechTemplateDocuments, TechTemplateDocumentsAdmin)
admin.site.register(TechTemplateOtherDocuments)
admin.site.register(TechTemplateSubContract)
admin.site.register(ListRentedEquipment)
admin.site.register(TechSecuritySubContract)
