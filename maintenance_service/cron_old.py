from datetime import datetime
from django.db.models import Sum, FloatField, Q
from django.shortcuts import redirect

from accounting.models import credited_with_paid
from base.views import logging_event
from maintenance_service.models import MaintenanceServiceObject, MaintenanceServiceContract, MaintenancePereodicAccrual
from reference_books.models import TypeDocument, ListMonth

__author__ = 'bondarenkoav'


# def cron_charge_subscription_contract():
#     created_bill = []
#     type_dct = TypeDocument.objects.get(slug='maintenance_service_contract')
#
#     action_contracts = MaintenanceServiceContract.objects.\
#         filter(Q(DateTermination__gt=datetime.today())|Q(DateTermination__isnull=True))
#
#     contracts = action_contracts.filter(PereodicAccrualMonth=)
















    # # автоматическое начисление абонплаты - ежемесячное
    # contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='monthly'))
    # for contract in contracts:
    #     objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
    #                                                       DateStart__lte=datetime.today(),
    #                                                       MaintenanceServiceContract=contract.id)
    #
    #     SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
    #
    #     if SumPriceServices['summ_contract']:
    #         created_bill = credited_with_paid.objects.create(
    #             dct=contract.id,
    #             date_event=datetime.today(),
    #             type_dct=type_dct,
    #             branch=contract.Branch,
    #             scompany=contract.ServingCompany,
    #             summ=SumPriceServices['summ_contract']
    #         )
    # objects = contracts = SumPriceServices = []
    #
    # # автоматическое начисление абонплаты - квартальное
    # if datetime.today().month in [3, 6, 9, 12]:
    #     contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='quarterly'))
    #     for contract in contracts:
    #         objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
    #                                                           DateStart__lte=datetime.today(),
    #                                                           MaintenanceServiceContract=contract.id)
    #
    #         SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
    #
    #         if SumPriceServices['summ_contract']:
    #             created_bill = credited_with_paid.objects.create(
    #                 dct=contract.id,
    #                 date_event=datetime.today(),
    #                 type_dct=type_dct,
    #                 branch=contract.Branch,
    #                 scompany=contract.ServingCompany,
    #                 summ=SumPriceServices['summ_contract']
    #             )
    #     objects = contracts = SumPriceServices = []
    #
    # # автоматическое начисление абонплаты - полугодичное
    # if datetime.today().month in [6, 12]:
    #     contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='halfyear'))
    #     for contract in contracts:
    #         objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
    #                                                           DateStart__lte=datetime.today(),
    #                                                           MaintenanceServiceContract=contract.id)
    #
    #         SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
    #
    #         if SumPriceServices['summ_contract']:
    #             created_bill = credited_with_paid.objects.create(
    #                 dct=contract.id,
    #                 date_event=datetime.today(),
    #                 type_dct=type_dct,
    #                 branch=contract.Branch,
    #                 scompany=contract.ServingCompany,
    #                 summ=SumPriceServices['summ_contract']
    #             )
    #     objects = contracts = SumPriceServices = []
    #
    # if created_bill:
    #     logging_event('auto_calculation_cost_service_contract', None, '', 'maintenance_service', 'system')


def cron_charge_subscription_contract_manual(request):
    created_bill = []
    type_dct = TypeDocument.objects.get(slug='maintenance_service_contract')
    per_accural = MaintenancePereodicAccrual.objects.all()

    action_contracts = MaintenanceServiceContract.objects.\
        filter(Q(DateTermination__gt=datetime.today())|Q(DateTermination__isnull=True))

    contracts = action_contracts.filter(PereodicAccrualMonth=ListMonth.objects.get(id=datetime.now().month))
    for contract in contracts:
        objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
                                                            DateStart__lte=datetime.today(),
                                                            MaintenanceServiceContract=contract.id)

        SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))

        if SumPriceServices['summ_contract']:
            created_bill = credited_with_paid.objects.create(
                dct=contract.id,
                date_event=datetime.today(),
                type_dct=type_dct,
                branch=contract.Branch,
                scompany=contract.ServingCompany,
                summ=SumPriceServices['summ_contract']
            )

    return redirect('index:dashboard')


# def cron_charge_subscription_contract_manual(request):
#     created_bill = []
#     type_dct = TypeDocument.objects.get(slug='maintenance_service_contract')
#     per_accural = MaintenancePereodicAccrual.objects.all()
#
#     action_contracts = MaintenanceServiceContract.objects.\
#         filter(Q(DateTermination__gt=datetime.today())|Q(DateTermination__isnull=True))
#
#     # автоматическое начисление абонплаты - ежемесячное
#     contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='monthly'))
#     for contract in contracts:
#         objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
#                                                           DateStart__lte=datetime.today(),
#                                                           MaintenanceServiceContract=contract.id)
#
#         SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
#
#         if SumPriceServices['summ_contract']:
#             created_bill = credited_with_paid.objects.create(
#                 dct=contract.id,
#                 date_event=datetime.today(),
#                 type_dct=type_dct,
#                 branch=contract.Branch,
#                 scompany=contract.ServingCompany,
#                 summ=SumPriceServices['summ_contract']
#             )
#     objects = contracts = SumPriceServices = []
#
#     # автоматическое начисление абонплаты - квартальное
#     if datetime.today().month in [3, 6, 9, 12]:
#         contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='quarterly'))
#         for contract in contracts:
#             objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
#                                                               DateStart__lte=datetime.today(),
#                                                               MaintenanceServiceContract=contract.id)
#
#             SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
#
#             if SumPriceServices['summ_contract']:
#                 created_bill = credited_with_paid.objects.create(
#                     dct=contract.id,
#                     date_event=datetime.today(),
#                     type_dct=type_dct,
#                     branch=contract.Branch,
#                     scompany=contract.ServingCompany,
#                     summ=SumPriceServices['summ_contract']
#                 )
#         objects = contracts = SumPriceServices = []
#
#     # автоматическое начисление абонплаты - полугодичное
#     if datetime.today().month in [6, 12]:
#         contracts = action_contracts.filter(PereodicAccrual=per_accural.get(slug='halfyear'))
#         for contract in contracts:
#             objects = MaintenanceServiceObject.objects.filter(Q(DateEnd__gt=datetime.today())|Q(DateEnd__isnull=True),
#                                                               DateStart__lte=datetime.today(),
#                                                               MaintenanceServiceContract=contract.id)
#
#             SumPriceServices = objects.aggregate(summ_contract=Sum('Price', output_field=FloatField()))
#
#             if SumPriceServices['summ_contract']:
#                 created_bill = credited_with_paid.objects.create(
#                     dct=contract.id,
#                     date_event=datetime.today(),
#                     type_dct=type_dct,
#                     branch=contract.Branch,
#                     scompany=contract.ServingCompany,
#                     summ=SumPriceServices['summ_contract']
#                 )
#         objects = contracts = SumPriceServices = []
#
#     if created_bill:
#         logging_event('auto_calculation_cost_service_contract', None, '', 'maintenance_service', 'system')
#
#     return redirect('index:dashboard')
