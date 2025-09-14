from rest_framework import serializers
from django.contrib.auth.models import User
from .models import HourSlot, Space, SpaceImage, SpaceManager, Event, SpaceFeature, Schedule, Reservation
from staffs.models import Staff
from students.models import Student
from common.validators import validate_password_strength
from django.core.validators import MinValueValidator
from django.utils.datastructures import MultiValueDict


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    

class SpaceFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceFeature
        fields = ['id', 'name']


class SpaceUpdateFeatureSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['add_existing', 'add_new']) 
    feature_name = serializers.CharField() 

    def validate(self, data):
        space = self.context.get('space')
        if not space:
            raise serializers.ValidationError("Space not found.")
        return data        


class FeatureIdsSerializer(serializers.Serializer):
    feature_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        help_text="List of existing feature IDs to add to the space."
    )
    
    
class SpaceManagerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceManager
        fields = ['first_name', 'last_name', 'email', 'username']
        
        
class SpaceManagerProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=8)  
    
    def validate_password(self, value):
        validate_password_strength(value)
        return value
    
    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value
    
    # def validate_email(self, value):
    #     user = self.context['request'].user
    #     if User.objects.exclude(pk=user.pk).filter(email=value).exists():
    #         raise serializers.ValidationError("This email is already in use.")
    #     return value
    
    def validate(self, attrs):
        if 'new_password' in attrs:
            if 'current_password' not in attrs:
                raise serializers.ValidationError({"current_password": "Current password is required to change password."})
            user = self.context['request'].user
            if not user.check_password(attrs['current_password']):
                raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs
    
    def update(self, instance, validated_data):
        user = instance.user
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.username = validated_data.get("username", user.username)
        user.email = validated_data.get("email", user.email)
        if 'new_password' in validated_data:
            user.set_password(validated_data['new_password'])
        user.save()
        
        instance.first_name = user.first_name
        instance.last_name = user.last_name
        instance.email = user.email
        instance.username = validated_data.get("username", instance.username)
        instance.save()
        return instance        


class SpaceImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = SpaceImage
        fields = ["id", "url"]

    def get_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url
    
    
class SpaceListSerializer(serializers.ModelSerializer):
    space_manager = SpaceManagerProfileSerializer(read_only=True)
    first_image_url = serializers.SerializerMethodField()
    

    class Meta:
        model = Space
        fields = ['id', 'space_type', 'name', 'address', 'capacity', 'description',
                  'space_manager', 'phone_number', 'first_image_url']
        read_only_fields = ['id']

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than zero.")
        return value

    def get_first_image_url(self, obj):
        img = obj.first_image
        if not img:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(img.image.url) if request else img.image.url
    

class SpaceSerializer(serializers.ModelSerializer):
    space_manager = SpaceManagerProfileSerializer()
    features = SpaceFeatureSerializer(many=True)
    images = SpaceImageSerializer(many=True, read_only=True)
    phone_number = serializers.SerializerMethodField()   

    class Meta:
        model = Space
        fields = ['id', 'space_type', 'name', 'address', 'capacity', 'description', 'space_manager', 'phone_number', 'features', 'images']
        
    def get_phone_number(self, obj):
        return obj.phone_number if obj.phone_number not in ("", None) else None    


class StudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'student_id']


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['first_name', 'last_name', 'personnel_code', 'email']


class OrganizerOutSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['student', 'staff'])
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(allow_null=True, required=False)


def _parse_time_range(time_range_str: str, pick: str = "start"):
    if not time_range_str or "-" not in time_range_str:
        return None
    part = time_range_str.split("-")[0 if pick == "start" else -1]
    return f"{part}:00" if len(part) == 5 else part


class EventSerializer(serializers.ModelSerializer):
    space = SpaceSerializer(read_only=True)
    organizer = serializers.SerializerMethodField()  
    poster = serializers.ImageField(read_only=True, allow_null=True)
    date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.SerializerMethodField()
    end_time   = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'date', 'start_time', 'end_time',
            'space', 'poster', 'organizer',
            'contact_info', 'registration_link',
            'description',
        ]
        read_only_fields = fields

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

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return _parse_time_range(getattr(slot, 'time_range', None), 'start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return _parse_time_range(getattr(slot, 'time_range', None), 'end')


class EventDetailSerializer(serializers.ModelSerializer):
    organizer = serializers.SerializerMethodField()
    space = SpaceSerializer(read_only=True)
    poster_url = serializers.SerializerMethodField()
    date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.SerializerMethodField()
    end_time   = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type',
            'date', 'start_time', 'end_time',
            'space', 'poster_url',
            'organizer',
            'contact_info', 'registration_link',  
            'description',
        ]
        read_only_fields = fields

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

    def get_poster_url(self, obj):
        if obj.poster:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.poster.url) if request else obj.poster.url
        return None

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return _parse_time_range(getattr(slot, 'time_range', None), 'start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return _parse_time_range(getattr(slot, 'time_range', None), 'end')


class ScheduleAvailabilitySerializer(serializers.Serializer):
    hour_code = serializers.IntegerField(read_only=True)
    time_range = serializers.CharField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)


class ScheduleSerializer(serializers.ModelSerializer):
    hour_codes = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=HourSlot.objects.all()),
        min_length=1,
        max_length=12,
        error_messages={
            'min_length': 'At least one hour code is required.',
            'max_length': 'Maximum 12 hour codes allowed.'
        }
    )

    class Meta:
        model = Schedule
        fields = ['hour_codes', 'date']

    def validate(self, data):
        slots = [hc.code for hc in data['hour_codes']]
        if len(slots) != len(set(slots)):
            raise serializers.ValidationError({"hour_codes": ["Duplicate hour codes are not allowed."]})
        if slots != sorted(slots):
            raise serializers.ValidationError({"hour_codes": ["Hour codes must be in ascending order."]})
        if max(slots) - min(slots) + 1 != len(slots):
            raise serializers.ValidationError({"hour_codes": ["Hour codes must be consecutive."]})
        return data

    def to_representation(self, instance):
        start = instance.start_hour_code.code
        end = instance.end_hour_code.code
        return {
            "hour_codes": list(range(start, end + 1)),
            "date": instance.date
        }

    def create(self, validated_data):
        hour_codes = validated_data.pop('hour_codes')
        space = self.context.get('space')
        if not space:
            raise serializers.ValidationError({"space": ["Space context is missing."]})

        start_hour_code = min(hour_codes, key=lambda x: x.code)
        end_hour_code   = max(hour_codes, key=lambda x: x.code)

        schedule = Schedule.objects.create(
            space=space,
            start_hour_code=start_hour_code,
            end_hour_code=end_hour_code,
            date=validated_data['date']
        )
        return schedule


class ReservationCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=False, allow_blank=True, max_length=11, min_length=11,
        error_messages={
            'max_length': ['Phone number must be exactly 11 digits.'],
            'min_length': ['Phone number must be exactly 11 digits.']
        }
    )
    schedule = ScheduleSerializer()
    hosting_association = serializers.CharField(required=False, allow_blank=True, max_length=100)
    hosting_organizations = serializers.CharField(required=False, allow_blank=True, max_length=200)
    responsible_organizer = serializers.CharField(required=False, allow_blank=True, max_length=100)
    position = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = Reservation
        fields = [
            'id', 'space', 'reservation_type', 'reservee_type',
            'student', 'staff', 'phone_number', 'description', 'status',
            'schedule', 'hosting_association', 'hosting_organizations',
            'responsible_organizer', 'position'
        ]
        read_only_fields = ['id', 'status', 'space', 'reservee_type', 'student', 'staff']

    def validate(self, data):
        user = self.context['request'].user

        if hasattr(user, 'student_profile') and user.student_profile is not None:
            data['reservee_type'] = 'student'
            data['student'] = user.student_profile
            data['staff'] = None
        elif hasattr(user, 'staff') and user.staff is not None:
            data['reservee_type'] = 'staff'
            data['staff'] = user.staff
            data['student'] = None
        else:
            raise serializers.ValidationError({"reservee_type": ["You must be a student or staff to create a reservation."]})

        if data.get('phone_number'):
            if not data['phone_number'].isdigit() or len(data['phone_number']) != 11:
                raise serializers.ValidationError({"phone_number": ["Phone number must be exactly 11 digits."]})

        return data

    def create(self, validated_data):
        schedule_data = validated_data.pop('schedule')
        space = self.context.get('space')
        if not space:
            raise serializers.ValidationError({"space": ["Space context is missing."]})

        schedule = ScheduleSerializer(context={'space': space}).create(schedule_data)

        reservation = Reservation.objects.create(
            space=space,
            schedule=schedule,
            **validated_data
        )
        return reservation
      
        
class ReservationListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reservee_name = serializers.SerializerMethodField()
    reservee_type = serializers.SerializerMethodField()
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'space_name',
            'date',
            'start_time',
            'end_time',
            'status_display',
            'reservation_type',
            'description',
            'reservee_name',
            'reservee_type',
            'phone_number',
        ]

    def _parse_time_range(self, time_range_str, pick='start'):
        if not time_range_str or '-' not in time_range_str:
            return None
        parts = time_range_str.split('-')
        val = parts[0] if pick == 'start' else parts[-1]
        if len(val) == 5:  
            return f"{val}:00"
        return val  

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='end')

    def get_reservee_name(self, obj):
        if obj.student and getattr(obj.student, 'user', None):
            return f"{obj.student.user.first_name} {obj.student.user.last_name}".strip() or "unknown"
        if obj.staff:
            full = f"{obj.staff.first_name} {obj.staff.last_name}".strip()
            return full or "unknown"
        return "unknown"

    def get_reservee_type(self, obj):
        if obj.student:
            return "student"
        if obj.staff:
            return "staff"
        return "unknown"
    
    
class ReservationDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    manager_comment = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate(self, data):
        request = self.context['request']
        reservation = self.context['reservation']
        if not reservation.space or reservation.space.space_manager != request.user.spacemanager:
            raise serializers.ValidationError({"error": "You are not authorized to make a decision for this reservation."})
        return data

    def save(self, **kwargs):
        reservation = self.context['reservation']
        decision = self.validated_data['decision']
        comment = self.validated_data.get('manager_comment', '')

        if reservation.status != 'under_review':
            raise serializers.ValidationError({"error": "This reservation has already been processed."})
        
        reservation.status = decision
        reservation.manager_comment = comment
        reservation.save()

        if decision == 'approved':
            Event.objects.create(
                title=f"{reservation.reservation_type.title()} at {reservation.space.name}",
                event_type=reservation.reservation_type,
                space=reservation.space,
                organizer=reservation.reservee_type,
                student_organizer=reservation.student if reservation.reservee_type == 'student' else None,
                staff_organizer=reservation.staff if reservation.reservee_type == 'staff' else None,
                description=reservation.description,
                schedule=reservation.schedule,
            )
        return reservation
    
    
class ManagerSpaceListSerializer(serializers.ModelSerializer):
    first_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [
            "id", "space_type", "name", "address", "capacity", "phone_number",
            "description", "first_image_url"
        ]

    def get_first_image_url(self, obj):
        img = obj.first_image
        if not img:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(img.image.url) if request else img.image.url
    
    
class ManagerSpaceDetailSerializer(serializers.ModelSerializer):
    features = SpaceFeatureSerializer(many=True, read_only=True)
    images = SpaceImageSerializer(many=True, read_only=True)

    class Meta:
        model = Space
        fields = [
            "id", "space_type", "name", "address", "capacity", "phone_number","description", "features", "images"
        ]


class SpaceCreateSerializer(serializers.ModelSerializer):
    features = serializers.PrimaryKeyRelatedField(
        queryset=SpaceFeature.objects.all(),
        many=True,
        required=False,
        allow_empty=True
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Space
        fields = [
            "id", "space_type", "name", "address", "capacity", "phone_number",
            "description", "features", "images"
        ]

    def to_internal_value(self, data):
        if isinstance(data, MultiValueDict):
            normalized = {}

            for key in ["space_type", "name", "address", "capacity", "phone_number", "description"]:
                if key in data:
                    normalized[key] = data.get(key)

            if "features" in data:
                feats = data.getlist("features")
                if len(feats) == 1 and isinstance(feats[0], str) and ',' in feats[0]:
                    feats = [x.strip() for x in feats[0].split(',') if x.strip()]
                if len(feats) == 1 and feats[0] == "":
                    feats = []
                normalized["features"] = feats

            if "images" in data:
                imgs = [f for f in data.getlist("images") if f]  
                normalized["images"] = imgs

            return super().to_internal_value(normalized)

        if isinstance(data, dict):
            if "features" in data and isinstance(data["features"], str):
                feats = [f.strip() for f in data["features"].split(",") if f.strip()]
                data = {**data, "features": feats}

            if data.get("features") == "":
                data = {**data}
                data.pop("features")
            if data.get("images") == "":
                data = {**data}
                data.pop("images")

        return super().to_internal_value(data)

    def create(self, validated_data):
        features = validated_data.pop("features", [])
        images   = validated_data.pop("images", [])
        request  = self.context["request"]

        space = Space.objects.create(
            space_manager=request.user.spacemanager,
            **validated_data
        )

        if features:
            space.features.set(features)

        if images:
            for img in images:
                SpaceImage.objects.create(space=space, image=img)

        return space


class SpaceUpdateSerializer(serializers.ModelSerializer):
    space_type = serializers.ChoiceField(choices=Space.SPACE_TYPES, required=False)
    name = serializers.CharField(max_length=100, required=False)
    address = serializers.CharField(required=False)
    capacity = serializers.IntegerField(validators=[MinValueValidator(1)], required=False)
    phone_number = serializers.CharField(max_length=11, required=False, allow_null=True, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    features = serializers.PrimaryKeyRelatedField(
        queryset=SpaceFeature.objects.all(),
        many=True,
        required=False
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False  
    )

    class Meta:
        model = Space
        fields = ["space_type", "name", "address", "capacity", "phone_number",
                  "description", "features", "images"]

    def to_internal_value(self, data):
        if isinstance(data, (MultiValueDict,)):
            normalized = {}
            for key in ["space_type", "name", "address", "capacity", "phone_number", "description"]:
                if key in data:
                    normalized[key] = data.get(key)

            if "features" in data:
                feats = data.getlist("features")
                if len(feats) == 1 and isinstance(feats[0], str) and ',' in feats[0]:
                    feats = [x.strip() for x in feats[0].split(',') if x.strip()]
                normalized["features"] = feats

            normalized["images"] = data.getlist("images")

            return super().to_internal_value(normalized)

        if isinstance(data, dict) and "features" in data and isinstance(data["features"], str):
            feats = [f.strip() for f in data["features"].split(",") if f.strip()]
            data = {**data, "features": feats}

        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        instance.space_type   = validated_data.get("space_type", instance.space_type)
        instance.name         = validated_data.get("name", instance.name)
        instance.address      = validated_data.get("address", instance.address)
        instance.capacity     = validated_data.get("capacity", instance.capacity)
        instance.phone_number = validated_data.get("phone_number", instance.phone_number)
        instance.description  = validated_data.get("description", instance.description)

        if "features" in validated_data:
            instance.features.set(validated_data["features"])

        if "images" in validated_data:
            new_images = validated_data["images"] or []
            instance.images.all().delete()
            for img in new_images:
                SpaceImage.objects.create(space=instance, image=img)

        instance.save()
        return instance


class ReservationDetailSerializer(serializers.ModelSerializer):
    space = SpaceSerializer(read_only=True)
    schedule_date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.SerializerMethodField()
    end_time   = serializers.SerializerMethodField()
    reservee_name = serializers.SerializerMethodField()
    reservee_type = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'reservation_type', 'reservee_type',
            'reservee_name', 'phone_number', 'description',
            'status_display', 'manager_comment',
            'space', 'schedule_date', 'start_time', 'end_time',
            'hosting_association', 'hosting_organizations',
            'responsible_organizer', 'position'
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

    def get_reservee_name(self, obj):
        if obj.student and getattr(obj.student, 'user', None):
            return f"{obj.student.user.first_name} {obj.student.user.last_name}"
        elif obj.staff:
            return f"{obj.staff.first_name} {obj.staff.last_name}"
        return "unknown"
