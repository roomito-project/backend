from rest_framework import serializers
from .models import Professor

class ProfessorRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    national_id = serializers.CharField()
    personnel_code = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            professor = Professor.objects.get(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                national_id=data['national_id'],
                personnel_code=data['personnel_code'],
                is_registered=False
            )
        except Professor.DoesNotExist:
            raise serializers.ValidationError("The entered information does not match the registered information.")
        return data

class ProfessorVerifySerializer(serializers.Serializer):
    personnel_code = serializers.CharField()
    verification_code = serializers.CharField()
    
class ProfessorLoginSerializer(serializers.Serializer):
    personnel_code = serializers.CharField()
    password = serializers.CharField(write_only=True)    