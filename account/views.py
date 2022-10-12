import six

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import auth
from django.urls import reverse

from account.models import Profile
from build_service.models import BuildServiceContract, BuildServiceContract_scan
from maintenance_service.models import MaintenanceServiceContract, MaintenanceServiceContract_scan
from tech_security.models import TechSecurityContract, TechSecurityContract_scan


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('login'))


def get_scompany(user):
    return Profile.objects.get(user=user).scompany.all()


# Декоратор для вью. Разрешает доступ в случае нахождения пользователя в одной из указанных групп.
def group_required(group, login_url=None, raise_exception=False):
    def in_groups(user):
        if isinstance(group, six.string_types):
            groups = (group, )
        else:
            groups = group
        if user.is_superuser or bool(user.groups.filter(name__in=groups)):
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    return user_passes_test(in_groups, login_url=login_url)


# Виджеты на рабочий стол в зависимости от группы
def get_desktop_widgets(request):
    widget_contract_nocomplete = {
        'tech_security': TechSecurityContract_scan.objects.exclude(id__in=TechSecurityContract.objects.all()),
        'build_service': BuildServiceContract_scan.objects.exclude(id__in=BuildServiceContract.objects.all()),
        'maint_service': MaintenanceServiceContract_scan.objects.
            exclude(id__in=MaintenanceServiceContract.objects.all()),
    }


@login_required()
def page_error403(request):
    return render(request, 'error.html', {
        'title': '403',
        'text': 'Доступ запрещён!'
    })


@login_required()
def page_error503(request):
    return render(request, 'error.html', {
        'title': '503',
        'text': 'Сервис не доступен!'
    })


@login_required()
def error_testclient(request):
    return render(request, 'error.html', {
        'title': 'Ошибка проверки клиента',
        'text': 'Возможно контрагент ликвидирован или не внесён в базу ИФНС. '
                'Также возможно отсутствие интернета.'
    })
