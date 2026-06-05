"""External service for scanning and flagging overdue activities."""

from django.utils import timezone

from core.models import Activity, ActivityStatus


def scan_overdue_activities():
    """
    Periodic task to scan and flag overdue activities.

    Updates Activity.is_overdue=True for activities that:
    - Are not soft-deleted (is_invalid=False)
    - Have status in [PLANNED, IN_PROGRESS]
    - Have due_at in the past

    Clears is_overdue=False for activities that no longer meet criteria.

    Returns:
        dict: Summary with counts of flagged and cleared activities.
    """
    now = timezone.now()

    # Find activities that should be flagged as overdue
    overdue_query = Activity.objects.filter(
        is_invalid=False,
        status__in=[ActivityStatus.PLANNED, ActivityStatus.IN_PROGRESS],
        due_at__lt=now,
        is_overdue=False,  # Only update those not already flagged
    )

    # Flag them
    flagged_count = overdue_query.update(is_overdue=True)

    # Find activities that should no longer be overdue
    # (due_at is None, or due_at is in the future, or status changed to completed/canceled)
    clear_query = Activity.objects.filter(
        is_overdue=True,
    ).exclude(
        is_invalid=False,
        status__in=[ActivityStatus.PLANNED, ActivityStatus.IN_PROGRESS],
        due_at__lt=now,
    )

    # Clear the flag
    cleared_count = clear_query.update(is_overdue=False)

    return {
        "flagged": flagged_count,
        "cleared": cleared_count,
        "timestamp": now.isoformat(),
    }
