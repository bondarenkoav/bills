import datetime
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.auth.models import User
from tasks.models import user_task

__author__ = 'bondarenkoav'


class task_form(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(task_form, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            if self.user.id == instance.Create_user:
                self.fields['done'].required = False
                self.fields['done'].widget.attrs['disabled'] = 'disabled'
                self.fields['done_description'].required = False
                self.fields['done_description'].widget.attrs['disabled'] = 'disabled'
            else:
                if self.user in instance.responsible.all():
                    self.fields['title'].required = False
                    self.fields['title'].widget.attrs['disabled'] = 'disabled'
                    self.fields['description'].required = False
                    self.fields['description'].widget.attrs['disabled'] = 'disabled'
                    self.fields['responsible'].required = False
                    self.fields['responsible'].widget.attrs['disabled'] = 'disabled'
                    self.fields['limitation'].required = False
                    self.fields['limitation'].widget.attrs['disabled'] = 'disabled'
                    self.fields['high_importance'].required = False
                    self.fields['high_importance'].widget.attrs['disabled'] = 'disabled'
                    self.fields['notification'].required = False
                    self.fields['notification'].widget.attrs['disabled'] = 'disabled'
                    self.fields['done_description'].required = False
                    self.fields['done_description'].widget.attrs['disabled'] = 'disabled'
                else:
                    self.fields['title'].required = False
                    self.fields['title'].widget.attrs['disabled'] = 'disabled'
                    self.fields['description'].required = False
                    self.fields['description'].widget.attrs['disabled'] = 'disabled'
                    self.fields['responsible'].required = False
                    self.fields['responsible'].widget.attrs['disabled'] = 'disabled'
                    self.fields['limitation'].required = False
                    self.fields['limitation'].widget.attrs['disabled'] = 'disabled'
                    self.fields['high_importance'].required = False
                    self.fields['high_importance'].widget.attrs['disabled'] = 'disabled'
                    self.fields['notification'].required = False
                    self.fields['notification'].widget.attrs['disabled'] = 'disabled'
                    self.fields['done'].required = False
                    self.fields['done'].widget.attrs['disabled'] = 'disabled'
                    self.fields['done_description'].required = False
                    self.fields['done_description'].widget.attrs['disabled'] = 'disabled'
        else:
            self.fields['done'].required = False
            self.fields['done'].widget.attrs['disabled'] = 'disabled'
            self.fields['done_description'].required = False
            self.fields['done_description'].widget.attrs['disabled'] = 'disabled'
            self.fields['limitation'].initial = datetime.datetime.today()

    description = forms.CharField(required=False, label='Описание', widget=forms.widgets.Textarea(attrs={'rows':5}))
    done_description = forms.CharField(required=False, label='Результат', widget=forms.widgets.Textarea(attrs={'rows':5}))
    responsible = forms.ModelChoiceField(required=False, label="Исполнитель", queryset=User.objects.all(), widget=forms.Select(attrs={'class':'js-example-basic-multiple','multiple':'multiple'}))
    limitation = forms.DateField(label='Крайний срок', widget=AdminDateWidget)
    done = forms.ChoiceField(required=True, label='Выполнено', widget=forms.CheckboxInput(attrs={'onclick':'DisplayDoneDescription();'}))

    class Meta:
         model = user_task
         fields = ['title','high_importance','description','responsible','limitation','notification','done','done_description']
