from rest_framework import viewsets
from .models import SpaceManager, Space, Reservation, Schedule, Event
from .serializers import SpaceManagerSerializer, SpaceSerializer, ReservationSerializer, ScheduleSerializer, EventSerializer

class SpaceManagerViewSet(viewsets.ModelViewSet):
    queryset = SpaceManager.objects.all()
    serializer_class = SpaceManagerSerializer

class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all()
    serializer_class = SpaceSerializer

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer