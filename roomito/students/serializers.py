from rest_framework import serializers
from .models import Student
from django.contrib.auth.hashers import make_password

class StudentRegistrationSerializer(serializers.ModelSerializer):
    student_card_photo = serializers.ImageField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Student
        fields = [
            'email',
            'password',
            'first_name',
            'last_name',
            'student_id',
            'national_id',
            'student_card_photo'
        ]

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return Student.objects.create(**validated_data)
