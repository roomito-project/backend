from django.urls import path
from .views import (
    SpaceManagerLoginView,
    SpaceManagerProfileView,
    SpaceListView,
    EventListView,
    EventDetailView,
    SpaceManagerProfileUpdateView
)

urlpatterns = [
    path("spacemanager/login/", SpaceManagerLoginView.as_view(), name="space-manager-login"),
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spaces/list/", SpaceListView.as_view(), name="spaces-list"),
    path("events/list/", EventListView.as_view(), name="events-list"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event-details"),
    path("spacemanager/updateProfile/", SpaceManagerProfileUpdateView.as_view(), name="space-manager-update-profile")
]
