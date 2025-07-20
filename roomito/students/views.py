from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import StudentRegistrationSerializer
from .models import Student
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import StudentLoginSerializer

class StudentRegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=StudentRegistrationSerializer,
        responses={
            201: OpenApiExample(
                name="Success",
                value={
                    "message": "The student has been successfully registered. Please wait for the confirmation of the card photo.",
                    "student_id": 42
                },
                response_only=True,
                status_codes=["201"]
            )
        },
        examples=[
            OpenApiExample(
                name="RegisterStudentExample",
                value={
                    "first_name": "string",
                    "last_name": "string",
                    "email": "user@example.com",
                    "password": "string",
                    "student_id": "string",
                    "national_id": "string",
                    "student_card_photo": "string.png"
                },
                request_only=True
            )
        ],
        description="Student registration (using student card photo)"
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
                "message": "The student has been successfully registered. Please wait for the confirmation of the card photo.",
                "student_id": student.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StudentLoginView(TokenObtainPairView):
    serializer_class = StudentLoginSerializer