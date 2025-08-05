from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.core.cache import cache
from .models import Professor
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    ProfessorRegisterSerializer,
    ProfessorLoginSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    TokenResponseSerializer,
    ProfessorProfileUpdateSerializer
)

class ProfessorRegisterView(APIView):
    @extend_schema(
        request=ProfessorRegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Successful registration",
                examples=[
                    OpenApiExample(
                        name="Success example",
                        value={"message": "The verification code and temporary password have been sent to the email."},
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid registration data",
                examples=[
                    OpenApiExample(
                        name="InvalidData",
                        value={"error": "Invalid data provided."},
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Professor not found or email mismatch",
                examples=[
                    OpenApiExample(
                        name="ProfessorNotFound",
                        value={"error": "Professor not found or email does not match the registered email."},
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Email sending failed",
                examples=[
                    OpenApiExample(
                        name="EmailSendError",
                        value={"error": "Failed to send verification email."},
                    )
                ]
            ),
        },
        description="Professor registration by University email and etc."
    )
    def post(self, request):
        serializer = ProfessorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            professor = Professor.objects.get(
                first_name__iexact=data['first_name'],
                last_name__iexact=data['last_name'],
                email__iexact=data['email'],
                is_registered=False
            )
        except Professor.DoesNotExist:
            return Response({"error": "Professor not found or details do not match the registered data."}, status=status.HTTP_404_NOT_FOUND)

        professor.personnel_code = data['personnel_code']
        professor.national_id = data['national_id']
        professor.save()

        temp_password = get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*')

        cache.set(f"professor_password_{data['email']}", temp_password, timeout=600) 

        try:
            send_mail(
                subject="رمز موقت ثبت‌نام در رومیتو",
                message=f"به رومیتو خوش آمدید\nرمز موقت شما: {temp_password}\nلطفاً پس از ورود رمز خود را تغییر دهید.",
                from_email="mahyajfri37@example.com",
                recipient_list=[professor.email],
                fail_silently=False
            )
        except Exception:
            return Response({"error": "Failed to send verification email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "The temporary password has been sent to the email."}, status=status.HTTP_200_OK)

class ProfessorLoginView(APIView):
    @extend_schema(
        request=ProfessorLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[
                    OpenApiExample(
                        name="LoginSuccess",
                        value={"access": "token_string", "refresh": "refresh_token_string"},
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid login data",
                examples=[
                    OpenApiExample(
                        name="InvalidData",
                        value={"error": "Invalid data provided."},
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        name="UnauthorizedError",
                        value={"error": "Invalid personnel code or password."},
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Token generation failed",
                examples=[
                    OpenApiExample(
                        name="TokenGenerationError",
                        value={"error": "Failed to generate token."},
                    )
                ]
            ),
        },
        description="Professor login using personnel code and temporary password"
    )
    def post(self, request):
        serializer = ProfessorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        personnel_code = serializer.validated_data['personnel_code']
        password = serializer.validated_data['password']

        try:
            professor = Professor.objects.get(personnel_code=personnel_code)
            email = professor.email 
            if not professor.is_registered:
                cached_password = cache.get(f"professor_password_{email}")
                if cached_password and cached_password == password:
                    user = User.objects.create_user(
                        username=personnel_code, 
                        password=password
                    )
                    professor.user = user
                    professor.is_registered = True
                    professor.save()
                    cache.delete(f"professor_password_{email}")
                else:
                    return Response({"error": "Invalid personnel code or password."}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                user = professor.user
                if not user.check_password(password):
                    return Response({"error": "Invalid personnel code or password."}, status=status.HTTP_401_UNAUTHORIZED)
        except Professor.DoesNotExist:
            return Response({"error": "Invalid personnel code or password."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Failed to generate token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfessorProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]   
    
    @extend_schema(
    request=ProfessorProfileUpdateSerializer,
    responses={
        200: OpenApiResponse(
            response=SuccessResponseSerializer,
            description="Profile updated successfully.",
            examples=[
                OpenApiExample(
                    name="UpdateSuccess",
                    value={"message": "Profile updated successfully."}
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Invalid input or validation error.",
            examples=[
                OpenApiExample(
                    name="ValidationError",
                    value={"personnel_code": ["This personnel code is already in use."]}
                ),
                OpenApiExample(
                    name="ValidationError",
                    value={"national_code": ["This national code is already in use."]}
                ),
                OpenApiExample(
                    name="MissingCurrentPassword",
                    value={"current_password": ["Current password is required to change password."]}
                ),
                OpenApiExample(
                    name="IncorrectCurrentPassword",
                    value={"current_password": ["Current password is incorrect."]}
                ),
            ]
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Authentication credentials were not provided or invalid.",
            examples=[
                OpenApiExample(
                    name="Unauthorized",
                    value={"detail": "Authentication credentials were not provided."}
                )
            ]
        ),
    },
        description="update profile informations of the authenticated professor"
)
    
    def patch(self, request):
        professor = request.user.professor
        serializer = ProfessorProfileUpdateSerializer(
            instance=professor,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        