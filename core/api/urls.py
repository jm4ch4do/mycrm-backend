from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.account import AccountViewSet
from core.api.views.activity import ActivityViewSet
from core.api.views.call import CallViewSet
from core.api.views.contact import ContactViewSet
from core.api.views.deal import DealViewSet
from core.api.views.event import EventViewSet
from core.api.views.meeting import MeetingViewSet
from core.api.views.note import NoteViewSet
from core.api.views.task import TaskViewSet
from core.api.views.timeline import TimelineViewSet
from core.api.views.user import CurrentUserView, UserViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"activities", ActivityViewSet, basename="activity")
router.register(r"calls", CallViewSet, basename="call")
router.register(r"contacts", ContactViewSet, basename="contact")
router.register(r"deals", DealViewSet, basename="deal")
router.register(r"events", EventViewSet, basename="event")
router.register(r"meetings", MeetingViewSet, basename="meeting")
router.register(r"notes", NoteViewSet, basename="note")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"users", UserViewSet, basename="user")

# Nested timeline routes
account_timeline = TimelineViewSet.as_view({"get": "list"})
contact_timeline = TimelineViewSet.as_view({"get": "list"})
deal_timeline = TimelineViewSet.as_view({"get": "list"})

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path(
        "accounts/<uuid:account_pk>/timeline/",
        account_timeline,
        name="account-timeline",
    ),
    path(
        "contacts/<uuid:contact_pk>/timeline/",
        contact_timeline,
        name="contact-timeline",
    ),
    path(
        "deals/<uuid:deal_pk>/timeline/",
        deal_timeline,
        name="deal-timeline",
    ),
    path("", include(router.urls)),
]
