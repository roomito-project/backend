from django.urls import path
from .views import (
    SpaceManagerLoginView,
    SpaceManagerProfileView,
    SpaceManagerPasswordChangeView,
    SpaceListView,
    EventListView,
    EventDetailView,
)

urlpatterns = [
    path("spacemanager/login/", SpaceManagerLoginView.as_view(), name="space-manager-login"),
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spacemanager/change-password/", SpaceManagerPasswordChangeView.as_view(), name="space-manager-change-password"),
    path("spaces/list/", SpaceListView.as_view(), name="spaces-list"),
    path("events/list/", EventListView.as_view(), name="events-list"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event-details")
]
