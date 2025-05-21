from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import OAuthToken, Memory, UserProfile

# Inline admin class for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Extend the existing UserAdmin to include UserProfile
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_bio')
    
    def get_bio(self, obj):
        try:
            return obj.profile.bio[:50] + '...' if len(obj.profile.bio) > 50 else obj.profile.bio
        except UserProfile.DoesNotExist:
            return ""
    get_bio.short_description = 'Bio'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'is_expired', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'permission', 'expiration_date', 'is_expired', 'created_at', 'updated_at')
    list_filter = ('permission', 'expiration_date')
    search_fields = ('user__username', 'user__email', 'text')
    readonly_fields = ('id', 'created_at', 'updated_at')
