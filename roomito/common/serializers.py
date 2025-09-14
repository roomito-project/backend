from rest_framework import serializers
from space_managers.serializers import SpaceSerializer
from space_managers.models import Event, HourSlot, Reservation, Schedule, Space
from django.core.exceptions import ValidationError as DjangoValidationError


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
    organizer   = serializers.SerializerMethodField()
    contact_info       = serializers.CharField(read_only=True, allow_null=True)
    registration_link  = serializers.CharField(read_only=True, allow_null=True)
    poster      = serializers.ImageField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'description',
            'poster', 'organizer', 'contact_info', 'registration_link', 
            'space', 'date', 'start_time', 'end_time'
        ]

    def get_organizer(self, obj):
        if obj.organizer == 'student' and obj.student_organizer and getattr(obj.student_organizer, 'user', None):
            u = obj.student_organizer.user
            return {
                "type": "student",
                "id": obj.student_organizer.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
            }
        if obj.organizer == 'staff' and obj.staff_organizer:
            s = obj.staff_organizer
            return {
                "type": "staff",
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.email,
            }
        return None

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


class ScheduleUpdateSerializer(serializers.Serializer):
    hour_codes = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=HourSlot.objects.all()),
        required=False, min_length=1, max_length=12
    )
    date = serializers.DateField(required=False)

    def validate(self, data):
        if 'hour_codes' in data:
            hour_objs = data['hour_codes']
            if not hour_objs:
                raise serializers.ValidationError({"hour_codes": ["At least one hour code is required."]})

            codes = [hc.code for hc in hour_objs]

            sorted_pairs = sorted(zip(codes, hour_objs), key=lambda x: x[0])
            codes, hour_objs = zip(*sorted_pairs)  
            data['hour_codes'] = list(hour_objs)

            if len(codes) != len(set(codes)):
                raise serializers.ValidationError({"hour_codes": ["Duplicate hour codes are not allowed."]})

            if (max(codes) - min(codes) + 1) != len(codes):
                raise serializers.ValidationError({"hour_codes": ["Hour codes must be consecutive."]})

        return data


class ReservationUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, min_length=11, max_length=11)
    schedule = ScheduleUpdateSerializer(required=False)

    class Meta:
        model = Reservation
        fields = [
            'reservation_type', 'phone_number', 'description',
            'hosting_association', 'hosting_organizations',
            'responsible_organizer', 'position', 'schedule',
        ]

    def validate_phone_number(self, v):
        if v and not v.isdigit():
            raise serializers.ValidationError("Phone number must be exactly 11 digits.")
        return v

    def update(self, instance: Reservation, validated_data):
        for f in ('reservation_type', 'phone_number', 'description',
                  'hosting_association', 'hosting_organizations',
                  'responsible_organizer', 'position'):
            if f in validated_data:
                setattr(instance, f, validated_data[f])

        sched_data = validated_data.get('schedule')
        if sched_data:
            sched: Schedule = instance.schedule
            if not sched:
                raise serializers.ValidationError({"schedule": ["This reservation has no schedule to update."]})

            if 'date' in sched_data:
                sched.date = sched_data['date']

            if 'hour_codes' in sched_data:
                hour_objs = sched_data['hour_codes'] 
                start_obj = min(hour_objs, key=lambda x: x.code)
                end_obj   = max(hour_objs, key=lambda x: x.code)
                sched.start_hour_code = start_obj
                sched.end_hour_code   = end_obj

            sched.full_clean()
            sched.save()

        instance.save()
        return instance



class MyEventUpdateSerializer(serializers.ModelSerializer):
    poster = serializers.ImageField(required=False, allow_null=True)
    removeImage = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = Event
        fields = ['title', 'poster', 'contact_info', 'registration_link', 'description', 'removeImage']
        extra_kwargs = {
            'title': {'required': False, 'max_length': 200},
            'contact_info': {'required': False, 'allow_blank': True, 'max_length': 200},
            'registration_link': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True, 'max_length': 500},
        }
