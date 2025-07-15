from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpaceManagerViewSet, SpaceViewSet, ReservationViewSet, ScheduleViewSet, EventViewSet

router = DefaultRouter()
router.register(r'space-managers', SpaceManagerViewSet)
router.register(r'spaces', SpaceViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]