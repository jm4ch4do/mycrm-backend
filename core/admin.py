from django.contrib import admin

from .models import Account, Contact


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for Account model."""

    list_display = (
        "name",
        "account_number",
        "status",
        "type",
        "owner_user",
        "created_at",
    )
    list_filter = ("status", "type", "is_invalid", "created_at")
    search_fields = ("name", "account_number", "website")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("id", "name", "account_number", "status", "type")}),
        (
            "Business Info",
            {
                "fields": (
                    "industry",
                    "company_size",
                    "annual_revenue",
                    "website",
                    "description",
                )
            },
        ),
        ("Ownership", {"fields": ("owner_user", "created_by", "updated_by")}),
        (
            "Addresses",
            {
                "classes": ("collapse",),
                "fields": (
                    ("billing_street", "billing_city", "billing_state"),
                    ("billing_country", "billing_postal_code"),
                    ("shipping_street", "shipping_city", "shipping_state"),
                    ("shipping_country", "shipping_postal_code"),
                ),
            },
        ),
        ("Audit", {"fields": ("is_invalid", "created_at", "updated_at")}),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin interface for Contact model."""

    list_display = (
        "first_name",
        "last_name",
        "email",
        "account",
        "role",
        "owner_user",
        "created_at",
    )
    list_filter = ("role", "seniority", "is_invalid", "created_at")
    search_fields = ("first_name", "last_name", "email", "job_title")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            "Identity",
            {"fields": ("id", "first_name", "last_name", "email", "phone", "mobile")},
        ),
        (
            "Professional Info",
            {"fields": ("job_title", "department", "role", "seniority")},
        ),
        (
            "Association",
            {"fields": ("account", "owner_user", "primary_contact")},
        ),
        (
            "Communication Preferences",
            {
                "classes": ("collapse",),
                "fields": ("preferred_channel", "opt_in_email", "opt_in_sms"),
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "is_invalid",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                )
            },
        ),
    )
