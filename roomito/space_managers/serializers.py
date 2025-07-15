from rest_framework import serializers
from .models import SpaceManager, Space, Reservation, Schedule, Event

class SpaceManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceManager
        fields = '__all__'

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'