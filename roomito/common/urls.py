from django.urls import path
from .views import MyReservationsListView, UnifiedLoginView, MyReservationDetailView, MyReservationDeleteView,MyEventDetailView,MyEventsListView

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified-login'),
    path("myreservations/", MyReservationsListView.as_view(), name="my-reservations"),
    path("myreservations/<int:reservation_id>/", MyReservationDetailView.as_view(), name="my-reservation"),
    path("myreservations/<int:reservation_id>/delete", MyReservationDeleteView.as_view(), name="my-reservation-delete"),
    path("myevents/", MyEventsListView.as_view(), name="my-events"),
    path("myevents/<int:event_id>/", MyEventDetailView.as_view(), name="my-event"),
]