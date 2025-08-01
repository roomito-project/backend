from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from common.validators import validate_password_strength
from .models import Student


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessRegistrationResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    student_id = serializers.IntegerField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class StudentRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    student_id = serializers.CharField()
    national_id = serializers.CharField()
    student_card_photo = serializers.ImageField()

    def validate_password(self, value):
        validate_password_strength(value)
        return value
    
    def validate(self, data):
        if not data.get('first_name'):
            raise serializers.ValidationError({"first_name": _("First name is required.")})
        if not data.get('last_name'):
            raise serializers.ValidationError({"last_name": _("Last name is required.")})
        if not data.get('email'):
            raise serializers.ValidationError({"email": _("Email is required.")})
        if not data.get('password'):
            raise serializers.ValidationError({"password": _("Password is required.")})
        if not data.get('student_id'):
            raise serializers.ValidationError({"student_id": _("Student ID is required.")})
        if not data.get('national_id'):
            raise serializers.ValidationError({"national_id": _("National ID is required.")})
        if not data.get('student_card_photo'):
            raise serializers.ValidationError({"student_card_photo": _("Student card photo is required.")})

        if not data['national_id'].isdigit():
            raise serializers.ValidationError({"national_id": _("National ID must be numeric.")})

        if not data['student_id'].isdigit():
            raise serializers.ValidationError({"student_id": _("Student ID must be numeric.")})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": _("This email is already registered.")})

        if User.objects.filter(username=data['student_id']).exists() or Student.objects.filter(student_id=data['student_id']).exists():
            raise serializers.ValidationError({"student_id": _("This student ID is already in use.")})

        if not data['student_card_photo'].content_type.startswith('image/'):
            raise serializers.ValidationError({"student_card_photo": _("Only image files are allowed.")})

        return data


class StudentLoginSerializer(TokenObtainPairSerializer):
    username_field = 'username'

    def validate(self, attrs):
        data = super().validate(attrs)

        if hasattr(self.user, 'student_profile'):
            if not self.user.student_profile.is_approved:
                raise serializers.ValidationError({"error": _("Your student card is not yet approved.")})
        else:
            raise serializers.ValidationError({"error": _("User is not a student.")})

        return data