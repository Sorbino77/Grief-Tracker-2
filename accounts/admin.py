from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active", "last_login")
    list_filter = ("role", "is_staff", "is_active", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = (*(UserAdmin.fieldsets or ()), ("Role", {"fields": ("role",)}))
    add_fieldsets = (
        *(UserAdmin.add_fieldsets or ()),
        ("Role", {"fields": ("email", "role")}),
    )
