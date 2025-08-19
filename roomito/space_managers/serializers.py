from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Space, SpaceImage, SpaceManager, Event, SpaceFeature, Schedule, Reservation
from staffs.models import Staff
from students.models import Student
from common.validators import validate_password_strength


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
    
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
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
        fields = ['id', 'name', 'address', 'capacity', 'description', 'space_manager','phone_number', 'first_image_url']
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
        fields = ['id', 'name', 'address', 'capacity', 'description', 'space_manager', 'phone_number', 'features', 'images']
        
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


class EventSerializer(serializers.ModelSerializer):
    space = SpaceSerializer(read_only=True)
    student_organizer = StudentSerializer(read_only=True)
    staff_organizer = StaffSerializer(read_only=True)
    poster = serializers.ImageField(read_only=True, allow_null=True)
    date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.TimeField(source='schedule.start_time', read_only=True)
    end_time = serializers.TimeField(source='schedule.end_time', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'date', 'start_time', 'end_time',
            'space', 'poster', 'organizer',
            'student_organizer', 'staff_organizer', 'description'
        ]
        read_only_fields = fields

    def validate(self, data):
        organizer = data.get('organizer')
        student = data.get('student_organizer')
        staff = data.get('staff_organizer')

        if organizer == 'student' and not student:
            raise serializers.ValidationError({"student_organizer": "A student must be selected when organizer is 'student'."})
        if organizer == 'staff' and not staff:
            raise serializers.ValidationError({"staff_organizer": "A staff must be selected when organizer is 'staff'."})
        if student and staff:
            raise serializers.ValidationError({"error": "Only one organizer (student or staff) can be selected."})

        return data


class EventDetailSerializer(serializers.ModelSerializer):
    organizer_name = serializers.SerializerMethodField()
    space_name = serializers.CharField(source='space.name', default=None)
    poster_url = serializers.SerializerMethodField()
    date = serializers.DateField(source='schedule.date', default=None)
    start_time = serializers.TimeField(source='schedule.start_time', default=None)
    end_time = serializers.TimeField(source='schedule.end_time', default=None)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'date', 'start_time', 'end_time',
            'space_name', 'poster_url', 'organizer', 'organizer_name', 'description'
        ]

    def get_organizer_name(self, obj):
        if obj.organizer == 'student' and obj.student_organizer:
            return f"{obj.student_organizer.first_name} {obj.student_organizer.last_name}"
        elif obj.organizer == 'staff' and obj.staff_organizer:
            return f"{obj.staff_organizer.first_name} {obj.staff_organizer.last_name}"
        return "unknown"

    def get_poster_url(self, obj):
        if obj.poster:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.poster.url) if request else obj.poster.url
        return None


class ScheduleSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(format='%H:%M:%S', input_formats=['%H:%M:%S'])
    end_time   = serializers.TimeField(format='%H:%M:%S', input_formats=['%H:%M:%S'])
    class Meta:
        model = Schedule
        fields = ['start_time', 'end_time', 'date']


class ReservationCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=11,
        min_length=11,
        error_messages={
            'max_length': 'Phone number must be exactly 11 digits.',
            'min_length': 'Phone number must be exactly 11 digits.'
        }
    )
     
    schedule = ScheduleSerializer()

    class Meta:
        model = Reservation
        fields = [
            'id', 'space', 'reservation_type', 'reservee_type',
            'student', 'staff', 'phone_number', 'description', 'status', 'schedule'
        ]
        read_only_fields = ['id', 'status', 'space', 'reservee_type', 'student', 'staff']

    def validate(self, data):
        user = self.context['request'].user

        if hasattr(user, 'student_profile'):
            data['reservee_type'] = 'student'
            data['student'] = user.student_profile
            data['staff'] = None
        elif hasattr(user, 'staff'):
            data['reservee_type'] = 'staff'
            data['staff'] = user.staff
            data['student'] = None
        else:
            raise serializers.ValidationError("You must be a student or staff to create a reservation.")

        if data.get('phone_number'):
            if not data['phone_number'].isdigit() or len(data['phone_number']) != 11:
                raise serializers.ValidationError({"phone_number": "Phone number must be exactly 11 digits."})
            
        schedule_data = data['schedule']
        start = schedule_data['start_time']
        end   = schedule_data['end_time']

        if start == end:
            raise serializers.ValidationError({"schedule": "Start and end time cannot be the same."})
        if start > end:
            raise serializers.ValidationError({"schedule": "Start time must be before end time."})

        return data

    def create(self, validated_data):
        schedule_data = validated_data.pop('schedule')
        space = self.context['space']
        schedule = Schedule.objects.create(space=space, **schedule_data)
        reservation = Reservation.objects.create(space=space, schedule=schedule, **validated_data)
        return reservation
  

class ReservationListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name')
    date = serializers.DateField(source='schedule.date')
    start_time = serializers.TimeField(source='schedule.start_time')
    end_time = serializers.TimeField(source='schedule.end_time')
    status_display = serializers.CharField(source='get_status_display') 
    reservee_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField() 
    reservee_type = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = ['id', 'space_name', 'date', 'start_time', 'end_time', 'status_display', 'reservation_type', 'description', 'reservee_name', 'reservee_type', 'phone_number']

    def get_reservee_name(self, obj):
        if obj.student and obj.student.user:
            return f"{obj.student.user.first_name} {obj.student.user.last_name}"
        elif obj.staff:
            return f"{obj.staff.first_name} {obj.staff.last_name}"
        return "unknown"   
    
    def get_reservee_type(self, obj):
        if obj.student:
            return "student"
        elif obj.staff:
            return "staff"
        return "unknown" 
    
    
class ManagerSpaceListSerializer(serializers.ModelSerializer):
    first_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [
            "id", "name", "address", "capacity", "phone_number",
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
            "id", "name", "address", "capacity", "phone_number","description", "features", "images"
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
            "id", "name", "address", "capacity", "phone_number",
            "description", "features", "images"
        ]

    def to_internal_value(self, data):
        mutable = data.copy()

        features = mutable.get("features")
        if features:
            if isinstance(features, str):
                try:
                    mutable.setlist("features", [int(f.strip()) for f in features.split(",")])
                except ValueError:
                    pass 
                
        if mutable.get('features') == "":
            mutable.pop('features') 
            
        if mutable.get('images') == "":
            mutable.pop('images') 
             
        return super().to_internal_value(mutable)

    def create(self, validated_data):
        features = validated_data.pop("features", [])
        images = validated_data.pop("images", [])
        request = self.context["request"]

        space = Space.objects.create(
            space_manager=request.user.spacemanager,
            **validated_data
        )
        if features:
            space.features.set(features)

        for img in images:
            SpaceImage.objects.create(space=space, image=img)

        return space


class SpaceUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    capacity = serializers.IntegerField(required=False)

    class Meta:
        model = Space
        fields = ["name", "address", "capacity", "phone_number", "description"]

    def validate(self, attrs):
        for field in ["name", "address", "description"]:
            if field in attrs and (attrs[field] is None or attrs[field] == ""):
                attrs.pop(field)

        if "phone_number" in attrs and attrs["phone_number"] in ["", None]:
            attrs["phone_number"] = None

        return attrs

    def update(self, instance, validated_data):
        for field in ["name", "address", "description", "phone_number", "capacity"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
