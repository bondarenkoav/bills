from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.context_processors import csrf
from django.urls import reverse
from tasks.forms import task_form
from tasks.models import user_task


def get_tasks(request):
    tasks = user_task.objects.filter(Q(Create_user=request.user.id)|Q(responsible=request.user)).distinct('id')#.order_by('-DateTime_add')
    return render(request, 'tasks.html', {'tasks': tasks})

def get_task(request,task_id=None):
    args = {}
    args.update(csrf(request))

    form = task_form(request.POST or None, user=request.user, instance=task_id and user_task.objects.get(id=task_id))

    if request.POST:
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.Create_user = request.user.id
            new_task.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('index:dashboard'))

    if task_id!=None:
        user_task.objects.filter(responsible=request.user,read=False).update(read=True)

    args['form'] = form
    args['task_id'] = task_id
    args['user'] = request.user
    return render(request, 'task.html', args)
