from django.conf.urls import url

from maintenance_service.cron import cron_charge_subscription_contract_manual
from accounting.views import view_accurals, view_payment, view_act_reconciliation_template, \
    view_change_startbalance_template, add_accural, get_accounting, dlt_payment, dlt_accural, journal_payments_period, \
    journal_accruals_period, sendDebtSMS, sendsms_debtors_list, get_turnover_statement, get_arrears, \
    export_to1S_objects_to_xml, export_to1S_objects_action_nofit, export_to1S_objects_action, export_toexcel_arrears, \
    import_from1C_bankpayments_run, import_from1C_bankpayments, get_turnover_statement_forunits

__author__ = 'bondarenkoav'
app_name = 'finance_department'

urlpatterns = [
    # Просмотр начислений на дату
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/dct-(?P<dct>\d+)/date-(?P<date_event>\w+)/$',
        view_accurals, name='view_accurals'),
    # Изменение
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/id-(?P<payment_id>\d+)/$',
        view_payment, name='view_payment'),
    # Акт сверки
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/act_reconciliation/$',
        view_act_reconciliation_template, name='act_reconciliation'),
    # Скорректировать начальное сальдо
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/change_startbalance/$',
        view_change_startbalance_template, name='change_startbalance'),
    # Внести начисление вручную
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/accural/add/$', add_accural, name='add_accural'),
    # Внесение оплаты
    url(r'^branch-(?P<branch_id>\d+)/scompany-(?P<scompany_id>\d+)/(?:type_dct-(?P<type_dct>\d+)/dct-(?P<dct>\d+)/)?',
        get_accounting, name='payment'),
    # Удаление платежа
    url(r'^delete/payment-(?P<payment_id>\d+)/$', dlt_payment, name='delete_payment'),
    # Удаление начисления
    url(r'^delete/accural-(?P<accural_id>\d+)/$', dlt_accural, name='delete_accural'),

    # -------------- Журналы ----------------
    # Платежи за период
    url(r'^payments_period/$', journal_payments_period, name='journal_payments_period'),
    # Начисления за период
    url(r'^accruals_period/$', journal_accruals_period, name='journal_accruals_period'),

    # ------------- Функции -----------------
    # Рассылка СМС-уведомлений должникам, действие
    url(r'^sendsms_debtors/run/$', sendDebtSMS, name='senddebtsms'),
    # Рассылка СМС-уведомлений должникам
    url(r'^sendsms_debtors/', sendsms_debtors_list, name='sendsms_debtors'),
    # Выгрузка в Excel
    url(r'^export_toexcel_arrears/(?P<cmonths>\d+)/(?P<scompany_id>\d+)/(?P<status>\w+)/$', export_toexcel_arrears, name='export_toexcel_arrears'),

    url(r'^maintenance_charge_subscription/$', cron_charge_subscription_contract_manual, name='maintenance_charge_subscription'),

    # ------------- Отчеты ------------------
    # Оборотная ведомость
    url(r'^turnover_statement/$', get_turnover_statement, name='report_turnover_statement'),
    # Оборотная ведомость по подразделениям
    url(r'^turnover_statement_forunits/$', get_turnover_statement_forunits, name='report_turnover_statement_forunits'),
    # Дебиторская задолженность (сделать постраничку)
    url(r'^arrears/$', get_arrears, name='report_arrears'),

    # ------------- Интеграция с 1С ---------
    # Импорт банковских платежей из 1С
    url(r'^import_bankpayments/', import_from1C_bankpayments, name='import_from1C_bankpayments'),
    url(r'^import_bankpayments_run/', import_from1C_bankpayments_run, name='import_from1C_bankpayments_run'),
    # Экспорт объектов в 1С для создания счетов
    url(r'^export_list_objects/scompany-(?P<scompany_id>\d+)/edo-(?P<edo>\w+)/paymentAfter-(?P<paymentAfter>\w+)/',
        export_to1S_objects_to_xml, name='export_to1S_objects_to_xml'),
    url(r'^export_list_objects/scompany-(?P<scompany_id>\d+)/error/',
        export_to1S_objects_action_nofit, name='export_to1S_objects_action_error'),
    url(r'^export_list_objects/', export_to1S_objects_action, name='export_to1S_objects_action'),
]