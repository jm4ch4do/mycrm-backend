"""Entity default handlers for BDD tests."""

from steps.domain.defaults.account import AccountDefaults
from steps.domain.defaults.activity import ActivityDefaults
from steps.domain.defaults.base import BaseEntityDefaults
from steps.domain.defaults.call import CallDefaults
from steps.domain.defaults.contact import ContactDefaults
from steps.domain.defaults.deal import DealDefaults
from steps.domain.defaults.event import EventDefaults
from steps.domain.defaults.meeting import MeetingDefaults
from steps.domain.defaults.note import NoteDefaults
from steps.domain.defaults.task import TaskDefaults

__all__ = [
    "BaseEntityDefaults",
    "AccountDefaults",
    "ActivityDefaults",
    "CallDefaults",
    "ContactDefaults",
    "DealDefaults",
    "EventDefaults",
    "MeetingDefaults",
    "NoteDefaults",
    "TaskDefaults",
]
