# tns_electricity/apps.py

from django.apps import AppConfig

class TnsElectricityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tns_electricity'
    verbose_name = 'Учёт электроэнергии ТНС'