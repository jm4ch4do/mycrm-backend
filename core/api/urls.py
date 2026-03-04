from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.account import AccountViewSet
from core.api.views.contact import ContactViewSet
from core.api.views.user import CurrentUserView

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"contacts", ContactViewSet, basename="contact")

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("", include(router.urls)),
]
