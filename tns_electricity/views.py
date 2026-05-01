# tns_electricity/views.py

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json
from io import BytesIO

from .models import MeterReading, Bill, BillDetail, Payment
from .utils import calculate_total

# Импорт для PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def index(request):
    """Главная страница"""
    return render(request, 'tns_electricity/index.html')


@require_http_methods(["GET"])
def get_last_reading(request):
    """Получить последние показания (не начальные)"""
    # Сначала ищем обычные показания
    last_reading = MeterReading.objects.filter(is_initial=False).order_by('-reading_date', '-date').first()

    if last_reading:
        return JsonResponse({
            'day': last_reading.day_reading,
            'night': last_reading.night_reading,
            'date': last_reading.reading_date.strftime(
                '%d.%m.%Y') if last_reading.reading_date else last_reading.date.strftime('%d.%m.%Y %H:%M'),
            'is_initial': False
        })

    # Если нет обычных показаний, показываем начальные как подсказку
    initial_reading = MeterReading.objects.filter(is_initial=True).first()
    if initial_reading:
        return JsonResponse({
            'day': initial_reading.day_reading,
            'night': initial_reading.night_reading,
            'date': initial_reading.reading_date.strftime(
                '%d.%m.%Y') if initial_reading.reading_date else 'Начальные показания',
            'is_initial': True
        })

    return JsonResponse(None, safe=False)


@require_http_methods(["GET"])
def check_initial_readings(request):
    """Проверить, установлены ли начальные показания"""
    initial_reading = MeterReading.objects.filter(is_initial=True).first()

    if initial_reading:
        return JsonResponse({
            'has_initial': True,
            'initial_day': initial_reading.day_reading,
            'initial_night': initial_reading.night_reading,
            'initial_date': initial_reading.reading_date.strftime('%d.%m.%Y') if initial_reading.reading_date else None
        })
    return JsonResponse({'has_initial': False})


@csrf_exempt
@require_http_methods(["POST"])
def save_initial_readings(request):
    """Сохранить начальные показания счётчика"""
    try:
        data = json.loads(request.body)
        day_initial = float(data['day'])
        night_initial = float(data['night'])
        initial_date = data.get('date')

        if initial_date:
            initial_date = datetime.strptime(initial_date, '%Y-%m-%d').date()
        else:
            initial_date = timezone.now().date()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': f'Неверный формат данных: {str(e)}'}, status=400)

    # Проверяем, не установлены ли уже начальные показания
    if MeterReading.objects.filter(is_initial=True).exists():
        return JsonResponse({'error': 'Начальные показания уже установлены'}, status=400)

    # Создаём начальные показания
    initial_reading = MeterReading.objects.create(
        day_reading=day_initial,
        night_reading=night_initial,
        reading_date=initial_date,
        is_initial=True,
        note="Начальные показания счётчика"
    )

    return JsonResponse({
        'success': True,
        'message': 'Начальные показания сохранены',
        'id': initial_reading.id
    })


@csrf_exempt
@require_http_methods(["POST"])
def edit_initial_readings(request):
    """Редактировать начальные показания счётчика"""
    try:
        data = json.loads(request.body)
        day_initial = float(data['day'])
        night_initial = float(data['night'])
        initial_date = data.get('date')

        if initial_date:
            initial_date = datetime.strptime(initial_date, '%Y-%m-%d').date()
        else:
            initial_date = timezone.now().date()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': f'Неверный формат данных: {str(e)}'}, status=400)

    # Находим начальные показания
    initial_reading = MeterReading.objects.filter(is_initial=True).first()
    if not initial_reading:
        return JsonResponse({'error': 'Начальные показания не найдены'}, status=404)

    # Проверяем, можно ли редактировать (нет ли связанных расчётов)
    has_bills = Bill.objects.filter(prev_reading=initial_reading).exists()
    if has_bills:
        return JsonResponse(
            {'error': 'Нельзя редактировать начальные показания, так как по ним уже были произведены расчёты'},
            status=400)

    # Обновляем начальные показания
    initial_reading.day_reading = day_initial
    initial_reading.night_reading = night_initial
    initial_reading.reading_date = initial_date
    initial_reading.save()

    return JsonResponse({
        'success': True,
        'message': 'Начальные показания обновлены',
        'id': initial_reading.id
    })


@require_http_methods(["DELETE"])
def delete_initial_readings(request):
    """Удалить начальные показания счётчика"""
    initial_reading = MeterReading.objects.filter(is_initial=True).first()
    if not initial_reading:
        return JsonResponse({'error': 'Начальные показания не найдены'}, status=404)

    # Проверяем, можно ли удалить (нет ли связанных расчётов)
    has_bills = Bill.objects.filter(prev_reading=initial_reading).exists()
    if has_bills:
        return JsonResponse(
            {'error': 'Нельзя удалить начальные показания, так как по ним уже были произведены расчёты'}, status=400)

    initial_reading.delete()

    return JsonResponse({
        'success': True,
        'message': 'Начальные показания удалены'
    })


def calculate_period_distribution(prev_reading, current_reading, day_consumption, night_consumption):
    """Распределяет расход по месяцам при длительном периоде"""
    if prev_reading.reading_date and current_reading.reading_date:
        months_diff = (current_reading.reading_date.year - prev_reading.reading_date.year) * 12 + \
                      (current_reading.reading_date.month - prev_reading.reading_date.month)
        days_diff = (current_reading.reading_date - prev_reading.reading_date).days
    else:
        months_diff = max(1, (current_reading.date.date() - prev_reading.date.date()).days // 30)
        days_diff = (current_reading.date.date() - prev_reading.date.date()).days

    if months_diff <= 0:
        months_diff = 1

    day_per_month = day_consumption / months_diff
    night_per_month = night_consumption / months_diff

    total_cost = 0
    monthly_breakdown = []

    for month in range(months_diff):
        month_result = calculate_total(day_per_month, night_per_month)
        total_cost += month_result['total_cost']
        monthly_breakdown.append({
            'month': month + 1,
            'day_consumption': round(day_per_month, 2),
            'night_consumption': round(night_per_month, 2),
            'total_consumption': round(day_per_month + night_per_month, 2),
            'cost': round(month_result['total_cost'], 2),
            'details': month_result
        })

    return {
        'total_cost': total_cost,
        'months_count': months_diff,
        'days_count': days_diff,
        'day_per_month': day_per_month,
        'night_per_month': night_per_month,
        'monthly_breakdown': monthly_breakdown
    }


@csrf_exempt
@require_http_methods(["POST"])
def calculate(request):
    """Рассчитать стоимость и сохранить"""
    try:
        data = json.loads(request.body)
        day_current = float(data['day_current'])
        night_current = float(data['night_current'])

        reading_date_str = data.get('reading_date', None)
        if reading_date_str:
            reading_date = datetime.strptime(reading_date_str, '%Y-%m-%d').date()
        else:
            reading_date = timezone.now().date()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': f'Неверный формат данных: {str(e)}'}, status=400)

    # Получаем начальные показания
    initial_reading = MeterReading.objects.filter(is_initial=True).first()
    if not initial_reading:
        return JsonResponse({
            'error': 'Сначала установите начальные показания счётчика!'
        }, status=400)

    # Получаем последние обычные показания (не начальные)
    last_reading = MeterReading.objects.filter(is_initial=False).order_by('-reading_date', '-date').first()

    # КРИТИЧНО: Определяем предыдущие показания
    # Если есть обычные показания - используем их
    # Если нет обычных показаний - используем начальные
    if last_reading:
        prev_reading = last_reading
        print(
            f"Используем предыдущие обычные показания: День={prev_reading.day_reading}, Ночь={prev_reading.night_reading}")
    else:
        prev_reading = initial_reading
        print(f"Используем начальные показания: День={prev_reading.day_reading}, Ночь={prev_reading.night_reading}")

    # Сохраняем текущие показания
    current_reading = MeterReading.objects.create(
        day_reading=day_current,
        night_reading=night_current,
        reading_date=reading_date,
        is_initial=False
    )

    # Расчёт потребления
    day_consumption = day_current - prev_reading.day_reading
    night_consumption = night_current - prev_reading.night_reading

    print(f"Расчёт: day_current={day_current} - day_prev={prev_reading.day_reading} = {day_consumption}")
    print(f"Расчёт: night_current={night_current} - night_prev={prev_reading.night_reading} = {night_consumption}")

    if day_consumption < 0 or night_consumption < 0:
        current_reading.delete()
        return JsonResponse({
            'error': f'Текущие показания меньше предыдущих! День: {prev_reading.day_reading} → {day_current}, Ночь: {prev_reading.night_reading} → {night_current}'
        }, status=400)

    if day_consumption == 0 and night_consumption == 0:
        current_reading.delete()
        return JsonResponse({
            'error': 'Расход равен нулю. Показания не изменились с момента предыдущей передачи.'
        }, status=400)

    # Проверяем период
    period_detected = False
    period_data = None

    if prev_reading.reading_date and current_reading.reading_date:
        days_diff = (current_reading.reading_date - prev_reading.reading_date).days
        if days_diff > 45:
            period_detected = True
            period_data = calculate_period_distribution(
                prev_reading, current_reading, day_consumption, night_consumption
            )

    if period_detected and period_data:
        bill = Bill.objects.create(
            prev_reading=prev_reading,
            current_reading=current_reading,
            day_consumption=round(day_consumption, 2),
            night_consumption=round(night_consumption, 2),
            total_consumption=round(day_consumption + night_consumption, 2),
            total_cost=round(period_data['total_cost'], 2)
        )

        for month_data in period_data['monthly_breakdown']:
            for zone in ['day', 'night']:
                for detail in month_data['details'][zone]['details']:
                    BillDetail.objects.create(
                        bill=bill,
                        zone=zone,
                        range_num=detail['range'],
                        kwh=round(detail['kwh'], 2),
                        tariff=detail['tariff'],
                        cost=round(detail['cost'], 2)
                    )

        return JsonResponse({
            'success': True,
            'period_detected': True,
            'months_count': period_data['months_count'],
            'days_count': period_data['days_count'],
            'day_prev': prev_reading.day_reading,
            'night_prev': prev_reading.night_reading,
            'day_current': day_current,
            'night_current': night_current,
            'day_total': round(day_consumption, 2),
            'night_total': round(night_consumption, 2),
            'total_consumption': round(day_consumption + night_consumption, 2),
            'total_cost': round(period_data['total_cost'], 2),
            'day_per_month': round(period_data['day_per_month'], 2),
            'night_per_month': round(period_data['night_per_month'], 2),
            'monthly_breakdown': period_data['monthly_breakdown']
        })
    else:
        calculation = calculate_total(day_consumption, night_consumption)

        bill = Bill.objects.create(
            prev_reading=prev_reading,
            current_reading=current_reading,
            day_consumption=round(day_consumption, 2),
            night_consumption=round(night_consumption, 2),
            total_consumption=round(calculation['total_kwh'], 2),
            total_cost=round(calculation['total_cost'], 2)
        )

        for zone in ['day', 'night']:
            for detail in calculation[zone]['details']:
                BillDetail.objects.create(
                    bill=bill,
                    zone=zone,
                    range_num=detail['range'],
                    kwh=round(detail['kwh'], 2),
                    tariff=detail['tariff'],
                    cost=round(detail['cost'], 2)
                )

        return JsonResponse({
            'success': True,
            'period_detected': False,
            'day_prev': prev_reading.day_reading,
            'night_prev': prev_reading.night_reading,
            'day_current': day_current,
            'night_current': night_current,
            'day_consumption': round(day_consumption, 2),
            'night_consumption': round(night_consumption, 2),
            'total_consumption': round(calculation['total_kwh'], 2),
            'total_cost': round(calculation['total_cost'], 2),
            'details': calculation
        })


@csrf_exempt
@require_http_methods(["POST"])
def recalculate(request):
    """Пересчитать стоимость при повторном вводе показаний"""
    try:
        data = json.loads(request.body)
        reading_id = int(data['reading_id'])
        day_new = float(data['day_new'])
        night_new = float(data['night_new'])
        reading_date_str = data.get('reading_date', None)

        if reading_date_str:
            reading_date = datetime.strptime(reading_date_str, '%Y-%m-%d').date()
        else:
            reading_date = timezone.now().date()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': f'Неверный формат данных: {str(e)}'}, status=400)

    try:
        current_reading = MeterReading.objects.get(id=reading_id, is_initial=False)
    except MeterReading.DoesNotExist:
        return JsonResponse({'error': 'Показания не найдены'}, status=404)

    # Получаем предыдущие показания
    previous_readings = MeterReading.objects.filter(
        is_initial=False,
        reading_date__lt=current_reading.reading_date
    ).exclude(id=current_reading.id).order_by('-reading_date', '-date')

    if previous_readings:
        prev_reading = previous_readings[0]
    else:
        prev_reading = MeterReading.objects.filter(is_initial=True).first()
        if not prev_reading:
            return JsonResponse({'error': 'Начальные показания не найдены'}, status=404)

    # Обновляем показания
    old_day = current_reading.day_reading
    old_night = current_reading.night_reading
    old_date = current_reading.reading_date

    current_reading.day_reading = day_new
    current_reading.night_reading = night_new
    current_reading.reading_date = reading_date
    current_reading.save()

    # Пересчитываем потребление
    day_consumption = day_new - prev_reading.day_reading
    night_consumption = night_new - prev_reading.night_reading

    if day_consumption < 0 or night_consumption < 0:
        # Откатываем изменения
        current_reading.day_reading = old_day
        current_reading.night_reading = old_night
        current_reading.reading_date = old_date
        current_reading.save()
        return JsonResponse({
            'error': f'Новые показания меньше предыдущих! День: {prev_reading.day_reading} → {day_new}'
        }, status=400)

    # Находим связанный счёт и обновляем его
    bill = Bill.objects.filter(current_reading=current_reading).first()

    if bill:
        # Проверяем период
        period_detected = False
        period_data = None

        if prev_reading.reading_date and current_reading.reading_date:
            days_diff = (current_reading.reading_date - prev_reading.reading_date).days
            if days_diff > 45:
                period_detected = True
                period_data = calculate_period_distribution(
                    prev_reading, current_reading, day_consumption, night_consumption
                )

        if period_detected and period_data:
            # Обновляем счёт с распределением
            bill.day_consumption = round(day_consumption, 2)
            bill.night_consumption = round(night_consumption, 2)
            bill.total_consumption = round(day_consumption + night_consumption, 2)
            bill.total_cost = round(period_data['total_cost'], 2)
            bill.save()

            # Удаляем старые детали и создаём новые
            BillDetail.objects.filter(bill=bill).delete()

            for month_data in period_data['monthly_breakdown']:
                for zone in ['day', 'night']:
                    for detail in month_data['details'][zone]['details']:
                        BillDetail.objects.create(
                            bill=bill,
                            zone=zone,
                            range_num=detail['range'],
                            kwh=round(detail['kwh'], 2),
                            tariff=detail['tariff'],
                            cost=round(detail['cost'], 2)
                        )

            return JsonResponse({
                'success': True,
                'message': 'Показания обновлены и пересчитаны',
                'period_detected': True,
                'months_count': period_data['months_count'],
                'days_count': period_data['days_count'],
                'day_prev': prev_reading.day_reading,
                'night_prev': prev_reading.night_reading,
                'day_current': day_new,
                'night_current': night_new,
                'day_total': round(day_consumption, 2),
                'night_total': round(night_consumption, 2),
                'total_consumption': round(day_consumption + night_consumption, 2),
                'total_cost': round(period_data['total_cost'], 2),
                'day_per_month': round(period_data['day_per_month'], 2),
                'night_per_month': round(period_data['night_per_month'], 2),
                'monthly_breakdown': period_data['monthly_breakdown']
            })
        else:
            calculation = calculate_total(day_consumption, night_consumption)

            # Обновляем счёт
            bill.day_consumption = round(day_consumption, 2)
            bill.night_consumption = round(night_consumption, 2)
            bill.total_consumption = round(calculation['total_kwh'], 2)
            bill.total_cost = round(calculation['total_cost'], 2)
            bill.save()

            # Удаляем старые детали и создаём новые
            BillDetail.objects.filter(bill=bill).delete()

            for zone in ['day', 'night']:
                for detail in calculation[zone]['details']:
                    BillDetail.objects.create(
                        bill=bill,
                        zone=zone,
                        range_num=detail['range'],
                        kwh=round(detail['kwh'], 2),
                        tariff=detail['tariff'],
                        cost=round(detail['cost'], 2)
                    )

            return JsonResponse({
                'success': True,
                'message': 'Показания обновлены и пересчитаны',
                'period_detected': False,
                'day_prev': prev_reading.day_reading,
                'night_prev': prev_reading.night_reading,
                'day_current': day_new,
                'night_current': night_new,
                'day_consumption': round(day_consumption, 2),
                'night_consumption': round(night_consumption, 2),
                'total_consumption': round(calculation['total_kwh'], 2),
                'total_cost': round(calculation['total_cost'], 2),
                'details': calculation
            })
    else:
        return JsonResponse({
            'success': True,
            'message': 'Показания обновлены без перерасчёта (счёт не найден)'
        })

@require_http_methods(["GET"])
def get_history(request):
    """Получить историю платежей"""
    bills = Bill.objects.all().order_by('-date')[:20]
    history = []
    for bill in bills:
        payments = Payment.objects.filter(bill=bill)
        total_paid = sum(p.payment_amount for p in payments)

        history.append({
            'id': bill.id,
            'date': bill.date.strftime('%d.%m.%Y'),
            'time': bill.date.strftime('%H:%M'),
            'total_consumption': bill.total_consumption,
            'total_cost': bill.total_cost,
            'total_paid': total_paid,
            'balance': bill.total_cost - total_paid,
            'payments': [{
                'date': p.payment_date.strftime('%d.%m.%Y'),
                'amount': p.payment_amount,
                'note': p.note
            } for p in payments]
        })
    return JsonResponse(history, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def add_payment(request):
    """Добавить платеж"""
    try:
        data = json.loads(request.body)
        bill_id = int(data['bill_id'])
        payment_amount = float(data['payment_amount'])
        payment_date_str = data.get('payment_date')
        note = data.get('note', '')

        if payment_date_str:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        else:
            payment_date = timezone.now().date()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JsonResponse({'error': f'Неверный формат данных: {str(e)}'}, status=400)

    try:
        bill = Bill.objects.get(id=bill_id)
    except Bill.DoesNotExist:
        return JsonResponse({'error': 'Счёт не найден'}, status=404)

    payment = Payment.objects.create(
        bill=bill,
        payment_amount=payment_amount,
        payment_date=payment_date,
        note=note
    )

    return JsonResponse({
        'success': True,
        'message': 'Платёж добавлен',
        'payment_id': payment.id
    })


@csrf_exempt
@require_http_methods(["POST"])
def export_pdf(request):
    """Экспорт результата в PDF"""
    if not REPORTLAB_AVAILABLE:
        return JsonResponse({'error': 'ReportLab не установлен. Установите: pip install reportlab'}, status=500)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, alignment=1,
                                 textColor=colors.HexColor('#1a5276'))

    story = []
    story.append(Paragraph("ТНС энерго Кубань", title_style))
    story.append(Paragraph("Квитанция об оплате электроэнергии", styles['Heading2']))
    story.append(Spacer(1, 20))

    if data.get('period_detected'):
        story.append(
            Paragraph(f"<b>Период: {data.get('months_count', 1)} месяцев ({data.get('days_count', 0)} дней)</b>",
                      styles['Normal']))
        story.append(Spacer(1, 10))

    if data.get('period_detected'):
        readings_data = [
            ["", "Предыдущие", "Текущие", "Всего за период"],
            ["День (Т1)", f"{data['day_prev']:.0f}", f"{data['day_current']:.0f}", f"{data['day_total']:.2f}"],
            ["Ночь (Т2)", f"{data['night_prev']:.0f}", f"{data['night_current']:.0f}", f"{data['night_total']:.2f}"],
            ["Всего", "", "", f"{data['total_consumption']:.2f}"]
        ]
    else:
        readings_data = [
            ["", "Предыдущие", "Текущие", "Расход (кВт·ч)"],
            ["День (Т1)", f"{data['day_prev']:.0f}", f"{data['day_current']:.0f}", f"{data['day_consumption']:.2f}"],
            ["Ночь (Т2)", f"{data['night_prev']:.0f}", f"{data['night_current']:.0f}",
             f"{data['night_consumption']:.2f}"],
            ["Всего", "", "", f"{data['total_consumption']:.2f}"]
        ]

    t = Table(readings_data, colWidths=[80, 100, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    if data.get('period_detected') and data.get('monthly_breakdown'):
        story.append(Paragraph("<b>Помесячная разбивка:</b>", styles['Heading3']))
        story.append(Spacer(1, 10))

        for month in data['monthly_breakdown']:
            story.append(Paragraph(f"<b>Месяц {month['month']}:</b>", styles['Normal']))
            story.append(Paragraph(
                f"Расход: {month['day_consumption']} (день) + {month['night_consumption']} (ночь) = {month['total_consumption']} кВт·ч",
                styles['Normal']))
            story.append(Paragraph(f"Стоимость: {month['cost']:.2f} ₽", styles['Normal']))
            story.append(Spacer(1, 5))

    story.append(Paragraph(f"<b>ИТОГО К ОПЛАТЕ: {data['total_cost']:.2f} ₽</b>",
                           ParagraphStyle('Total', parent=styles['Heading1'],
                                          textColor=colors.HexColor('#e74c3c'),
                                          alignment=1)))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="kvitanciya_tns.pdf"'
    return response

@require_http_methods(["GET"])
def get_reading_by_bill(request, bill_id):
    """Получить показания по ID счёта"""
    try:
        bill = Bill.objects.get(id=bill_id)
        reading = bill.current_reading
        return JsonResponse({
            'reading_id': reading.id,
            'day_reading': reading.day_reading,
            'night_reading': reading.night_reading,
            'reading_date': reading.reading_date.strftime('%Y-%m-%d') if reading.reading_date else None
        })
    except Bill.DoesNotExist:
        return JsonResponse({'error': 'Счёт не найден'}, status=404)