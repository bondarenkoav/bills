from django import forms
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from accounting.models import credited_with_paid, AccountingTemplates

class AccountingTemplatesAdminForm(forms.ModelForm):
    TextTemplate = forms.CharField(widget=CKEditorWidget())
    class Meta:
        model = AccountingTemplates
        exclude = ()

class AccountingTemplatesAdmin(admin.ModelAdmin):
    form = AccountingTemplatesAdminForm

admin.site.register(AccountingTemplates, AccountingTemplatesAdmin)
admin.site.register(credited_with_paid)