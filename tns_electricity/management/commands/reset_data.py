# tns_electricity/management/commands/reset_data.py

"""
Команда для полной очистки данных (сброс до начальной установки)
Использование: python manage.py reset_data
             python manage.py reset_data --keep-initial  # сохранить начальные показания
             python manage.py reset_data --yes  # без подтверждения
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from tns_electricity.models import MeterReading, Bill, BillDetail, Payment


class Command(BaseCommand):
    help = 'Полная очистка данных (сброс до начальной установки)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-initial',
            action='store_true',
            help='Сохранить начальные показания (очистить только историю)',
        )
        parser.add_argument(
            '--yes',
            '-y',
            action='store_true',
            help='Автоматически подтвердить очистку',
        )

    def handle(self, *args, **options):
        # Спрашиваем подтверждение
        if not options['yes']:
            self.stdout.write(self.style.WARNING('ВНИМАНИЕ! Эта операция удалит все данные.'))
            if not options['keep_initial']:
                self.stdout.write(self.style.WARNING('Начальные показания ТАКЖЕ будут удалены.'))
            else:
                self.stdout.write(self.style.INFO('Начальные показания будут сохранены.'))

            confirm = input('Вы уверены? (y/n): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.SUCCESS('Операция отменена.'))
                return

        # Сохраняем начальные показания, если нужно
        initial_reading = None
        if options['keep_initial']:
            initial_reading = MeterReading.objects.filter(is_initial=True).first()
            if initial_reading:
                day = initial_reading.day_reading
                night = initial_reading.night_reading
                date = initial_reading.reading_date
                self.stdout.write(f'📌 Сохраняем начальные показания: День={day}, Ночь={night}, Дата={date}')

        # Удаляем все платежи
        payments_count = Payment.objects.all().count()
        Payment.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено платежей: {payments_count}'))

        # Удаляем все детали счетов
        details_count = BillDetail.objects.all().count()
        BillDetail.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено деталей счетов: {details_count}'))

        # Удаляем все счета
        bills_count = Bill.objects.all().count()
        Bill.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено счетов: {bills_count}'))

        # Удаляем все обычные показания
        regular_count = MeterReading.objects.filter(is_initial=False).count()
        MeterReading.objects.filter(is_initial=False).delete()
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено обычных показаний: {regular_count}'))

        # Обработка начальных показаний
        if not options['keep_initial']:
            # Полное удаление
            initial_count = MeterReading.objects.filter(is_initial=True).count()
            MeterReading.objects.filter(is_initial=True).delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Удалено начальных показаний: {initial_count}'))
            self.stdout.write(self.style.WARNING(
                '⚠️ Начальные показания удалены. При следующем запуске нужно будет установить их заново.'))
        else:
            # Восстанавливаем начальные показания, если они были сохранены
            if initial_reading:
                MeterReading.objects.filter(is_initial=True).delete()
                MeterReading.objects.create(
                    day_reading=day,
                    night_reading=night,
                    reading_date=date,
                    is_initial=True,
                    note="Начальные показания счётчика (восстановлены после очистки)"
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Начальные показания восстановлены: День={day}, Ночь={night}'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ Начальные показания не были найдены и не сохранены.'))

        # Итог
        self.stdout.write(self.style.SUCCESS('\n🎉 Очистка данных завершена!'))
        self.stdout.write(self.style.SUCCESS('=' * 40))

        # Показываем текущее состояние
        self.stdout.write(self.style.INFO(f'📊 Текущее состояние:'))
        self.stdout.write(f'   - Показаний в базе: {MeterReading.objects.count()}')
        self.stdout.write(f'   - Счетов: {Bill.objects.count()}')
        self.stdout.write(f'   - Деталей счетов: {BillDetail.objects.count()}')
        self.stdout.write(f'   - Платежей: {Payment.objects.count()}')