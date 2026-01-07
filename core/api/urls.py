from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.account import AccountViewSet

router = DefaultRouter()
router.register(r'', AccountViewSet, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]
