from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Space, SpaceManager, Event
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from professors.models import Professor
from students.models import Student

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class SpaceManagerLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if not hasattr(user, 'spacemanager'):
            raise serializers.ValidationError({"error": "User is not a space manager."})

        return data


class SpaceManagerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceManager
        fields = ['first_name', 'last_name', 'email', 'username', 'spaces']


class SpaceManagerPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Current password is incorrect."})
        return data


class SpaceListSerializer(serializers.ModelSerializer):
    space_manager = SpaceManagerProfileSerializer(read_only=True)
    
    class Meta:
        model = Space
        fields = ['id', 'name', 'address', 'capacity', 'space_manager']
        read_only_fields = ['id'] 

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than zero.")
        return value
    

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ['id', 'name', 'address', 'capacity']

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
    student = StudentSerializer(read_only=True)
    professor = ProfessorSerializer(read_only=True)
    poster = serializers.ImageField(read_only=True, allow_null=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'event_type', 'date', 'space', 'poster', 'organizer', 'student', 'professor', 'description']
        read_only_fields = ['id', 'title', 'event_type', 'date', 'space', 'poster', 'organizer', 'student', 'professor', 'description']

    def validate(self, data):
        organizer = data.get('organizer')
        student = data.get('student')
        professor = data.get('professor')

        if organizer == 'student' and not student:
            raise serializers.ValidationError({"student": "A student must be selected when organizer is 'student'."})
        if organizer == 'professor' and not professor:
            raise serializers.ValidationError({"professor": "A professor must be selected when organizer is 'professor'."})
        if student and professor:
            raise serializers.ValidationError({"error": "Only one organizer (student or professor) can be selected."})

        return data