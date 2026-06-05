from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Account,
    Activity,
    Call,
    Contact,
    Deal,
    DealContactAssoc,
    Meeting,
    MeetingContactAssoc,
    MeetingUserAssoc,
    Note,
    Task,
    UserProfile,
)


class UserProfileInline(admin.StackedInline):
    """Inline admin for CRM-specific user profile fields."""

    model = UserProfile
    fields = ("role",)
    extra = 0


user_model = get_user_model()
# django.contrib.auth registers User with its built-in UserAdmin at startup.
# Unregister it first so we can re-register with the extended version below.
admin.site.unregister(user_model)


@admin.register(user_model)
class UserAdmin(BaseUserAdmin):
    """Extended User admin with CRM profile inline."""

    inlines = [UserProfileInline]


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


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    """Admin interface for Deal model."""

    list_display = (
        "name",
        "account",
        "stage",
        "status",
        "amount",
        "currency",
        "owner_user",
        "created_at",
    )
    list_filter = (
        "stage",
        "status",
        "lead_source",
        "currency",
        "is_invalid",
        "created_at",
    )
    search_fields = ("name", "loss_reason")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("id", "name", "account")}),
        (
            "Financial",
            {"fields": ("amount", "currency", "expected_close_date", "probability")},
        ),
        ("Pipeline", {"fields": ("stage", "status", "loss_reason")}),
        ("Source", {"fields": ("lead_source",)}),
        ("Ownership", {"fields": ("owner_user", "created_by", "updated_by")}),
        (
            "Audit",
            {"fields": ("is_invalid", "closed_at", "created_at", "updated_at")},
        ),
    )


@admin.register(DealContactAssoc)
class DealContactAssocAdmin(admin.ModelAdmin):
    """Admin interface for DealContactAssoc model."""

    list_display = ("deal", "contact", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin interface for Activity model."""

    list_display = (
        "title",
        "type",
        "status",
        "owner_user",
        "account",
        "contact",
        "deal",
        "due_at",
        "created_at",
    )
    list_filter = ("type", "status", "is_invalid", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("id", "type", "title", "description")}),
        ("Context", {"fields": ("account", "contact", "deal")}),
        ("Lifecycle", {"fields": ("status", "due_at", "completed_at")}),
        ("Ownership", {"fields": ("owner_user", "created_by", "updated_by")}),
        ("Audit", {"fields": ("is_invalid", "created_at", "updated_at")}),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = (
        "activity",
        "state",
        "priority",
        "category",
        "estimated_duration_minutes",
    )
    list_filter = ("state", "priority", "category")
    search_fields = ("activity__title", "activity__description")
    readonly_fields = ("id",)
    fieldsets = (
        ("Identity", {"fields": ("id", "activity")}),
        (
            "Task Details",
            {
                "fields": (
                    "state",
                    "priority",
                    "category",
                    "estimated_duration_minutes",
                )
            },
        ),
    )


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Admin interface for Meeting model."""

    list_display = (
        "activity",
        "start_time",
        "end_time",
        "location",
        "outcome",
    )
    list_filter = ("outcome",)
    search_fields = ("activity__title", "location")
    readonly_fields = ("id",)
    fieldsets = (
        ("Identity", {"fields": ("id", "activity")}),
        (
            "Scheduling",
            {"fields": ("start_time", "end_time", "location", "meeting_url")},
        ),
        ("Outcome", {"fields": ("outcome", "summary")}),
    )


@admin.register(MeetingUserAssoc)
class MeetingUserAssocAdmin(admin.ModelAdmin):
    """Admin interface for MeetingUserAssoc model."""

    list_display = ("meeting", "user", "created_at")
    readonly_fields = ("created_at",)


@admin.register(MeetingContactAssoc)
class MeetingContactAssocAdmin(admin.ModelAdmin):
    """Admin interface for MeetingContactAssoc model."""

    list_display = ("meeting", "contact", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    """Admin interface for Call model."""

    list_display = (
        "activity",
        "direction",
        "outcome",
        "phone_number",
        "duration_seconds",
    )
    list_filter = ("direction", "outcome")
    search_fields = ("activity__title", "phone_number", "summary")
    readonly_fields = ("id",)
    fieldsets = (
        ("Identity", {"fields": ("id", "activity")}),
        (
            "Call Details",
            {"fields": ("direction", "phone_number", "duration_seconds")},
        ),
        ("Outcome", {"fields": ("outcome", "summary")}),
    )


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin interface for Note model."""

    list_display = (
        "get_title_or_body_preview",
        "author",
        "visibility",
        "is_pinned",
        "created_at",
    )
    list_filter = ("visibility", "is_pinned", "author", "is_invalid", "created_at")
    search_fields = ("title", "body")
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Identity", {"fields": ("id", "author")}),
        ("Content", {"fields": ("title", "body")}),
        ("Relationships", {"fields": ("account", "contact", "deal")}),
        ("Visibility", {"fields": ("visibility", "is_pinned")}),
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

    def get_title_or_body_preview(self, obj):
        """Display title if present, otherwise show first 50 chars of body."""
        if obj.title:
            return obj.title
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body

    get_title_or_body_preview.short_description = "Note"
