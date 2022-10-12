import datetime
from django.shortcuts import render
from django.template import Template, Context
from base.models import Event
from build_service.models import BuildServiceContract, BuildServiceContract_scan
from maintenance_service.models import MaintenanceServiceContract, MaintenanceServiceContract_scan
from notifications.models import notification
from reference_books.models import StatusSecurity
from tech_security.models import TechSecurityContract, TechSecurityObject, TechSecurityObjectRent, \
    TechSecurityContract_scan, TechSecuritySubContract, TechSecuritySubContract_scan


# def crontab_create_notifications(request):
#     status = StatusSecurity.objects.get(Status=True)
#     event = Event.objects.all()
#     # ------------------------------------- Техническая охрана ---------------------------------------
#     # Договора, у которых заканчивается срок действия через 3 недели
#     tech_security_contract = TechSecurityContract.objects.filter(DateTermination=(datetime.datetime.today()+datetime.timedelta(weeks=3)))
#     for item in tech_security_contract:
#         text_template = Template(event.get(slug='expires_contract').template)
#         tags = Context({
#             'application': 'технической охраны',
#             'contract'  : item.NumContractInternal,
#             'branch'    : item.Branch.NameBranch,
#             'date_start': item.DateConclusion,
#             'date_end'  : item.DateTermination,
#         })
#         notification.objects.create(application="tech_security", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.ServingCompany).first(), limitation=item.DateTermination)
#
#     # Договора, у которых через 2 недели после подписания не загружен скан
#     tech_security_contract_filter = TechSecurityContract.objects.filter(DateConclusion__gt=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     tech_security_contract_scan = TechSecurityContract_scan.objects.exclude(TechSecurityContract__in=tech_security_contract_filter)
#     for item in tech_security_contract_scan:
#         text_template = Template(event.get(slug='creation_contract_isnotcompleted').template)
#         tags = Context({
#             'application': 'технической охраны',
#             'contract'   : item.TechSecurityContract.NumContractInternal,
#             'branch'     : item.TechSecurityContract.Branch.NameBranch,
#             'date_start' : item.TechSecurityContract.DateConclusion,
#         })
#         notification.objects.create(application="tech_security", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.TechSecurityContract.ServingCompany).first())
#
#     # Допсоглашения, у которых через 2 недели после подписания не загружен скан
#     tech_security_subcontract_filter = TechSecuritySubContract.objects.filter(DateSubContract__gt=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     tech_security_subcontract_scan = TechSecuritySubContract_scan.objects.exclude(TechSecuritySubContract=tech_security_subcontract_filter)
#     for item in tech_security_subcontract_scan:
#         text_template = Template(event.get(slug='creation_subcontract_isnotcompleted').template)
#         tags = Context({
#             'application': 'технической охраны',
#             'branch'     : item.TechSecuritySubContract.TechSecurityContract.Branch.NameBranch,
#             'contract'   : item.TechSecuritySubContract.TechSecurityContract.NumContractInternal,
#             'date_start' : item.TechSecuritySubContract.TechSecurityContract.DateConclusion,
#             'subcontract': item.TechSecuritySubContract.NumSubContract
#         })
#         notification.objects.create(application="tech_security", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.TechSecurityContract.ServingCompany).first())
#
#     # Объекты, у которых заканчивается срок аренды через 2 недели
#     tech_security_object = TechSecurityObject.objects.filter(StatusSecurity=status)
#     tech_security_object_rent = TechSecurityObjectRent.objects.filter(TechSecurityObject=tech_security_object, DateEndContractRent=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     for item in tech_security_object_rent:
#         text_template = Template(event.get(slug='expires_rent').template)
#         tags = Context({
#             'application': 'технической охраны',
#             'branch'     : item.TechSecurityObject.TechSecurityContract.Branch.NameBranch,
#             'contract'   : item.TechSecurityObject.TechSecurityContract.NumContractInternal,
#             'date_start' : item.TechSecurityObject.TechSecurityContract.DateConclusion,
#             'object'     : item.TechSecurityObject.NumObjectPCN,
#             'date_end'   : item.DateEndContractRent,
#         })
#         notification.objects.create(application="tech_security", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.TechSecurityContract.ServingCompany).first(), limitation=item.DateEndContractRent)
#     # ------------------------------------------------------------------------------------------------
#
#     # ------------------------------------------ Монтаж ----------------------------------------------
#     # Договора, у которых заканчивается срок действия через 3 недели
#     build_service_contract = BuildServiceContract.objects.filter(DateTermination=(datetime.datetime.today()+datetime.timedelta(weeks=3)))
#     for item in build_service_contract:
#         text_template = Template(event.get(slug='expires_contract').template)
#         tags = Context({
#             'application': 'монтажа',
#             'contract'  : item.NumContractInternal,
#             'branch'    : item.Branch.NameBranch,
#             'date_start': item.DateConclusion,
#             'date_end'  : item.DateTermination,
#         })
#         notification.objects.create(application="build_service", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.ServingCompany).first(), limitation=item.DateTermination)
#
#     # Договора, у которых через 2 недели после подписания не загружен скан
#     build_service_contract_filter = BuildServiceContract.objects.filter(DateConclusion__gt=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     build_service_contract_scan = BuildServiceContract_scan.objects.exclude(BuildServiceContract=build_service_contract_filter)
#     for item in build_service_contract_scan:
#         text_template = Template(event.get(slug='creation_contract_isnotcompleted').template)
#         tags = Context({
#             'application': 'монтажа',
#             'contract'   : item.BuildServiceContract.NumContractInternal,
#             'branch'     : item.BuildServiceContract.Branch.NameBranch,
#             'date_start' : item.BuildServiceContract.DateConclusion,
#         })
#         notification.objects.create(application="build_service", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.BuildServiceContract.ServingCompany).first())
#
#     # Допсоглашения, у которых через 2 недели после подписания не загружен скан
#     # build_service_subcontract_filter = BuildServiceSubContract.objects.filter(DateSubContract__gte=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     # build_service_subcontract_scan = BuildServiceSubContract_scan.objects.exclude(BuildServiceSubContract__in=tech_security_subcontract_filter)
#     # ------------------------------------------------------------------------------------------------
#
#     # ---------------------------------- Техническое обслуживание ------------------------------------
#     # Договора, у которых заканчивается срок действия через 3 недели
#     maintenance_service_contract = MaintenanceServiceContract.objects.filter(DateTermination=(datetime.datetime.today()+datetime.timedelta(weeks=3)))
#     for item in maintenance_service_contract:
#         text_template = Template(event.get(slug='expires_contract').template)
#         tags = Context({
#             'application': 'технического обслуживания',
#             'contract'  : item.NumContractInternal,
#             'branch'    : item.Branch.NameBranch,
#             'date_start': item.DateConclusion,
#             'date_end'  : item.DateTermination,
#         })
#         notification.objects.create(application="maintenance_service", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.ServingCompany).first(), limitation=item.DateTermination)
#
#     # Договора, у которых через 2 недели после подписания не загружен скан
#     maintenance_service_contract_filter = MaintenanceServiceContract.objects.filter(DateConclusion__gt=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     maintenance_service_contract_scan = MaintenanceServiceContract_scan.objects.exclude(MaintenanceServiceContract__in=maintenance_service_contract_filter)
#     for item in maintenance_service_contract_scan:
#         text_template = Template(event.get(slug='creation_contract_isnotcompleted').template)
#         tags = Context({
#             'application': 'технического обслуживания',
#             'contract'   : item.MaintenanceServiceContract.NumContractInternal,
#             'branch'     : item.MaintenanceServiceContract.Branch.NameBranch,
#             'date_start' : item.MaintenanceServiceContract.DateConclusion,
#         })
#         notification.objects.create(application="maintenance_service", note=text_template.render(tags), responsible=custom_user_profile.user.filter(scompany=item.MaintenanceServiceContract.ServingCompany).first())
#
#     # Допсоглашения, у которых через 2 недели после подписания не загружен скан
#     # build_service_subcontract_filter = BuildServiceSubContract.objects.filter(DateSubContract__gte=(datetime.datetime.today()+datetime.timedelta(weeks=2)))
#     # build_service_subcontract_scan = BuildServiceSubContract_scan.objects.exclude(BuildServiceSubContract__in=tech_security_subcontract_filter)
#     # ------------------------------------------------------------------------------------------------


def get_notifications(request):
    return render(request, 'notifications.html', {'notifications': notification.objects.filter(responsible=request.user)})


def get_notification(request,notification_id=None):
    notification.objects.filter(responsible=request.user,read=False).update(read=True)
    return render(request, 'notification.html', {'notification':notification.objects.get(id=notification_id)})
