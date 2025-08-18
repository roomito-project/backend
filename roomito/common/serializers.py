from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    

class UnifiedLoginSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['staff', 'student', 'space_manager'])
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        if not data.get('role') or not data.get('username') or not data.get('password'):
            raise serializers.ValidationError("All fields are required.")
        return data
