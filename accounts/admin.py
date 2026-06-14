from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import AccessibilityPreferences, Role, User


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

    # ----- self-demotion guard -----
    def get_readonly_fields(self, request, obj=None):
        """Lock the ``role`` field whenever an admin edits themselves.

        Defence in depth — also blocked in ``save_model`` and in the custom
        change_role view, but locking the field prevents the form from even
        offering the option."""
        readonly = list(super().get_readonly_fields(request, obj))
        editing_self_as_admin = (
            obj is not None and obj.pk == request.user.pk and request.user.role == Role.ADMIN
        )
        if editing_self_as_admin and "role" not in readonly:
            readonly.append("role")
        return readonly

    def save_model(self, request, obj, form, change):
        """Reject any attempt to lower the current admin's own role."""
        if (
            change
            and obj.pk == request.user.pk
            and request.user.role == Role.ADMIN
            and obj.role != Role.ADMIN
        ):
            # Restore the field to its DB value and warn — do not save the demotion.
            obj.role = Role.ADMIN
            messages.error(
                request,
                "You can't lower your own admin role. Ask another admin to do it.",
            )
        super().save_model(request, obj, form, change)


@admin.register(AccessibilityPreferences)
class AccessibilityPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "high_contrast_mode",
        "dyslexia_friendly_font",
        "reduced_motion",
        "large_touch_targets",
    )
    list_filter = (
        "high_contrast_mode",
        "dyslexia_friendly_font",
        "reduced_motion",
        "large_touch_targets",
        "simplified_layout",
        "font_size",
        "colorblind_mode",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Visual Accessibility",
            {
                "fields": (
                    "high_contrast_mode",
                    "dyslexia_friendly_font",
                    "font_size",
                    "colorblind_mode",
                )
            },
        ),
        (
            "Motor Accessibility",
            {
                "fields": (
                    "reduced_motion",
                    "large_touch_targets",
                    "keyboard_navigation_hints",
                )
            },
        ),
        (
            "Cognitive Accessibility",
            {"fields": ("simplified_layout", "reading_guide")},
        ),
        ("Audio & Content", {"fields": ("captions", "screen_reader_mode")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
