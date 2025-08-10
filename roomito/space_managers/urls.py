from django.urls import path
from .views import (
    SpaceManagerProfileView,
    SpaceListView,
    EventListView,
    EventDetailView,
    SpaceManagerProfileUpdateView,
    SpaceUpdateFeatureView,
    SpaceFeatureView,
)

urlpatterns = [
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spaces/list/", SpaceListView.as_view(), name="spaces-list"),
    path("events/list/", EventListView.as_view(), name="events-list"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event-details"),
    path("spacemanager/updateProfile/", SpaceManagerProfileUpdateView.as_view(), name="space-manager-profile-update"),
    path("space/<int:space_id>/features", SpaceFeatureView.as_view(), name="space-feature-update"),
    path("space/<int:space_id>/updateFeatures", SpaceUpdateFeatureView.as_view(), name="space-feature-update")
]
