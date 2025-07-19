from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .serializers import StudentRegistrationSerializer
from .models import Student

class StudentRegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=StudentRegistrationSerializer,
        responses=inline_serializer(
            name="RegisterResponse",
            fields={
                "message": serializers.CharField(),
                "student_id": serializers.IntegerField(),
            }
        ),
        description="Student registeration (using student card photo)"
    )
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            user = User.objects.create_user(
                username=data["student_id"],
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            student = Student.objects.create(
                user=user,
                student_id=data["student_id"],
                national_id=data["national_id"],
                student_card_photo=data["student_card_photo"],
            )

            return Response({
                "message": "The student has been successfully registered.\n Please wait for the confirmation of the card photo.",
                "student_id": student.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
