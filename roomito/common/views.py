from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from professors.models import Professor
from students.models import Student
from space_managers.models import SpaceManager
from .serializers import UnifiedLoginSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import UnifiedLoginSerializer, TokenResponseSerializer, ErrorResponseSerializer

class UnifiedLoginView(APIView):
    @extend_schema(
        request=UnifiedLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "LoginSuccess",
                        value={"access": "access_token", "refresh": "refresh_token"},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Missing fields or invalid input format",
                examples=[
                    OpenApiExample(
                        "MissingFields",
                        value={"role": ["This field is required."]},
                        response_only=True
                    ),
                    OpenApiExample(
                        "InvalidChoice",
                        value={"role": ["\"admin\" is not a valid choice."]},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized – invalid credentials or account status",
                examples=[
                    OpenApiExample(
                        "ProfessorNotRegistered",
                        value={"error": "Invalid personnel code or password."},
                        response_only=True
                    ),
                    OpenApiExample(
                        "StudentNotApproved",
                        value={"error": "Your student card is not yet approved."},
                        response_only=True
                    ),
                    OpenApiExample(
                        "SpaceManagerMissing",
                        value={"error": "User is not a space manager."},
                        response_only=True
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal Server Error – token generation failed",
                examples=[
                    OpenApiExample(
                        "TokenGenerationError",
                        value={"error": "Failed to generate token."},
                        response_only=True
                    )
                ]
            )
        },
        description="Unified login for professors, students, and space managers (use personnel code for professor and student id for student as usernames)."
    )

    def post(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = serializer.validated_data['role']
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            if role == 'professor':
                professor = Professor.objects.get(personnel_code=username)
                email = professor.email
                if not professor.is_registered:
                    cached_password = cache.get(f"professor_password_{email}")
                    if cached_password == password:
                        user = User.objects.create_user(username=username, password=password)
                        professor.user = user
                        professor.is_registered = True
                        professor.save()
                        cache.delete(f"professor_password_{email}")
                    else:
                        raise Exception("Invalid personnel code or password.")
                else:
                    user = professor.user
                    if not user.check_password(password):
                        raise Exception("Invalid personnel code or password.")

            elif role == 'student':
                user = User.objects.get(username=username)
                if not hasattr(user, 'student_profile'):
                    raise Exception("User is not a student.")
                if not user.student_profile.is_approved:
                    raise Exception("Your student card is not yet approved.")
                if not user.check_password(password):
                    raise Exception("Invalid username or password.")

            elif role == 'space_manager':
                user = User.objects.get(username=username)
                if not hasattr(user, 'spacemanager'):
                    raise Exception("User is not a space manager.")
                if not user.check_password(password):
                    raise Exception("Invalid username or password.")

            else:
                return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
