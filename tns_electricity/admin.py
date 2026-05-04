# tns_electricity/admin.py

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.contrib import messages
from django.utils.html import format_html
from .models import MeterReading, Bill, BillDetail, Payment


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    """Админка для показаний счётчика"""
    list_display = ['id', 'date', 'day_reading', 'night_reading', 'is_initial']
    list_display_links = ['id', 'date']
    list_filter = ['date', 'is_initial']
    search_fields = ['day_reading', 'night_reading']
    readonly_fields = ['date']

    fieldsets = (
        ('Информация о показаниях', {
            'fields': ('date', 'day_reading', 'night_reading', 'is_initial', 'note')
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Админка для платежей"""
    list_display = ['id', 'bill_link', 'payment_date', 'payment_amount', 'note']
    list_filter = ['payment_date']
    search_fields = ['note']

    def bill_link(self, obj):
        return format_html('<a href="/custom-admin/tns_electricity/bill/{}/">Счёт #{}</a>', obj.bill.id, obj.bill.id)

    bill_link.short_description = 'Счёт'


# Расширяем админ-панель для добавления кнопок очистки
class CustomAdminSite(admin.AdminSite):
    site_header = 'ТНС энерго Кубань - Администрирование'
    site_title = 'Админ-панель ТНС'
    index_template = 'admin/custom_index.html'  # Указываем кастомный шаблон

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reset-data/', self.admin_view(self.reset_data), name='reset_data'),
            path('reset-data-full/', self.admin_view(self.reset_data_full), name='reset_data_full'),
        ]
        return custom_urls + urls

    def reset_data(self, request):
        # Очистка с сохранением начальных показаний
        try:
            from .models import MeterReading, Bill, BillDetail, Payment

            # Сохраняем начальные показания
            initial = MeterReading.objects.filter(is_initial=True).first()
            if initial:
                day = initial.day_reading
                night = initial.night_reading
                date = initial.reading_date
                note = initial.note

            # Удаляем все данные
            Payment.objects.all().delete()
            BillDetail.objects.all().delete()
            Bill.objects.all().delete()
            MeterReading.objects.filter(is_initial=False).delete()

            # Восстанавливаем начальные показания
            if initial:
                MeterReading.objects.filter(is_initial=True).delete()
                MeterReading.objects.create(
                    day_reading=day,
                    night_reading=night,
                    reading_date=date,
                    is_initial=True,
                    note=note or "Начальные показания счётчика (восстановлены после очистки)"
                )

            self.message_user(request, '✅ Данные успешно очищены! Начальные показания сохранены.', level='SUCCESS')
        except Exception as e:
            self.message_user(request, f'❌ Ошибка при очистке: {str(e)}', level='ERROR')

        return redirect('/custom-admin/')

    def reset_data_full(self, request):
        # Полная очистка всех данных
        try:
            from .models import MeterReading, Bill, BillDetail, Payment

            Payment.objects.all().delete()
            BillDetail.objects.all().delete()
            Bill.objects.all().delete()
            MeterReading.objects.all().delete()

            self.message_user(request, '✅ Полная очистка завершена! Все данные удалены.', level='SUCCESS')
        except Exception as e:
            self.message_user(request, f'❌ Ошибка при очистке: {str(e)}', level='ERROR')

        return redirect('/custom-admin/')


admin_site = CustomAdminSite(name='admin')

# Регистрация моделей
admin_site.register(MeterReading, MeterReadingAdmin)
admin_site.register(Bill, BillAdmin)
admin_site.register(BillDetail, BillDetailAdmin)
admin_site.register(Payment, PaymentAdmin)