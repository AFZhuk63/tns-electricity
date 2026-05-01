import json
import os
from datetime import datetime

DATA_FILE = "tns_readings.json"

# Актуальные тарифы ТНС энерго Кубань с 01.07.2025 по 31.12.2025
# По данным с официальных источников [citation:2][citation:8]
TARIFFS_2025 = {
    "city": {  # Городское население
        1: 7.35,  # 1 диапазон: до 1100 кВт·ч
        2: 10.00,  # 2 диапазон: 1101-1700 кВт·ч
        3: 14.64  # 3 диапазон: свыше 1700 кВт·ч
    },
    "city_electric_stove": {  # Город + электроплита (нужны подтверждающие документы)
        1: 5.88,
        2: 7.99,
        3: 16.70
    },
    "country": {  # Сельское население
        1: 5.15,
        2: 7.00,
        3: 14.64
    },
    "country_electric_heating": {  # Село + электроотопление (в отопительный период)
        1: 5.15,
        2: 7.00,
        3: 14.64
    }
}

# Границы диапазонов (кВт·ч в месяц)
RANGES = {
    1: (0, 1100),
    2: (1101, 1700),
    3: (1701, float('inf'))
}

# Сезонные коэффициенты (зимой больше льготный лимит при отоплении)
HEATING_MONTHS = [10, 11, 12, 1, 2, 3, 4]  # октябрь-апрель
HEATING_RANGE_1_LIMIT = 3900  # Для домов с электроотоплением зимой


def load_previous_reading():
    """Загружает последние показания"""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_reading(data):
    """Сохраняет показания"""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_user_profile():
    """Определяем категорию потребителя"""
    print("\nВыберите вашу категорию:")
    print("1 - Городское население")
    print("2 - Городское население + электроплита (нужны документы в ТНС)")
    print("3 - Сельское население")
    print("4 - Сельское население + электроотопление")

    choice = input("Ваш выбор (1/2/3/4): ")

    profiles = {
        "1": "city",
        "2": "city_electric_stove",
        "3": "country",
        "4": "country_electric_heating"
    }

    return profiles.get(choice, "city")


def calculate_cost(consumption, profile, current_month):
    """
    Рассчитывает стоимость по диапазонам

    consumption - расход за месяц в кВт·ч
    profile - категория потребителя
    current_month - месяц (1-12) для учёта отопительного сезона
    """
    tariffs = TARIFFS_2025[profile]

    # Для домов с электроотоплением зимой — увеличенный лимит первого диапазона
    if profile == "country_electric_heating" and current_month in HEATING_MONTHS:
        range1_limit = HEATING_RANGE_1_LIMIT
    else:
        range1_limit = RANGES[1][1]

    remaining = consumption
    total_cost = 0
    details = {}

    # 1 диапазон
    range1_consumption = min(remaining, range1_limit)
    if range1_consumption > 0:
        cost = range1_consumption * tariffs[1]
        total_cost += cost
        details["range1"] = {"kwh": range1_consumption, "tariff": tariffs[1], "cost": cost}
        remaining -= range1_consumption

    # 2 диапазон
    if remaining > 0:
        range2_limit = RANGES[2][1] - RANGES[2][0] + 1
        range2_consumption = min(remaining, range2_limit)
        if range2_consumption > 0:
            cost = range2_consumption * tariffs[2]
            total_cost += cost
            details["range2"] = {"kwh": range2_consumption, "tariff": tariffs[2], "cost": cost}
            remaining -= range2_consumption

    # 3 диапазон (всё остальное)
    if remaining > 0:
        cost = remaining * tariffs[3]
        total_cost += cost
        details["range3"] = {"kwh": remaining, "tariff": tariffs[3], "cost": cost}

    return total_cost, details


def get_month_season():
    """Определяем текущий месяц для учёта отопительного сезона"""
    now = datetime.now()
    month = now.month
    return month


def main():
    print("=" * 50)
    print("    Учёт электроэнергии ТНС энерго Кубань")
    print("=" * 50)

    # Загружаем прошлые показания
    saved = load_previous_reading()

    # Определяем профиль пользователя
    profile = get_user_profile()

    # Вводим текущие показания
    print("\nВведите текущие показания счётчика (кВт·ч):")
    current_reading = float(input("Показания: "))

    if saved is None or "last_reading" not in saved:
        # Первый запуск — просто сохраняем
        print("\n[Первый запуск] Сохраняю показания как начальные.")
        save_reading({
            "last_reading": current_reading,
            "last_date": datetime.now().isoformat(),
            "profile": profile
        })
        print("Данные сохранены. В следующий раз будет рассчитано потребление.")
        return

    # Расчёт потребления
    last_reading = saved["last_reading"]
    consumption = current_reading - last_reading

    if consumption < 0:
        print("\nОШИБКА: Текущие показания меньше предыдущих!")
        print(f"Было: {last_reading}, Стало: {current_reading}")
        return

    if consumption == 0:
        print("\nПотребление за месяц: 0 кВт·ч")
        return

    # Определяем месяц для расчёта (используем текущий)
    current_month = get_month_season()

    # Рассчитываем стоимость
    total_cost, details = calculate_cost(consumption, profile, current_month)

    # Выводим результат
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТ РАСЧЁТА")
    print("=" * 50)
    print(f"Предыдущие показания: {last_reading:,.0f} кВт·ч")
    print(f"Текущие показания:    {current_reading:,.0f} кВт·ч")
    print(f"Расход за месяц:      {consumption:,.0f} кВт·ч")
    print("-" * 50)

    # Детали по диапазонам
    profile_names = {
        "city": "Город",
        "city_electric_stove": "Город + электроплита",
        "country": "Село",
        "country_electric_heating": "Село + электроотопление"
    }
    print(f"Категория: {profile_names.get(profile, profile)}")

    if profile == "country_electric_heating" and current_month in HEATING_MONTHS:
        print("⚠ Режим: отопительный сезон (льготный лимит 3900 кВт·ч)")

    print("\nРасход по диапазонам:")
    for rng in ["range1", "range2", "range3"]:
        if rng in details:
            d = details[rng]
            range_names = {"range1": "1-й (до 1100)", "range2": "2-й (1101-1700)", "range3": "3-й (свыше 1700)"}
            print(f"  {range_names[rng]}: {d['kwh']:,.0f} кВт·ч × {d['tariff']:.2f} руб = {d['cost']:,.2f} руб")

    print("-" * 50)
    print(f"ИТОГО К ОПЛАТЕ: {total_cost:,.2f} руб")
    print("=" * 50)

    # Подсказка про льготы
    print("\n💡 Важно:")
    print("• Тарифы зависят от диапазонов — чем больше расход, тем выше цена")
    print("• При наличии электроплиты/отопления нужны подтверждающие документы в ТНС")
    print("• Льготы (многодетные, участники СВО) — весь расход по тарифу 1-го диапазона")

    # Сохраняем новые показания
    save_reading({
        "last_reading": current_reading,
        "last_date": datetime.now().isoformat(),
        "profile": profile
    })
    print("\n✓ Показания сохранены для следующего месяца.")


if __name__ == "__main__":
    main()