from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserMFA

class UserMFAInline(admin.StackedInline):
    model = UserMFA
    can_delete = False
    verbose_name_plural = 'MFA Settings'
    fields = ('is_mfa_enabled', 'secret_key')
    readonly_fields = ('secret_key',)

class UserAdmin(BaseUserAdmin):
    inlines = (UserMFAInline,)

# Re-register UserAdmin
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

@admin.register(UserMFA)
class UserMFAAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_mfa_enabled', 'has_secret_key', 'backup_tokens_count')
    list_filter = ('is_mfa_enabled',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('secret_key',)
    
    def has_secret_key(self, obj):
        return bool(obj.secret_key)
    has_secret_key.boolean = True
    has_secret_key.short_description = 'Has Secret Key'
    
    def backup_tokens_count(self, obj):
        return len(obj.backup_tokens) if obj.backup_tokens else 0
    backup_tokens_count.short_description = 'Backup Tokens'