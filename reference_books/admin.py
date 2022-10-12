from django.contrib import admin

from base.models import CoWorkers
from .models import TypeObject, TypeDocument, TypesClient, ListPosts, FormsSchet, PowersOfficeActs, StatusSecurity, \
    PaymentMethods, TypeWork, TypeEquipmentInstalled, OpSoS_name, OpSoS_rate


class TypeObjectAdmin(admin.ModelAdmin):
    list_display = ['ShortName', 'slug', 'DescName']


class TypesClientAdmin(admin.ModelAdmin):
    list_display = ['ShortTypeClient', 'slug', 'DescTypeClient']


class TypeDocumentAdmin(admin.ModelAdmin):
    list_display = ['Name', 'slug']


class FormsSchetAdmin(admin.ModelAdmin):
    list_display = ['ShortNameSchet', 'DescShortNameSchet', 'slug']


class OpSoSRateAdmin(admin.ModelAdmin):
    model = OpSoS_rate
    list_display = ['Name', 'Price', 'Descript']
    list_filter = ['Name', 'Price']


class OpSoSRateInline(admin.TabularInline):
    model = OpSoS_rate
    extra = 0


class OpSoSNameAdmin(admin.ModelAdmin):
    list_display = ['Name']
    inlines = [OpSoSRateInline]
    model = OpSoS_name


admin.site.register(TypeObject, TypeObjectAdmin)
admin.site.register(TypeDocument, TypeDocumentAdmin)
admin.site.register(TypesClient, TypesClientAdmin)
admin.site.register(TypeEquipmentInstalled)
admin.site.register(TypeWork)
admin.site.register(ListPosts)
admin.site.register(CoWorkers)
admin.site.register(PaymentMethods)
admin.site.register(StatusSecurity)
admin.site.register(FormsSchet, FormsSchetAdmin)
admin.site.register(PowersOfficeActs)
admin.site.register(OpSoS_name, OpSoSNameAdmin)
