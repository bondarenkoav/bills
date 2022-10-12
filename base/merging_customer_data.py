from accounting.models import start_balance, credited_with_paid
from base.models import Branch, Contacts, Client, logging
from build_service.models import BuildServiceContract
from maintenance_service.models import MaintenanceServiceContract
from tech_security.models import TechSecurityContract


def merging_data(request, source_id=None, destination_id=None):
    try:
        if source_id and destination_id:
            source = Branch.objects.get(id=source_id)
            destination = Branch.objects.get(id=destination_id)
            # Начальное сальдо
            start_balance.objects.filter(branch=source).update(branch=destination)
            # Начисления и оплаты
            credited_with_paid.objects.filter(branch=source).update(branch=destination)
            # Договора монтажа
            BuildServiceContract.objects.filter(Branch=source).update(Branch=destination)
            # Договора ТО
            MaintenanceServiceContract.objects.filter(Branch=source).update(Branch=destination)
            # Договора техохраны
            TechSecurityContract.objects.filter(Branch=source).update(Branch=destination)
            # История
            logging.objects.filter(branch_id=source.id).update(branch_id=destination.id)
            # Контакты
            Contacts.objects.filter(Branch=source).update(Branch=destination)
            # Пометка на удаление контрагенты
            Client.objects.filter(id=source.Client.id).update(NameClient_full='Удалить')
        return u'Удача'
    except:
        return u'Не удачно'
