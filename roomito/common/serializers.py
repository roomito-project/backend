from rest_framework import serializers
from space_managers.models import Reservation


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
    space_name      = serializers.CharField(source='space.name', read_only=True)
    date            = serializers.DateField(source='schedule.date', read_only=True)
    start_time      = serializers.SerializerMethodField()
    end_time        = serializers.SerializerMethodField()
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
            'space_name',
            'date',
            'start_time',
            'end_time',
            'hosting_association',
            'hosting_organizations',
            'responsible_organizer',
            'position',
        ]

    def _parse_time_range(self, time_range_str, pick='start'):
        if not time_range_str or '-' not in time_range_str:
            return None
        parts = time_range_str.split('-')
        val = parts[0] if pick == 'start' else parts[-1]
        return f"{val}:00" if len(val) == 5 else val

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), 'end')
