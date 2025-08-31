from django.apps import AppConfig

class AllBookingsAndRegistrationsConfig(AppConfig):  # Changed class name
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'all_bookings_and_registrations'  # Changed app name