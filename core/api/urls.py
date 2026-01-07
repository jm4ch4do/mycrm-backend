from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.account import AccountViewSet
from core.api.views.user import CurrentUserView

router = DefaultRouter()
router.register(r'', AccountViewSet, basename='account')

urlpatterns = [
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('', include(router.urls)),
]
