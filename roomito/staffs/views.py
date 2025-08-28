from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django.core.cache import cache
from .models import Staff
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from .serializers import (
    StaffRegisterSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    StaffProfileUpdateSerializer,
    StaffProfileSerializer
)

@extend_schema(tags=['auth'])
class StaffRegisterView(APIView):
    @extend_schema(
        request=StaffRegisterSerializer,
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
                description="Validation error",
                examples=[
                    OpenApiExample(
                        name="MissingField",
                        value={"first_name": ["This field is required."]}
                    ),
                    OpenApiExample(
                        name="MissingField",
                        value={"last_name": ["This field is required."]}
                    ),
                    OpenApiExample(
                        name="InvalidNationalId",
                        value={"national_id": ["National ID must be exactly 10 digits."]}
                    ),
                    OpenApiExample(
                        name="InvalidPersonnelCode",
                        value={"personnel_code": ["Personnel code cannot be more than 10 characters."]}
                    ),
                    OpenApiExample(
                        name="InvalidEmail",
                        value={"email": ["Enter a valid email address."]}
                    ),
                    OpenApiExample(
                        name="DuplicatePersonnelCode",
                        value={"personnel_code": ["This personnel code already exists."]}
                    ),
                    OpenApiExample(
                        name="DuplicateNationalId",
                        value={"national_id": ["This national ID already exists."]}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Staff not found or email mismatch",
                examples=[
                    OpenApiExample(
                        name="StaffNotFound",
                        value={"error": "Staff not found or details do not match the registered data."},
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
                    ),
                    OpenApiExample(
                        name="CacheError",
                        value={"error": "Failed to store temporary password in cache."},
                    )
                ]
            )
        },
        description="Staff registration by University email and etc."
    )
    def post(self, request):
        serializer = StaffRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            staff = Staff.objects.get(
                first_name__iexact=data['first_name'].strip(),
                last_name__iexact=data['last_name'].strip(),
                email__iexact=data['email'],
                is_registered=False
            )
        except Staff.DoesNotExist:
            return Response({"error": "Staff not found or details do not match the registered data."}, status=status.HTTP_404_NOT_FOUND)

        # staff.first_name = data['first_name']
        # staff.last_name = data['last_name']
        staff.personnel_code = data['personnel_code']
        staff.national_id = data['national_id']
        staff.is_registered = True
        staff.save()

        temp_password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyz!@#$%^&*')

        try:
            cache.set(f"staff_tmp_pass_{staff.personnel_code}", temp_password)
        except Exception:
            return Response({"error": "Failed to store temporary password in cache."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            send_mail(
                subject="رمز موقت ثبت‌نام کارمند در رومیتو",
                message=f"کارمند گرامی {staff.first_name} {staff.last_name}،\nبه رومیتو خوش آمدید\nرمز موقت شما: {temp_password}\nلطفاً پس از ورود، رمز عبور خود را تغییر دهید.",
                from_email="mahyajfri37@gmail.com",
                recipient_list=[staff.email],
                fail_silently=False
            )
        except Exception:
            return Response({"error": "Failed to send verification email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "The temporary password has been sent to the email."}, status=status.HTTP_200_OK)


@extend_schema(tags=['staff'])
class StaffProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StaffProfileUpdateSerializer,
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
                        name="DuplicatePersonnelCode",
                        value={"personnel_code": ["This personnel code is already in use."]}
                    ),
                    OpenApiExample(
                        name="DuplicateNationalId",
                        value={"national_id": ["This national ID is already in use."]}
                    ),
                    OpenApiExample(
                        name="InvalidNationalId",
                        value={"national_id": ["National ID must be exactly 10 digits."]}
                    ),
                    OpenApiExample(
                        name="InvalidPersonnelCode",
                        value={"personnel_code": ["Personnel code cannot be more than 10 characters."]}
                    ),
                    OpenApiExample(
                        name="InvalidEmail",
                        value={"email": ["Enter a valid email address."]}
                    ),
                    # OpenApiExample(
                    # name="ValidationError",
                    # value={"email": ["This email is already in use."]}
                    # ),
                    OpenApiExample(
                        name="InvalidEmail",
                        value={"email": ["Enter a valid email address."]}
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
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a Staff.",
                examples=[
                    OpenApiExample(
                        name="NotStaff",
                        value={"error": "User is not a Staff."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error while updating profile.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred while updating profile."}
                    )
                ]
            )
        },
        description="Update profile informations of the authenticated Staff."
    )
    def patch(self, request):
        user = request.user
        try:
            staff = user.staff
        except Staff.DoesNotExist:
            return Response({"error": "User is not a Staff."}, status=status.HTTP_403_FORBIDDEN)

        if staff.user is None:
            return Response({"error": "This staff profile is not linked to a user account."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = StaffProfileUpdateSerializer(
            instance=staff,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_staff = serializer.save()

        if serializer.validated_data.get("new_password"):
            update_session_auth_hash(request, updated_staff.user)

        return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
    
    
@extend_schema(tags=['staff'])
class StaffProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Staff profile retrieved successfully.",
                examples=[
                    OpenApiExample(
                        name="StaffProfileExample",
                        value={
                            "first_name": "string",
                            "last_name": "string",
                            "email": "string@example.com",
                            "personnel_code": "string",
                            "national_id": "string"
                        },
                        response_only=True
                    )
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
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a Staff.",
                examples=[
                    OpenApiExample(
                        name="NotStaff",
                        value={"error": "User is not a staff."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=None,
                description="Server error while retrieving profile.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred while retrieving profile."}
                    )
                ]
            )
        },
        description="Retrieves the authenticated Staff's profile."
    )
    def get(self, request):
        user = request.user

        try:
            staff = user.staff
        except Staff.DoesNotExist:
            return Response({"error": "User is not a staff."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StaffProfileSerializer(staff)
        return Response(serializer.data, status=status.HTTP_200_OK)        