#from captcha.fields import CaptchaField
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.contrib.auth import authenticate

__author__ = 'bondarenkoav'

class LoginForm(forms.Form):
    username = forms.CharField(label=u'Логин', widget=forms.TextInput(attrs={'class':'input-sm chat-input'}))
    password = forms.CharField(label=u'Пароль', widget=forms.PasswordInput(attrs={'class':'input-sm chat-input'}))

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        if not self.errors:
            user = authenticate(username=cleaned_data['username'], password=cleaned_data['password'])
            if user is None:
                raise forms.ValidationError(u'Имя пользователя и пароль не подходят')
            self.user = user
        return cleaned_data

    def get_user(self):
        return self.user or None
#
# class custom_user_profile_form(forms.ModelForm):
#
#     def __init__(self, *args, **kwargs):
#         super(custom_user_profile_form, self).__init__(*args, **kwargs)
#         instance = getattr(self, 'instance', None)
#         if instance and instance.id:
#             pass
#         else:
#             pass
#
#     date_birth = forms.DateField(label='Дата рождения', widget=AdminDateWidget)
#     class Meta:
#          model = custom_user_profile
#          fields = ['photo','user','work_scompany','date_birth','work_phone','mobile_phone','post','scompany']
