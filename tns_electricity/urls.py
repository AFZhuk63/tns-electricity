# tns_electricity/urls.py

from django.urls import path
from . import views

app_name = 'tns_electricity'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/last-reading/', views.get_last_reading, name='last_reading'),
    path('api/check-initial-readings/', views.check_initial_readings, name='check_initial'),
    path('api/save-initial-readings/', views.save_initial_readings, name='save_initial'),
    path('api/edit-initial-readings/', views.edit_initial_readings, name='edit_initial'),
    path('api/delete-initial-readings/', views.delete_initial_readings, name='delete_initial'),
    path('api/calculate/', views.calculate, name='calculate'),
    path('api/recalculate/', views.recalculate, name='recalculate'),
    path('api/history/', views.get_history_table, name='history'),  # Изменено: get_history -> get_history_table
    path('api/add-payment/', views.add_payment, name='add_payment'),
    path('api/get-reading-by-bill/<int:bill_id>/', views.get_reading_by_bill, name='get_reading_by_bill'),
    path('api/export-pdf/', views.export_pdf, name='export_pdf'),
    path('api/export-history-pdf/', views.export_history_pdf, name='export_history_pdf'),
    path('api/export-history-excel/', views.export_history_excel, name='export_history_excel'),
    path('api/history-table/', views.get_history_table, name='history_table'),
]