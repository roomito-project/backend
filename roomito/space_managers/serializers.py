from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Space, SpaceManager, Event, SpaceFeature, Schedule, Reservation
from professors.models import Professor
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


class SpaceListSerializer(serializers.ModelSerializer):
    space_manager = SpaceManagerProfileSerializer(read_only=True)
    features = SpaceFeatureSerializer(many=True, read_only=True) 
    
    class Meta:
        model = Space
        fields = ['id', 'name', 'address', 'capacity', 'description', 'space_manager', 'features']
        read_only_fields = ['id'] 

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than zero.")
        return value
    

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ['id', 'name', 'address', 'capacity', 'description', 'space_manager', 'features']


class StudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'student_id']


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ['first_name', 'last_name', 'personnel_code', 'email']


class EventSerializer(serializers.ModelSerializer):
    space = SpaceSerializer(read_only=True)
    student_organizer = StudentSerializer(read_only=True)
    professor_organizer = ProfessorSerializer(read_only=True)
    poster = serializers.ImageField(read_only=True, allow_null=True)
    date = serializers.DateField(source='schedule.date', read_only=True)
    start_time = serializers.TimeField(source='schedule.start_time', read_only=True)
    end_time = serializers.TimeField(source='schedule.end_time', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'date', 'start_time', 'end_time',
            'space', 'poster', 'organizer',
            'student_organizer', 'professor_organizer', 'description'
        ]
        read_only_fields = fields

    def validate(self, data):
        organizer = data.get('organizer')
        student = data.get('student_organizer')
        professor = data.get('professor_organizer')

        if organizer == 'student' and not student:
            raise serializers.ValidationError({"student_organizer": "A student must be selected when organizer is 'student'."})
        if organizer == 'professor' and not professor:
            raise serializers.ValidationError({"professor_organizer": "A professor must be selected when organizer is 'professor'."})
        if student and professor:
            raise serializers.ValidationError({"error": "Only one organizer (student or professor) can be selected."})

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
        elif obj.organizer == 'professor' and obj.professor_organizer:
            return f"{obj.professor_organizer.first_name} {obj.professor_organizer.last_name}"
        return "unknown"

    def get_poster_url(self, obj):
        if obj.poster:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.poster.url) if request else obj.poster.url
        return None


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['start_time', 'end_time', 'date']


class ReservationCreateSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer()

    class Meta:
        model = Reservation
        fields = ['id', 'space', 'reservation_type', 'reservee_type', 'student', 'professor', 'description', 'status', 'schedule']
        read_only_fields = ['id', 'status', 'student', 'professor']

    def validate(self, data):
        user = self.context['request'].user

        if data['reservee_type'] == 'student' and not hasattr(user, 'student'):
            raise serializers.ValidationError({"reservee_type": "You must be a student to select this reservee type."})
        if data['reservee_type'] == 'professor' and not hasattr(user, 'professor'):
            raise serializers.ValidationError({"reservee_type": "You must be a professor to select this reservee type."})

        if data['reservee_type'] == 'student':
            data['student'] = user.student
            data['professor'] = None
        elif data['reservee_type'] == 'professor':
            data['professor'] = user.professor
            data['student'] = None

        schedule_data = data['schedule']
        if schedule_data['start_time'] >= schedule_data['end_time']:
            raise serializers.ValidationError({"schedule": "Start time must be before end time."})

        return data

    def create(self, validated_data):
        schedule_data = validated_data.pop('schedule')
        space = validated_data['space']
        schedule = Schedule.objects.create(space=space, **schedule_data)
        reservation = Reservation.objects.create(schedule=schedule, **validated_data)
        return reservation
  

class ReservationListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name')
    date = serializers.DateField(source='schedule.date')
    start_time = serializers.TimeField(source='schedule.start_time')
    end_time = serializers.TimeField(source='schedule.end_time')
    status_display = serializers.CharField(source='get_status_display') 
    reservee_name = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = ['id', 'space_name', 'date', 'start_time', 'end_time', 'status_display', 'reservation_type', 'description', 'reservee_name']

    def get_reservee_name(self, obj):
        return obj.student.first_name if obj.student else obj.professor.first_name if obj.professor else "unknown"    