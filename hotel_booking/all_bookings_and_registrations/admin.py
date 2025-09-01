# all_bookings_and_registrations/admin.py

from django.contrib import admin
from .models import QRSession

@admin.register(QRSession)
class QRSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['session_id']
    readonly_fields = ['session_id', 'secret_key', 'created_at']