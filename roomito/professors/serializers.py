from rest_framework import serializers
from .models import Staff
from common.validators import validate_password_strength
import re


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class StaffRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    personnel_code = serializers.CharField(max_length=10)
    national_id = serializers.CharField()

    def validate_email(self, value):
        if '[at]' in value:
            value = value.replace('[at]', '@')
        return value

    def validate_national_id(self, value):
        if not re.fullmatch(r'\d{10}', value):
            raise serializers.ValidationError("National ID must be exactly 10 digits.")
        return value

    def validate_personnel_code(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Personnel code cannot be more than 10 characters.")
        return value

    def validate(self, data):
        required_fields = ['first_name', 'last_name', 'email', 'personnel_code', 'national_id']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: "This field is required."})
        return data


class StaffProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    personnel_code = serializers.CharField(max_length=20)
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
    
    def validate_personnel_code(self, value):
        Staff = self.context['request'].user.Staff
        if Staff.objects.exclude(pk=Staff.pk).filter(personnel_code=value).exists():
            raise serializers.ValidationError("This personnel code is already in use.")
        return value

    def validate_national_id(self, value):
        Staff = self.context['request'].user.Staff
        if Staff.objects.exclude(pk=Staff.pk).filter(national_id=value).exists():
            raise serializers.ValidationError("This national ID is already in use.")
        return value
    
    # def validate_email(self, value):
    #     user = self.context['request'].user.Staff
    #     if Staff.objects.exclude(pk=Staff.pk).filter(email=value).exists():
    #         raise serializers.ValidationError("This email is already in use.")
    #     return value
    
    def update(self, instance, validated_data):
        user = instance.user
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.email = validated_data.get("email", user.email)
        if 'new_password' in validated_data:
            user.set_password(validated_data['new_password'])
        user.save()

        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.personnel_code = validated_data.get("personnel_code", instance.personnel_code)
        instance.national_id = validated_data.get("national_id", instance.national_id)
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        return instance
    

class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ["first_name", "last_name", "email", "personnel_code", "national_id"]    