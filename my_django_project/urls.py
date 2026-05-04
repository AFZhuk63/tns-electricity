# my_django_project/urls.py

from django.contrib import admin
from django.urls import path, include
from tns_electricity.admin import admin_site

urlpatterns = [
    path('admin/', admin.site.urls),           # стандартная админка
    path('custom-admin/', admin_site.urls),    # ваша кастомная админка с кнопками
    path('', include('tns_electricity.urls')),
]