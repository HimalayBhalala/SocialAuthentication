from django.contrib import admin
from .models import User, Token

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'provider')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'provider')

admin.site.register(User, UserAdmin)


class TokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_token', 'refresh_token', 'created_at', 'expires_at')
    search_fields = ('user__email', 'access_token', 'refresh_token')
    list_filter = ('created_at', 'expires_at')

admin.site.register(Token, TokenAdmin)