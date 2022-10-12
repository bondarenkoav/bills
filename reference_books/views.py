from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.csrf import csrf_protect

from base.models import Branch, GroupClient, ServingCompanyBranch, CoWorkers
from reference_books.forms import group_form, scompany_branch_form, coworker_form, post_form, equipment_form, \
    typesobject_form, typeswork_form
from reference_books.models import ListPosts, ListEquipment, TypeObject, TypeWork


area = u'Справочники'


@login_required
def getlist_clients(request):
    paginator = Paginator(Branch.objects.all().order_by('NameBranch'), 50)
    page = request.GET.get('page')
    try:
        client_list = paginator.page(page)
    except PageNotAnInteger:
        client_list = paginator.page(1)
    except EmptyPage:
        client_list = paginator.page(paginator.num_pages)

    return render(request, 'clients_list.html', {
        'title': u'Список контрагентов',
        'area': area,
        'list': client_list,
        'page': page}
    )


@login_required
def getlist_group(request):
    paginator = Paginator(GroupClient.objects.all().order_by('NameGroupClient'), 20)
    page = request.GET.get('page')
    try:
        group_list = paginator.page(page)
    except PageNotAnInteger:
        group_list = paginator.page(1)
    except EmptyPage:
        group_list = paginator.page(paginator.num_pages)

    return render(request, 'group/group_list.html', {
        'title': u'Список групп контрагентов',
        'area': area,
        'list': group_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_group(request, group_id=None):
    form = group_form(request.POST or None, instance=group_id and GroupClient.objects.get(id=group_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_group')
    else:
        if group_id:
            group_data = GroupClient.objects.get(id=group_id)
        else:
            group_data = GroupClient.objects.none()

    return render(request, 'group/group_item.html', {
        'title': u'Группа контрагентов',
        'area': area,
        'data': group_data,
        'form': form}
    )


@login_required
def getlist_scompany(request):
    paginator = Paginator(ServingCompanyBranch.objects.all(), 20)
    page = request.GET.get('page')
    try:
        scompany_list = paginator.page(page)
    except PageNotAnInteger:
        scompany_list = paginator.page(1)
    except EmptyPage:
        scompany_list = paginator.page(paginator.num_pages)

    return render(request, 'scompany/scompany_list.html', {
        'title': u'Список сервисных компаний',
        'area': area,
        'list': scompany_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_scompany(request, scompany_id=None):
    form = scompany_branch_form(request.POST or None,
                                instance=scompany_id and ServingCompanyBranch.objects.get(id=scompany_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_scompany')
    else:
        if scompany_id:
            scompany_data = ServingCompanyBranch.objects.get(id=scompany_id)
        else:
            scompany_data = ServingCompanyBranch.objects.none()

    return render(request, 'scompany/scompany_item.html', {
        'title': u'Сервисная компания',
        'area': area,
        'data': scompany_data,
        'form': form}
    )


@login_required
def getlist_coworker(request):
    paginator = Paginator(CoWorkers.objects.all(),20)
    page = request.GET.get('page')
    try:
        coworker_list = paginator.page(page)
    except PageNotAnInteger:
        coworker_list = paginator.page(1)
    except EmptyPage:
        coworker_list = paginator.page(paginator.num_pages)

    return render(request, 'coworker/coworker_list.html', {
        'title': u'Список сотрудников',
        'area': area,
        'list': coworker_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_coworker(request, coworker_id=None):
    form = coworker_form(request.POST or None, instance=coworker_id and CoWorkers.objects.get(id=coworker_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_coworker')
    else:
        if coworker_id:
            coworker_data = CoWorkers.objects.get(id=coworker_id)
        else:
            coworker_data = CoWorkers.objects.none()

    return render(request, 'coworker/coworker_item.html', {
        'title': u'Сотрудник',
        'area': area,
        'data': coworker_data,
        'form': form}
    )


@login_required()
def getlist_post(request):
    paginator = Paginator(ListPosts.objects.all(),20)
    page = request.GET.get('page')
    try:
        post_list = paginator.page(page)
    except PageNotAnInteger:
        post_list = paginator.page(1)
    except EmptyPage:
        post_list = paginator.page(paginator.num_pages)

    return render(request, 'post/post_list.html', {
        'title': u'Список должностей',
        'area': area,
        'list': post_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_post(request, post_id=None):
    form = post_form(request.POST or None, instance=post_id and ListPosts.objects.get(id=post_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_post')
    else:
        if post_id:
            post_data = ListPosts.objects.get(id=post_id)
        else:
            post_data = ListPosts.objects.none()

    return render(request, 'post/post_item.html', {
        'title': u'Сотрудник',
        'area': area,
        'data': post_data,
        'form': form}
    )


@login_required
def getlist_equipment(request):
    paginator = Paginator(ListEquipment.objects.all(),20)
    page = request.GET.get('page')
    try:
        equipment_list = paginator.page(page)
    except PageNotAnInteger:
        equipment_list = paginator.page(1)
    except EmptyPage:
        equipment_list = paginator.page(paginator.num_pages)

    return render(request, 'equipment/equipment_list.html', {
        'title': u'Список оборудования',
        'area': area,
        'list': equipment_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_equipment(request, equipment_id=None):
    form = equipment_form(request.POST or None, instance=equipment_id and ListEquipment.objects.get(id=equipment_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_equipment')
    else:
        if equipment_id:
            equipment_data = ListPosts.objects.get(id=equipment_id)
        else:
            equipment_data = ListPosts.objects.none()

    return render(request, 'equipment/equipment_item.html', {
        'title': u'Оборудование',
        'area': area,
        'data': equipment_data,
        'form': form}
    )


@login_required
def getlist_typesobject(request):
    paginator = Paginator(TypeObject.objects.all(),20)
    page = request.GET.get('page')
    try:
        typesobject_list = paginator.page(page)
    except PageNotAnInteger:
        typesobject_list = paginator.page(1)
    except EmptyPage:
        typesobject_list = paginator.page(paginator.num_pages)

    return render(request, 'typesobject/typesobject_list.html', {
        'title': u'Типы объектов',
        'area': area,
        'list': typesobject_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_typesobject(request, typesobject_id=None):
    form = typesobject_form(request.POST or None,
                            instance=typesobject_id and TypeObject.objects.get(id=typesobject_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_typesobject')
    else:
        if typesobject_id:
            typesobject_data = TypeObject.objects.get(id=typesobject_id)
        else:
            typesobject_data = TypeObject.objects.none()

    return render(request, 'typesobject/typesobject_item.html', {
        'title': u'Оборудование',
        'area': area,
        'data': typesobject_data,
        'form': form}
    )


@login_required
def getlist_typeswork(request):
    paginator = Paginator(TypeWork.objects.all(),20)
    page = request.GET.get('page')
    try:
        typeswork_list = paginator.page(page)
    except PageNotAnInteger:
        typeswork_list = paginator.page(1)
    except EmptyPage:
        typeswork_list = paginator.page(paginator.num_pages)

    return render(request, 'typeswork/typeswork_list.html', {
        'title': u'Виды работ',
        'area': area,
        'list': typeswork_list,
        'page': page}
    )


@login_required
@csrf_protect
def addget_typeswork(request, typeswork_id=None):
    form = typeswork_form(request.POST or None, instance=typeswork_id and TypeWork.objects.get(id=typeswork_id))
    if request.POST:
        if form.is_valid():
            form.save()
        return redirect('reference_books:getlist_typeswork')
    else:
        if typeswork_id:
            typeswork_data = TypeObject.objects.get(id=typeswork_id)
        else:
            typeswork_data = TypeObject.objects.none()

    return render(request, 'typeswork/typeswork_item.html', {
        'title': u'Вид работ',
        'area': area,
        'data': typeswork_data,
        'form': form}
    )