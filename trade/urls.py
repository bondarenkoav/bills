from django.conf.urls import url

from trade.views import add_get_invoice_trade, get_invoices_period, get_invoices_notrepaid, import_invoices_from_1S, \
    clear_import_invoices

__author__ = 'bondarenkoav'
app_name = 'trade_department'

urlpatterns = [
    url(r'^branch-(?P<branch_id>\d+)/(?:invoice-(?P<invoice_id>\d+)/)?$', add_get_invoice_trade, name='addget_invoice'),
    # --------------- Журналы --------------------
    # Вывод накладных за период
    url(r'^invoices_period/$', get_invoices_period, name='journal_invoices_period'),
    # Вывод не закрытых накладных
    url(r'^invoices_notrepaid/$', get_invoices_notrepaid, name='journal_invoices_notrepaid'),
    # --------------- Функции --------------------
    # Очистка таблицы импорта пользователем
    url(r'^import_invoice_1S/clear/city-(?P<city>\w+)/', clear_import_invoices, name='clear_import_invoices'),
    # Импорт накладных
    url(r'^import_invoice_1S/', import_invoices_from_1S, name='import_invoices_from1S'),
]