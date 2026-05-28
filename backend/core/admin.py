from django.contrib import admin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    search_fields = ['name', 'slug']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'role', 'tenant', 'is_active']
    list_filter = ['role', 'tenant', 'is_active']
    search_fields = ['email', 'username']
