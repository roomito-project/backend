from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.throttling import ScopedRateThrottle
from .models import Professor
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    ProfessorRegisterSerializer,
    ProfessorVerifySerializer,
    ProfessorLoginSerializer,
    ErrorResponseSerializer,
    ResendVerificationSerializer,
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
                examples=[OpenApiExample(
                    "RegistrationSuccess",
                    value={"message": "The verification code has been sent to the email."},
                    response_only=True
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid registration data",
                examples=[OpenApiExample(
                    "InvalidData",
                    value={"error": "Invalid data provided."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Professor not found",
                examples=[OpenApiExample(
                    "ProfessorNotFound",
                    value={"error": "Professor not found or already registered."},
                    response_only=True
                )]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Email sending failed",
                examples=[OpenApiExample(
                    "EmailSendError",
                    value={"error": "Failed to send verification email."},
                    response_only=True
                )]
            ),
        },
        description="Professor registration"
    )
    def post(self, request):
        serializer = ProfessorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            professor = Professor.objects.get(email=data['email'], is_registered=False)
        except Professor.DoesNotExist:
            return Response({"error": "Professor not found or already registered."}, status=status.HTTP_404_NOT_FOUND)

        code = get_random_string(length=6, allowed_chars='0123456789')
        professor.first_name = data['first_name']
        professor.last_name = data['last_name']
        professor.national_id = data['national_id']
        professor.personnel_code = data['personnel_code']
        professor.verification_code = code
        professor.save()
        cache.set(f"professor_password_{data['personnel_code']}", data['password'], timeout=600)


        try:
            send_mail(
                subject="کد تأیید ثبت‌نام در رومیتو",
                message=f"کد تأیید شما: {code}",
                from_email="mahyajfri37@example.com",
                recipient_list=[professor.email],
                fail_silently=False
            )
        except Exception:
            return Response({"error": "Failed to send verification email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "The verification code has been sent to the email."}, status=status.HTTP_200_OK)


class ProfessorVerifyView(APIView):
    @extend_schema(
        request=ProfessorVerifySerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Verification successful",
                examples=[OpenApiExample(
                    "VerificationSuccess",
                    value={"message": "The professor has been successfully registered."},
                    response_only=True
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid verification code or already registered",
                examples=[OpenApiExample(
                    "InvalidCode",
                    value={"error": "The verification code is incorrect."},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Professor not found",
                examples=[OpenApiExample(
                    "NotFound",
                    value={"error": "The professor could not be found."},
                    response_only=True
                )]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User creation failed",
                examples=[OpenApiExample(
                    "UserCreationFailure",
                    value={"error": "Failed to create user account."},
                    response_only=True
                )]
            ),
        },
        description="Professor verification using personnel code and verification code"
    )
    def post(self, request):
        serializer = ProfessorVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        personnel_code = serializer.validated_data['personnel_code']
        code = serializer.validated_data['verification_code']

        try:
            professor = Professor.objects.get(personnel_code=personnel_code)
        except Professor.DoesNotExist:
            return Response({"error": "The professor could not be found."}, status=404)

        if professor.verification_code != code:
            return Response({"error": "The verification code is incorrect."}, status=400)

        if professor.is_registered:
            return Response({"error": "This professor has registered before."}, status=400)
        
        password = cache.get(f"professor_password_{personnel_code}")
        if not password:
            return Response({"error": "Password expired or not found. Please register again."}, status=400)

        try:
            user = User.objects.create_user(
                username=professor.personnel_code,
                password=password
            )
            professor.user = user
            professor.is_registered = True
            professor.is_verified = True
            professor.verification_code = None
            professor.save()
            cache.delete(f"professor_password_{personnel_code}")
            
        except Exception:
            return Response({"error": "Failed to create user account."}, status=500)

        return Response({"message": "The professor has been successfully registered."}, status=200)


class ProfessorLoginView(APIView):
    @extend_schema(
        request=ProfessorLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[OpenApiExample(
                    "LoginSuccess",
                    value={"access": "token_string", "refresh": "refresh_token_string"},
                    response_only=True
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid login data",
                examples=[OpenApiExample(
                    "InvalidData",
                    value={"error": "Invalid data provided."},
                    response_only=True
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized",
                examples=[OpenApiExample(
                    "UnauthorizedError",
                    value={"error": "Invalid personnel code or password."},
                    response_only=True
                )]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Token generation failed",
                examples=[OpenApiExample(
                    "TokenGenerationError",
                    value={"error": "Failed to generate token."},
                    response_only=True
                )]
            ),
        },
        description="Professor login using personnel code and password"
    )
    def post(self, request):
        serializer = ProfessorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        try:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Failed to generate token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfessorResendVerificationThrottle(SimpleRateThrottle):
    scope = 'resend_verification'

    def get_cache_key(self, request, view):
        email = request.data.get('email')
        if not email:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': email
        }


class ProfessorResendVerificationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'resend_verification'  

    @extend_schema(
        request=ResendVerificationSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Verification code resent successfully",
                examples=[
                    OpenApiExample(
                        "ResendSuccess",
                        value={"message": "A new verification code has been sent to the email."}
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Too many attempts or invalid code"
            )
        },
            description="resend verification code to professor"
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        personnel_code = serializer.validated_data['personnel_code']

        try:
            professor = Professor.objects.get(personnel_code=personnel_code, is_registered=False)
        except Professor.DoesNotExist:
            return Response({"error": "Professor not found or already registered."}, status=400)

        code = get_random_string(length=6, allowed_chars='0123456789')
        professor.verification_code = code
        professor.save()

        try:
            send_mail(
                subject="کد تأیید ثبت‌نام مجدد",
                message=f"کد تأیید جدید شما: {code}",
                from_email="mahyajfri37@gmail.com",
                recipient_list=[professor.email],
                fail_silently=False
            )
        except Exception:
            return Response({"error": "Failed to send verification email."}, status=500)

        return Response({"message": "A new verification code has been sent to the email."}, status=200)
    
    
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
        