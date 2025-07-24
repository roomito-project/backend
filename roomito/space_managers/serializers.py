from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SpaceManager
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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
