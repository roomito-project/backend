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
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    ProfessorProfileUpdateSerializer,
    ProfessorProfileSerializer
)

@extend_schema(tags=['auth'])
class ProfessorRegisterView(APIView):
    @extend_schema(
        request=ProfessorRegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Successful registration",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={"message": "The temporary password has been sent to the email."},
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="validation error",
                examples=[
                    OpenApiExample(
                        "Invalid National ID",
                        value={"national_id": ["National ID must be exactly 10 digits."]}
                    ),
                    OpenApiExample(
                        "Invalid Personnel Code",
                        value={"personnel_code": ["Personnel code cannot be more than 10 characters."]}
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
                description="Server error while sending email",
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
                first_name__iexact=data['first_name'].strip(),
                last_name__iexact=data['last_name'].strip(),
                email__iexact=data['email'],
                is_registered=False
            )
        except Professor.DoesNotExist:
            return Response({"error": "Professor not found or details do not match the registered data."}, status=status.HTTP_404_NOT_FOUND)

        # professor.first_name = data['first_name']
        # professor.last_name = data['last_name']
        professor.personnel_code = data['personnel_code']
        professor.national_id = data['national_id']
        # professor.is_registered = True
        professor.save()

        temp_password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyz!@#$%^&*')

        cache.set(f"prof_tmp_pass_{professor.personnel_code}", temp_password)

        try:
            send_mail(
                subject="رمز موقت ثبت‌نام استاد در رومیتو",
                message=f"استاد گرامی {professor.first_name} {professor.last_name}،\nبه رومیتو خوش آمدید\nرمز موقت شما: {temp_password}\nلطفاً پس از ورود، رمز عبور خود را تغییر دهید.",
                from_email="mahyajfri37@gmail.com",
                recipient_list=[professor.email],
                fail_silently=False
            )
        except Exception:
            return Response({"error": "Failed to send verification email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "The temporary password has been sent to the email."}, status=status.HTTP_200_OK)


@extend_schema(tags=['professor'])
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
                # OpenApiExample(
                #     name="ValidationError",
                #     value={"email": ["This email is already in use."]}
                # ),
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
        

@extend_schema(tags=['professor'])
class ProfessorProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=ProfessorProfileSerializer,
                description="Professor profile retrieved successfully",
                examples=[
                    OpenApiExample(
                        "ProfessorProfileExample",
                        value={
                            "first_name": "string",
                            "last_name": "string",
                            "email": "string@example",
                            "personnel_code": "string",
                            "national_id": "string"
                        },
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a professor",
                examples=[
                    OpenApiExample(
                        "NotProfessor",
                        value={"error": "User is not a professor."},
                        response_only=True
                    )
                ]
            )
        },
        description="Retrieves the authenticated professor's profile"
    )
    def get(self, request):
        user = request.user

        if not hasattr(user, 'professor'):
            return Response({"error": "User is not a professor."}, status=status.HTTP_403_FORBIDDEN)

        professor = user.professor
        serializer = ProfessorProfileSerializer(professor)
        return Response(serializer.data, status=status.HTTP_200_OK)
        