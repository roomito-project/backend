from django.urls import path
from .views import (
    SpaceManagerProfileView,
    SpaceListView,
    EventListView,
    EventDetailView,
    SpaceManagerProfileUpdateView,
    SpaceUpdateFeatureView,
    SpaceFeatureView,
    ReservationCreateView,
    ManagerReservationListView,
    SpaceDetailView,
    ManagerSpaceDetailView,
    ManagerSpaceListView,
    ManagerSpaceCreateView,
    ManagerSpaceUpdateView
)

urlpatterns = [
    path("spacemanager/profile/", SpaceManagerProfileView.as_view(), name="space-manager-profile"),
    path("spaces/list/", SpaceListView.as_view(), name="spaces-list"),
    path("events/list/", EventListView.as_view(), name="events-list"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event-details"),
    path("spacemanager/updateProfile/", SpaceManagerProfileUpdateView.as_view(), name="space-manager-profile-update"),
    path("<int:space_id>/features", SpaceFeatureView.as_view(), name="space-feature-update"),
    # path("<int:space_id>/updateFeatures", SpaceUpdateFeatureView.as_view(), name="space-feature-update"),
    path('<int:space_id>/reserve/', ReservationCreateView.as_view(), name='space_reserve'),
    path('spacemanager/reservations/', ManagerReservationListView.as_view(), name='manager_reservations'),
    path('space/<int:space_id>/', SpaceDetailView.as_view(), name="space-details"),
    path("spacemanager/spaces/", ManagerSpaceListView.as_view(), name="manager-space-list"),
    path("spacemanager/<int:space_id>/", ManagerSpaceDetailView.as_view(), name="manager-space-detail"),
    path('spacemanager/createSpace/', ManagerSpaceCreateView.as_view(), name="create-space"),
    path('spacemanager/<int:space_id>/updateSpace/', ManagerSpaceUpdateView.as_view(), name="update-space"),
]
