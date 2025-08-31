from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('mfa/verify/', views.mfa_verify_view, name='mfa_verify'),
    path('mfa/setup/', views.mfa_setup_view, name='mfa_setup'),
    path('mfa/backup-tokens/', views.mfa_backup_tokens_view, name='mfa_backup_tokens'),
    path('mfa/disable/', views.mfa_disable_view, name='mfa_disable'),
]