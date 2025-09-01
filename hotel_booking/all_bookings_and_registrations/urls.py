# all_bookings_and_registrations/urls.py

from django.urls import path
from . import views

app_name = 'all_bookings_and_registrations'

urlpatterns = [
    path('', views.home_page, name='home'),
    path('verify-qr/', views.verify_qr_code, name='verify_qr'),
]