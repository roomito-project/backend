from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
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

    def validate_student_id(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Student ID must be numeric.")
        if len(value) > 12:
            raise serializers.ValidationError("Student ID cannot be more than 12 digits.")
        return value

    def validate_national_id(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("National ID must be numeric.")
        if len(value) != 10:
            raise serializers.ValidationError("National ID must be exactly 10 digits.")
        return value


    def validate(self, data):
        # if User.objects.filter(email=data['email']).exists():
        #     raise serializers.ValidationError({"email": "This email is already registered."})
        if User.objects.filter(username=data['student_id']).exists() or Student.objects.filter(student_id=data['student_id']).exists():
            raise serializers.ValidationError({"student_id": "This student ID is already in use."})
        if not data['student_card_photo'].content_type.startswith('image/'):
            raise serializers.ValidationError({"student_card_photo": "Only image files are allowed."})
        return data


class StudentProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email') 
    student_card_photo = serializers.ImageField()

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'student_id', 'national_id', 'student_card_photo']
    
        
class StudentProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    student_id = serializers.CharField(max_length=20)
    national_id = serializers.CharField(max_length=10)
    email = serializers.EmailField()
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
        user.email = validated_data.get("email", user.email)
        if 'new_password' in validated_data:
            user.set_password(validated_data['new_password'])
        user.save()
        
        instance.student_id = validated_data.get('student_id', instance.student_id)
        instance.national_id = validated_data.get('national_id', instance.national_id)
        instance.save()

        return instance