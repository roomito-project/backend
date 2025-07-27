from django.urls import path
from .views import (
    SpaceManagerLoginView,
    SpaceManagerProfileView,
    SpaceManagerPasswordChangeView,
    SpaceListView,
    EventListView,
)

urlpatterns = [
    path("spacemanager/login/", SpaceManagerLoginView.as_view(), name="space-manager-login"),
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spacemanager/change-password/", SpaceManagerPasswordChangeView.as_view(), name="space-manager-change-password"),
    path("space/list/", SpaceListView.as_view(), name="space-list"),
    path("event/list/", EventListView.as_view(), name="event-list")
]
