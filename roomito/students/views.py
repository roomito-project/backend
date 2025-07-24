from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .models import Student
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    StudentRegistrationSerializer,
    ErrorResponseSerializer,
    SuccessRegistrationResponseSerializer,
    StudentLoginSerializer,
    TokenResponseSerializer
)


class StudentRegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=StudentRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=SuccessRegistrationResponseSerializer,
                description="Student registration successful",
                examples=[
                    OpenApiExample(
                        name="RegistrationSuccess",
                        value={
                            "message": "The student has been successfully registered. Please wait for the confirmation of the card photo.",
                            "student_id": 42
                        },
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid data or format",
                examples=[
                    OpenApiExample(
                        name="InvalidData",
                        value={"error": "One or more fields are invalid."},
                        response_only=True
                    )
                ]
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Duplicate email or student ID",
                examples=[
                    OpenApiExample(
                        name="Conflict",
                        value={"error": "Email or student ID already exists."},
                        response_only=True
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error",
                examples=[
                    OpenApiExample(
                        name="UnexpectedError",
                        value={"error": "An unexpected error occurred."},
                        response_only=True
                    )
                ]
            ),
        },
        description="Student registeration"
    )
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "One or more fields are invalid."}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            if User.objects.filter(email=data["email"]).exists():
                return Response({"error": "Email already exists."}, status=status.HTTP_409_CONFLICT)

            if User.objects.filter(username=data["student_id"]).exists() or Student.objects.filter(student_id=data["student_id"]).exclude(id__isnull=True).exists():
                return Response({"error": "Student ID already exists."}, status=status.HTTP_409_CONFLICT)

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

        except Exception:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentLoginView(TokenObtainPairView):
    serializer_class = StudentLoginSerializer

    @extend_schema(
        request=StudentLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[
                    OpenApiExample(
                        name="LoginSuccess",
                        value={"access": "access_token", "refresh": "refresh_token"},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid credentials or not approved",
                examples=[
                    OpenApiExample(
                        name="LoginError",
                        value={"error": "Your student card is not yet approved."},
                        response_only=True
                    )
                ]
            )
        },
            description="Student login using student id and password"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)