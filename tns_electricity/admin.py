# tns_electricity/admin.py

from django.contrib import admin
from .models import MeterReading, Bill, BillDetail


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    """Админка для показаний счётчика"""
    list_display = ['id', 'date', 'day_reading', 'night_reading']
    list_display_links = ['id', 'date']
    list_filter = ['date']
    search_fields = ['day_reading', 'night_reading']
    readonly_fields = ['date']

    fieldsets = (
        ('Информация о показаниях', {
            'fields': ('date', 'day_reading', 'night_reading')
        }),
    )

    class Meta:
        verbose_name = 'Показание счётчика'
        verbose_name_plural = 'Показания счётчика'


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Админка для счетов"""
    list_display = ['id', 'date', 'total_consumption', 'total_cost', 'get_period']
    list_display_links = ['id', 'date']
    list_filter = ['date']
    search_fields = ['total_cost']
    readonly_fields = ['date']

    fieldsets = (
        ('Период', {
            'fields': ('date',)
        }),
        ('Показания', {
            'fields': ('prev_reading', 'current_reading')
        }),
        ('Расход', {
            'fields': ('day_consumption', 'night_consumption', 'total_consumption')
        }),
        ('Стоимость', {
            'fields': ('total_cost',)
        }),
    )

    def get_period(self, obj):
        """Возвращает период между показаниями"""
        if obj.prev_reading and obj.current_reading:
            return f"{obj.prev_reading.date.strftime('%d.%m.%Y')} - {obj.current_reading.date.strftime('%d.%m.%Y')}"
        return "Не определён"

    get_period.short_description = 'Период'
    get_period.admin_order_field = 'date'


@admin.register(BillDetail)
class BillDetailAdmin(admin.ModelAdmin):
    """Админка для детализации счетов"""
    list_display = ['id', 'bill', 'get_bill_date', 'zone', 'range_num', 'kwh', 'tariff', 'cost']
    list_display_links = ['id']
    list_filter = ['zone', 'range_num', 'bill__date']
    search_fields = ['bill__id']

    fieldsets = (
        ('Счёт', {
            'fields': ('bill',)
        }),
        ('Детали', {
            'fields': ('zone', 'range_num', 'kwh', 'tariff', 'cost')
        }),
    )

    def get_bill_date(self, obj):
        """Возвращает дату счёта"""
        return obj.bill.date.strftime('%d.%m.%Y %H:%M')

    get_bill_date.short_description = 'Дата счёта'
    get_bill_date.admin_order_field = 'bill__date'