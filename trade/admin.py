from django.contrib import admin
from .models import invoice, import_invoices


# class InvoiceAdmin(admin.ModelAdmin):
#     list_display = ['id','number','price','Branch','ServingCompany','date_add']
#
# class ImportInvoicesAdmin(admin.ModelAdmin):
#     list_display = ['INN','Client','type_invoice','number_invoice','parent_invoice',
#                     'date_invoice','price','ServingCompany','Branch','date_add']

admin.site.register(invoice)
admin.site.register(import_invoices)