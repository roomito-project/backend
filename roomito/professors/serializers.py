from rest_framework import serializers
from .models import Professor
from django.contrib.auth import authenticate


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class ProfessorRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    national_id = serializers.CharField()
    personnel_code = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        required_fields = ['first_name', 'last_name', 'email', 'national_id', 'personnel_code', 'password']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: "This field is required."})

        if not data['national_id'].isdigit():
            raise serializers.ValidationError({"national_id": "National ID must be numeric."})
        if not data['personnel_code'].isdigit():
            raise serializers.ValidationError({"personnel_code": "Personnel code must be numeric."})

        if Professor.objects.filter(national_id=data['national_id']).exists():
            raise serializers.ValidationError({"national_id": "This national ID is already in use."})
        if Professor.objects.filter(personnel_code=data['personnel_code']).exists():
            raise serializers.ValidationError({"personnel_code": "This personnel code is already in use."})

        try:
            professor = Professor.objects.get(
                email=data['email'],
                is_registered=False
            )
        except Professor.DoesNotExist:
            raise serializers.ValidationError("No matching unregistered professor found with the provided email.")

        return data


class ProfessorVerifySerializer(serializers.Serializer):
    personnel_code = serializers.CharField()
    verification_code = serializers.CharField()

    def validate(self, data):
        if not data.get('personnel_code'):
            raise serializers.ValidationError({"personnel_code": "Personnel code is required."})
        if not data.get('verification_code'):
            raise serializers.ValidationError({"verification_code": "Verification code is required."})

        try:
            professor = Professor.objects.get(personnel_code=data['personnel_code'])
        except Professor.DoesNotExist:
            raise serializers.ValidationError({"personnel_code": "No professor found with this personnel code."})

        if professor.verification_code != data['verification_code']:
            raise serializers.ValidationError({"verification_code": "Invalid verification code."})

        if professor.is_registered:
            raise serializers.ValidationError({"error": "This professor is already registered."})

        return data


class ProfessorLoginSerializer(serializers.Serializer):
    personnel_code = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        if not data.get('personnel_code'):
            raise serializers.ValidationError({"personnel_code": "Personnel code is required."})
        if not data.get('password'):
            raise serializers.ValidationError({"password": "Password is required."})

        from django.contrib.auth import authenticate
        user = authenticate(username=data['personnel_code'], password=data['password'])
        if user is None:
            raise serializers.ValidationError({"error": "Invalid personnel code or password."})

        if not hasattr(user, 'professor') or not user.professor.is_verified:
            raise serializers.ValidationError({"error": "Account is not verified or not a professor."})

        data['user'] = user
        return data