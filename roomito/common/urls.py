from django.urls import path
from .views import (
    MyEventUpdateView,
    MyReservationsListView, 
    UnifiedLoginView, 
    MyReservationDetailView, 
    MyReservationDeleteView,
    MyEventDetailView,
    MyEventsListView,
    MyReservationUpdateView
)

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified-login'),
    path("myreservations/", MyReservationsListView.as_view(), name="my-reservations"),
    path("myreservations/<int:reservation_id>/", MyReservationDetailView.as_view(), name="my-reservation"),
    path("myreservations/<int:reservation_id>/delete", MyReservationDeleteView.as_view(), name="my-reservation-delete"),
    path("myevents/", MyEventsListView.as_view(), name="my-events"),
    path("myevents/<int:event_id>/", MyEventDetailView.as_view(), name="my-event"),
    path("myreservations/<int:reservation_id>/update", MyReservationUpdateView.as_view(), name="my-reservation-update"),
    path("myevents/<int:event_id>/update/", MyEventUpdateView.as_view(), name="my-event-update"),
]