from rest_framework import serializers
from .models import Staff
from common.validators import validate_password_strength
import re
from django.contrib.auth.models import User


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
        if Staff.objects.filter(personnel_code=data['personnel_code']).exists():
            raise serializers.ValidationError({"personnel_code": ["A staff with this personnel code already exists."]})
        if Staff.objects.filter(national_id=data['national_id']).exists():
            raise serializers.ValidationError({"national_id": ["A staff with this national ID already exists."]})
        return data
    
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['personnel_code'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email']
        )
        user.set_unusable_password()
        user.save()

        staff = Staff.objects.create(user=user, **validated_data, is_registered=True)
        return staff


class StaffProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False)
    last_name  = serializers.CharField(max_length=100, required=False)
    personnel_code = serializers.CharField(max_length=20, required=False)
    national_id    = serializers.CharField(max_length=10, required=False)
    email = serializers.EmailField(required=False)

    current_password = serializers.CharField(write_only=True, required=False)
    new_password     = serializers.CharField(write_only=True, required=False, min_length=8)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        want_change_pwd = bool(attrs.get("new_password"))
        if want_change_pwd:
            current = attrs.get("current_password")
            if not current:
                raise serializers.ValidationError({"current_password": "Current password is required to change password."})

            staff_instance = getattr(self, "instance", None)
            target_user = getattr(staff_instance, "user", None) if staff_instance else None
            if target_user is None:
                raise serializers.ValidationError({"user": "This staff profile is not linked to a user account."})

            if not target_user.check_password(current):
                req_user = self.context.get("request").user if self.context.get("request") else None
                if not (req_user and req_user.pk == target_user.pk and req_user.check_password(current)):
                    raise serializers.ValidationError({"current_password": "Current password is incorrect."})


        return attrs

    def validate_personnel_code(self, value):
        request = self.context.get('request')
        if not request:
            return value
        staff = getattr(request.user, 'staff', None)
        if staff is None:
            return value
        if Staff.objects.exclude(pk=staff.pk).filter(personnel_code=value).exists():
            raise serializers.ValidationError("This personnel code is already in use.")
        return value

    def validate_national_id(self, value):
        if value and (len(value) != 10 or not value.isdigit()):
            raise serializers.ValidationError("National ID must be exactly 10 digits.")
        request = self.context.get('request')
        if not request:
            return value
        staff = getattr(request.user, 'staff', None)
        if staff is None:
            return value
        from .models import Staff
        if Staff.objects.exclude(pk=staff.pk).filter(national_id=value).exists():
            raise serializers.ValidationError("This national ID is already in use.")
        return value

    # def validate_email(self, value):
    #     instance = getattr(self, 'instance', None) 
    #     current_user_id = instance.user_id if instance else None
    #     if User.objects.exclude(pk=current_user_id).filter(email=value).exists():
    #         raise serializers.ValidationError("This email is already in use.")
    #     return value

    def update(self, instance, validated_data):
    
        user = instance.user

        new_password = validated_data.get('new_password')
        if new_password:
            user.set_password(new_password)

        for f in ('first_name', 'last_name', 'email'):
            if f in validated_data:
                setattr(user, f, validated_data[f])
        user.save()

        for f in ('first_name', 'last_name', 'email', 'personnel_code', 'national_id'):
            if f in validated_data:
                setattr(instance, f, validated_data[f])

        instance.save()
        return instance
    

class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ["first_name", "last_name", "email", "personnel_code", "national_id"]    