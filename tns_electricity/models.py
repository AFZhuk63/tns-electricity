# tns_electricity/models.py

from django.db import models
from django.utils import timezone

class MeterReading(models.Model):
    """Показания счётчика"""
    date = models.DateTimeField(auto_now_add=True)
    reading_date = models.DateField(verbose_name="Дата показаний", null=True, blank=True)
    day_reading = models.FloatField(verbose_name="День (Т1), кВт·ч")
    night_reading = models.FloatField(verbose_name="Ночь (Т2), кВт·ч")
    is_initial = models.BooleanField(verbose_name="Начальные показания", default=False)
    note = models.TextField(verbose_name="Примечание", blank=True, null=True)

    class Meta:
        verbose_name = "Показание счётчика"
        verbose_name_plural = "Показания счётчика"
        ordering = ['-date']

    def __str__(self):
        date_str = self.reading_date.strftime('%d.%m.%Y') if self.reading_date else self.date.strftime('%d.%m.%Y')
        prefix = "🔰 " if self.is_initial else ""
        return f"{prefix}{date_str} | Д: {self.day_reading} | Н: {self.night_reading}"

class Bill(models.Model):
    """Счёт за период"""
    date = models.DateTimeField(auto_now_add=True)
    prev_reading = models.ForeignKey(MeterReading, on_delete=models.CASCADE, related_name='prev_bills')
    current_reading = models.ForeignKey(MeterReading, on_delete=models.CASCADE, related_name='current_bills')

    day_consumption = models.FloatField(verbose_name="Расход день, кВт·ч")
    night_consumption = models.FloatField(verbose_name="Расход ночь, кВт·ч")
    total_consumption = models.FloatField(verbose_name="Общий расход, кВт·ч")
    total_cost = models.FloatField(verbose_name="Сумма к оплате, руб")

    class Meta:
        verbose_name = "Счёт"
        verbose_name_plural = "Счета"
        ordering = ['-date']

    def __str__(self):
        return f"Счёт от {self.date.strftime('%d.%m.%Y')}: {self.total_cost:.2f} ₽"


class BillDetail(models.Model):
    """Детализация по диапазонам"""
    ZONE_CHOICES = [
        ('day', 'День'),
        ('night', 'Ночь'),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='details')
    zone = models.CharField(max_length=10, choices=ZONE_CHOICES)
    range_num = models.IntegerField(verbose_name="Диапазон")
    kwh = models.FloatField(verbose_name="Расход, кВт·ч")
    tariff = models.FloatField(verbose_name="Тариф, руб")
    cost = models.FloatField(verbose_name="Сумма, руб")

    def __str__(self):
        return f"{self.get_zone_display()} - {self.range_num} диапазон: {self.cost:.2f} ₽"

class Payment(models.Model):
    """Платежи по счетам"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(verbose_name="Дата платежа", default=timezone.now)
    payment_amount = models.FloatField(verbose_name="Сумма платежа, руб")
    note = models.TextField(verbose_name="Примечание", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Платёж {self.payment_amount:.2f}₽ от {self.payment_date.strftime('%d.%m.%Y')}"