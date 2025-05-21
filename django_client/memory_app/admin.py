from django.contrib import admin
from .models import OAuthToken, Memory

@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'is_expired', 'created_at', 'updated_at')
    list_filter = ('is_expired',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'permission', 'expiration_date', 'is_expired', 'created_at', 'updated_at')
    list_filter = ('permission', 'is_expired')
    search_fields = ('user__username', 'user__email', 'text')
    readonly_fields = ('id', 'created_at', 'updated_at')
