from django.contrib import admin

# Register your models here.
from accounts.models import AuthRequest, User


@admin.register(AuthRequest)
class AuthRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request_status',
        'request_type',
        'created_at',
    )
    list_filter = (
        'request_type',
    )
    search_fields = (
        'email',
    )
    date_hierarchy = 'created_at'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
    )
    search_fields = (
        'username',
        'email',
    )
