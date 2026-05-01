# tns_electricity/utils.py

# Тарифы ТНС энерго Кубань
TARIFFS = {
    "day": {1: 5.88, 2: 7.99, 3: 16.70},
    "night": {1: 3.16, 2: 4.30, 3: 8.93}
}


def calculate_total(day_consumption, night_consumption):
    """
    Рассчёт стоимости с распределением по суммарным диапазонам
    """
    total_consumption = day_consumption + night_consumption

    if total_consumption == 0:
        return {
            "day": {"kwh": 0, "total": 0, "details": []},
            "night": {"kwh": 0, "total": 0, "details": []},
            "total_kwh": 0,
            "total_cost": 0
        }

    # Доли дня и ночи
    day_share = day_consumption / total_consumption
    night_share = night_consumption / total_consumption

    remaining = total_consumption
    day_total = 0
    night_total = 0
    day_details = []
    night_details = []

    # 1 диапазон (0-1100 кВт·ч)
    range1_limit = 1100
    range1_used = min(remaining, range1_limit)
    if range1_used > 0:
        day_part = range1_used * day_share
        night_part = range1_used * night_share

        day_cost = day_part * TARIFFS["day"][1]
        night_cost = night_part * TARIFFS["night"][1]

        day_total += day_cost
        night_total += night_cost

        if day_part > 0:
            day_details.append({"range": 1, "kwh": day_part, "tariff": TARIFFS["day"][1], "cost": day_cost})
        if night_part > 0:
            night_details.append({"range": 1, "kwh": night_part, "tariff": TARIFFS["night"][1], "cost": night_cost})

        remaining -= range1_used

    # 2 диапазон (1101-1700 кВт·ч) - всего 600 кВт·ч
    if remaining > 0:
        range2_limit = 600
        range2_used = min(remaining, range2_limit)
        if range2_used > 0:
            day_part = range2_used * day_share
            night_part = range2_used * night_share

            day_cost = day_part * TARIFFS["day"][2]
            night_cost = night_part * TARIFFS["night"][2]

            day_total += day_cost
            night_total += night_cost

            if day_part > 0:
                day_details.append({"range": 2, "kwh": day_part, "tariff": TARIFFS["day"][2], "cost": day_cost})
            if night_part > 0:
                night_details.append({"range": 2, "kwh": night_part, "tariff": TARIFFS["night"][2], "cost": night_cost})

            remaining -= range2_used

    # 3 диапазон (>1700 кВт·ч)
    if remaining > 0:
        day_part = remaining * day_share
        night_part = remaining * night_share

        day_cost = day_part * TARIFFS["day"][3]
        night_cost = night_part * TARIFFS["night"][3]

        day_total += day_cost
        night_total += night_cost

        if day_part > 0:
            day_details.append({"range": 3, "kwh": day_part, "tariff": TARIFFS["day"][3], "cost": day_cost})
        if night_part > 0:
            night_details.append({"range": 3, "kwh": night_part, "tariff": TARIFFS["night"][3], "cost": night_cost})

    return {
        "day": {"kwh": day_consumption, "total": day_total, "details": day_details},
        "night": {"kwh": night_consumption, "total": night_total, "details": night_details},
        "total_kwh": total_consumption,
        "total_cost": day_total + night_total
    }