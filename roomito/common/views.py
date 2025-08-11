from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from professors.models import Professor
from students.models import Student
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
                        value={"access": "access_token", "refresh": "refresh_token", "role": "professor"},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Missing fields or invalid input format",
                examples=[
                    OpenApiExample(
                        "InvalidRole",
                        value={"error": "Invalid role. Must be one of: professor, student, space_manager."},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized – invalid credentials or account status",
                examples=[
                    OpenApiExample("InvalidCredentials", value={"error": "Invalid credentials."}, response_only=True),
                    OpenApiExample("StudentNotApproved", value={"error": "Your student card is not yet approved."}, response_only=True),
                    OpenApiExample("NotSpaceManager", value={"error": "User is not a space manager."}, response_only=True),
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal Server Error – token generation failed",
                examples=[
                    OpenApiExample("TokenGenerationError", value={"error": "Failed to generate token."}, response_only=True)
                ]
            )
        },
        description="Unified login for professors, students, and space managers (use personnel code for professor and student id for student as usernames)."
    )
    def post(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = (serializer.validated_data['role'] or '').strip().lower()
        username = (serializer.validated_data['username'] or '').strip()
        password = serializer.validated_data['password'] 

        try:
            if role == 'professor':
                try:
                    professor = Professor.objects.get(personnel_code=username)
                except Professor.DoesNotExist:
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                user = professor.user

                if user is None:
                    cached_pw = cache.get(f"professor_password_{professor.email}") or \
                                cache.get(f"professor_password_{professor.personnel_code}") or \
                                cache.get(f"prof_tmp_pass_{professor.personnel_code}")

                    if not cached_pw or cached_pw != password:
                        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                    user = User.objects.create_user(
                        username=professor.personnel_code,
                        password=password,
                        first_name=professor.first_name,
                        last_name=professor.last_name,
                        email=professor.email,
                    )
                    professor.user = user
                    professor.is_registered = True
                    professor.save(update_fields=['user', 'is_registered'])

                    cache.delete(f"professor_password_{professor.email}")
                    cache.delete(f"professor_password_{professor.personnel_code}")
                    cache.delete(f"prof_tmp_pass_{professor.personnel_code}")

                else:
                    if not user.check_password(password):
                        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            elif role == 'student':
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                if not hasattr(user, 'student_profile'):
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                if not user.student_profile.is_approved:
                    return Response({"error": "Your student card is not yet approved."}, status=status.HTTP_401_UNAUTHORIZED)

                if not user.check_password(password):
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            elif role == 'space_manager':
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                if not hasattr(user, 'spacemanager'):
                    return Response({"error": "User is not a space manager."}, status=status.HTTP_401_UNAUTHORIZED)

                if not user.check_password(password):
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

            else:
                return Response(
                    {"error": "Invalid role. Must be one of: professor, student, space_manager."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                refresh = RefreshToken.for_user(user)
            except Exception:
                return Response({"error": "Failed to generate token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": role,
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
