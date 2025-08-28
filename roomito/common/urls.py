from django.urls import path
from .views import MyReservationsListView, UnifiedLoginView

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified-login'),
    path("myreservations/", MyReservationsListView.as_view(), name="my-reservations"),
]