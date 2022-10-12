__author__ = 'bondarenkoav'

from django import template

register = template.Library()

@register.filter
def view_shortfio_user(user):
    try:
        return get_shortfio(user.last_name+' '+user.first_name)
    except:
        return 'ошибка'


@register.filter
def get_shortfio(fio):
    if fio:
        split_fio = fio.split(' ')
        if len(split_fio) == 1:
            return split_fio
        elif len(split_fio) == 2:
            return split_fio[0]+' '+split_fio[1][:1]+'.'
        elif len(split_fio) == 3:
            return split_fio[0]+' '+split_fio[1][:1]+'.'+split_fio[2][:1]+'.'
        else:
            return 'неизвестно'
    else:
        return 'нет'
