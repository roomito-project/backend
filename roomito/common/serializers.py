from rest_framework import serializers
from space_managers.serializers import SpaceSerializer
from space_managers.models import Event, Reservation


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    

class UnifiedLoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['staff', 'student', 'space_manager'])
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        if not data.get('role') or not data.get('username') or not data.get('password'):
            raise serializers.ValidationError("All fields are required.")
        return data


class MyReservationListSerializer(serializers.ModelSerializer):
    space_name  = serializers.CharField(source='space.name', read_only=True)
    date        = serializers.DateField(source='schedule.date', read_only=True)
    start_time  = serializers.SerializerMethodField()
    end_time    = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    phone_number   = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'space_name',
            'date',
            'start_time',
            'end_time',
            'status_display',
            'manager_comment',
            'reservation_type',
            'description',
            'phone_number',
        ]

    def _parse_time_range(self, time_range_str, pick='start'):
        if not time_range_str or '-' not in time_range_str:
            return None
        parts = time_range_str.split('-')
        val = parts[0] if pick == 'start' else parts[-1]
        return f"{val}:00" if len(val) == 5 else val

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='end')


class MyReservationDetailSerializer(serializers.ModelSerializer):
    space           = SpaceSerializer(read_only=True) 
    date            = serializers.DateField(source='schedule.date', read_only=True)
    hour_codes      = serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'reservation_type',
            'description',
            'status_display',    
            'phone_number',
            'manager_comment',
            'space',
            'date',
            'hour_codes',
            'hosting_association',
            'hosting_organizations',
            'responsible_organizer',
            'position',
        ]

    def get_hour_codes(self, obj):
        sch = getattr(obj, 'schedule', None)
        if not sch or not sch.start_hour_code or not sch.end_hour_code:
            return []
        start = sch.start_hour_code.code
        end   = sch.end_hour_code.code
        if start is None or end is None or end < start:
            return []
        return list(range(start, end + 1))


class MyEventListSerializer(serializers.ModelSerializer):
    space_name  = serializers.CharField(source='space.name', read_only=True)
    date        = serializers.DateField(source='schedule.date', read_only=True)
    start_time  = serializers.SerializerMethodField()
    end_time    = serializers.SerializerMethodField()
    poster      = serializers.ImageField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'description',
            'poster', 'space_name', 'date', 'start_time', 'end_time'
        ]

    def _parse_time_range(self, time_range_str, pick='start'):
        if not time_range_str or '-' not in time_range_str:
            return None
        part = time_range_str.split('-')[0 if pick=='start' else -1]
        return f"{part}:00" if len(part) == 5 else part

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'end')


class EventDetailSerializer(serializers.ModelSerializer):
    space       = SpaceSerializer(read_only=True)              
    date        = serializers.DateField(source='schedule.date', read_only=True)
    start_time  = serializers.SerializerMethodField()
    end_time    = serializers.SerializerMethodField()
    organizer_display = serializers.CharField(source='get_organizer_display', read_only=True)
    poster      = serializers.ImageField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'description',
            'poster', 'organizer', 'organizer_display',
            'space', 'date', 'start_time', 'end_time'
        ]

    def _parse_time_range(self, time_range_str, pick='start'):
        if not time_range_str or '-' not in time_range_str:
            return None
        part = time_range_str.split('-')[0 if pick=='start' else -1]
        return f"{part}:00" if len(part) == 5 else part

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'end')
