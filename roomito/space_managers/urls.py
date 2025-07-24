from django.urls import path
from .views import (
    SpaceManagerLoginView,
    SpaceManagerProfileView,
    SpaceManagerPasswordChangeView
)

urlpatterns = [
    path("spacemanager/login/", SpaceManagerLoginView.as_view(), name="space-manager-login"),
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spacemanager/change-password/", SpaceManagerPasswordChangeView.as_view(), name="space-manager-change-password"),
]
