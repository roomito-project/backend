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
    
    
class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    

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
    

class StudentProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    student_id = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=10)
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=8)    
    
    def validate_password(self, value):
        validate_password_strength(value)
        return value
    
    def validate(self, attrs):
        if 'new_password' in attrs:
            if 'current_password' not in attrs:
                raise serializers.ValidationError({"current_password": "Current password is required to change password."})
            user = self.context['request'].user
            if not user.check_password(attrs['current_password']):
                raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs
    
    def validate_student_id(self, value):
        student = getattr(self.context['request'].user, 'student_profile', None)
        if Student.objects.exclude(pk=student.pk).filter(student_id=value).exists():
            raise serializers.ValidationError("This student ID is already in use.")
        return value

    def validate_national_id(self, value):
        student = getattr(self.context['request'].user, 'student_profile', None)
        if Student.objects.exclude(pk=student.pk).filter(national_id=value).exists():
            raise serializers.ValidationError("This national ID is already in use.")
        return value
    
    def update(self, instance, validated_data):
        user = instance.user
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        if 'new_password' in validated_data:
            user.set_password(validated_data['new_password'])
        user.save()
        
        instance.student_id = validated_data.get('student_id', instance.student_id)
        instance.national_id = validated_data.get('national_id', instance.national_id)
        instance.save()

        return instance