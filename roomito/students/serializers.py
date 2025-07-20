from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Student
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

class StudentRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    student_id = serializers.CharField()
    national_id = serializers.CharField()
    student_card_photo = serializers.ImageField()

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create(
            username=validated_data['student_id'], 
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password)
        )

        student = Student.objects.create(user=user, **validated_data)
        return student

class StudentLoginSerializer(TokenObtainPairSerializer):
    username_field = 'username' 

    def validate(self, attrs):
        data = super().validate(attrs)

        if hasattr(self.user, 'student_profile'):
            if not self.user.student_profile.is_approved:
                raise serializers.ValidationError(_("Your student card is not yet approved."))
        else:
            raise serializers.ValidationError(_("User is not a student."))

        return data