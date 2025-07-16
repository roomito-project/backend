from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from .serializers import StudentRegistrationSerializer
from .models import Student

class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=StudentRegistrationSerializer,
        responses=inline_serializer(
            name="RegisterResponse",
            fields={
                "message": serializers.CharField(),
                "student_id": serializers.IntegerField()
            }
        ),
        description="Student Registration"
    )
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({
                "message": "ثبت‌نام با موفقیت انجام شد",
                "student_id": student.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
