# ТНС энерго Кубань - Учёт электроэнергии

Веб-приложение для учёта и расчёта стоимости электроэнергии по двухтарифному счётчику для ТНС энерго Кубань.

## Функционал

- ✅ Учёт начальных показаний счётчика
- ✅ Ввод текущих показаний с указанием даты
- ✅ Автоматический расчёт стоимости по диапазонным тарифам (день/ночь)
- ✅ Распределение расхода по месяцам при длительном периоде (>45 дней)
- ✅ История платежей с визуальным статусом оплаты
- ✅ Добавление платежей по счетам
- ✅ Редактирование показаний с автоматическим перерасчётом
- ✅ Экспорт квитанций в PDF
- ✅ Админ-панель Django

## Тарифы

### ДЕНЬ (7:00-23:00)
- 1 диапазон (до 1100 kWh): 5.88 ₽
- 2 диапазон (1101-1700 kWh): 7.99 ₽
- 3 диапазон (>1700 kWh): 16.70 ₽

### НОЧЬ (23:00-7:00)
- 1 диапазон (до 1100 kWh): 3.16 ₽
- 2 диапазон (1101-1700 kWh): 4.30 ₽
- 3 диапазон (>1700 kWh): 8.93 ₽

## Установка и запуск

### Требования
- Python 3.8+
- Django 4.2+
- ReportLab 4.0+

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/tns-electricity.git
cd tns-electricity
```
Создайте виртуальное окружение:

bash
python -m venv myenv
myenv\Scripts\activate  # Windows
source myenv/bin/activate  # Linux/Mac
Установите зависимости:

bash
pip install -r requirements.txt
Выполните миграции:

bash
python manage.py makemigrations
python manage.py migrate
Создайте суперпользователя:

bash
python manage.py createsuperuser
Запустите сервер:

bash
python manage.py runserver
Откройте браузер: http://127.0.0.1:8000

Структура проекта
text
my_django_project/
├── manage.py
├── requirements.txt
├── my_django_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tns_electricity/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│   ├── admin.py
│   ├── static/
│   └── templates/
└── media/
API Endpoints
GET /api/last-reading/ - последние показания

GET /api/check-initial-readings/ - проверка начальных показаний

POST /api/save-initial-readings/ - сохранение начальных показаний

POST /api/calculate/ - расчёт стоимости

POST /api/recalculate/ - перерасчёт при редактировании

GET /api/history/ - история платежей

POST /api/add-payment/ - добавление платежа

POST /api/export-pdf/ - экспорт в PDF

Технологии
Django 4.2

SQLite3

ReportLab (PDF generation)

HTML5/CSS3

Vanilla JavaScript

Лицензия
MIT

Автор
Ваше Имя

Статус проекта
✅ В разработке, работает стабильно

text

### 3. Создайте `requirements.txt` (если ещё нет):

```txt
Django==4.2.7
reportlab==4.0.4
Pillow==10.1.0
```
### Инициализируйте Git репозиторий:
```bash
cd C:\Users\Iron Mask\my_django_project
```

# Инициализируем Git
git init

# Добавляем файлы
git add .

# Проверяем статус
git status

# Создаём первый коммит
git commit -m "Initial commit: ТНС энерго Кубань учёт электроэнергии"
### 5. Создайте репозиторий на GitHub:
Зайдите на GitHub

Нажмите на + в правом верхнем углу → New repository

Название: tns-electricity (или любое другое)

Описание: Веб-приложение для учёта электроэнергии ТНС энерго Кубань

Выберите Public или Private

НЕ отмечайте "Add a README file" (уже создали)

Нажмите Create repository

### 6. Свяжите локальный репозиторий с GitHub:
bash
# Добавляем удалённый репозиторий (ЗАМЕНИТЕ username на ваш)
git remote add origin https://github.com/YOUR_USERNAME/tns-electricity.git

# Пушим код
git branch -M main
git push -u origin main
### 7. Если хотите использовать SSH вместо HTTPS:
```bash
git remote add origin git@github.com:YOUR_USERNAME/tns-electricity.git
git branch -M main
git push -u origin main
```
### 8. После успешного пуша, проверьте:
Откройте https://github.com/YOUR_USERNAME/tns-electricity - там должен быть ваш код.

Дополнительные файлы (опционально):
Создайте LICENSE файл (MIT License):
bash
# Создайте файл LICENSE
echo "# MIT License" > LICENSE
Или используйте веб-интерфейс GitHub для добавления лицензии.

Создайте .gitattributes для правильной обработки переносов строк:
gitattributes
# Auto detect text files and perform LF normalization
* text=auto

# Python
*.py text diff=python
*.pyc binary

# Django
*.html text diff=html
*.css text diff=css
*.js text diff=javascript

# Images
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary

# Documents
*.pdf binary
*.doc binary
*.docx binary
Полезные команды для Git:
bash
# Проверить статус
git status

# Посмотреть изменения
git diff

# Добавить все изменения
git add .

# Сделать коммит
git commit -m "Описание изменений"

# Отправить на GitHub
git push

# Получить обновления с GitHub
git pull

# Посмотреть историю коммитов
git log --oneline
Готово!
Теперь ваш проект на GitHub. Завтра сможем приступить к созданию Telegram бота для приёма показаний через мессенджер.

Важно: Не забудьте добавить в .gitignore чувствительные данные:

db.sqlite3 (база данных)

media/ (загруженные файлы)

__pycache__/

myenv/ (виртуальное окружение)

Если вы уже закоммитили эти файлы, можно их удалить:

bash
git rm -r --cached myenv/
git rm --cached db.sqlite3
git commit -m "Remove sensitive files"
git push
Дайте знать, когда создадите репозиторий, и завтра приступим к Telegram боту! 🚀

