from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for Account model."""
    list_display = ("name", "account_number", "status", "type", "owner_user", "created_at")
    list_filter = ("status", "type", "is_invalid", "created_at")
    search_fields = ("name", "account_number", "website")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("id", "name", "account_number", "status", "type")}),
        ("Business Info", {"fields": ("industry", "company_size", "annual_revenue", "website", "description")}),
        ("Ownership", {"fields": ("owner_user", "created_by", "updated_by")}),
        ("Addresses", {
            "classes": ("collapse",),
            "fields": (
                ("billing_street", "billing_city", "billing_state"),
                ("billing_country", "billing_postal_code"),
                ("shipping_street", "shipping_city", "shipping_state"),
                ("shipping_country", "shipping_postal_code"),
            ),
        }),
        ("Audit", {"fields": ("is_invalid", "created_at", "updated_at")}),
    )
