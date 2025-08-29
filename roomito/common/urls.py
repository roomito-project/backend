from django.urls import path
from .views import MyReservationsListView, UnifiedLoginView, MyReservationDetailView

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified-login'),
    path("myreservations/", MyReservationsListView.as_view(), name="my-reservations"),
    path("myreservations/<int:reservation_id>/", MyReservationDetailView.as_view(), name="my-reservation"),
]