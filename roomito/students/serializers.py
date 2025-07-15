from rest_framework import serializers
from .models import Student
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']

class StudentRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'student_id', 'national_id', 'student_card_photo']
        
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            email=user_data['email'],
            password=user_data['password']
        )
        student = Student.objects.create(user=user, **validated_data)
        return student        