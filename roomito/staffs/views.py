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
from django.db import transaction
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from staffs.models import Staff
from .serializers import StaffRegisterSerializer, SuccessResponseSerializer, ErrorResponseSerializer


def _norm(s: str) -> str:
    return (s or "").strip()


@extend_schema(tags=['auth'])
class StaffRegisterView(APIView):
    @extend_schema(
        request=StaffRegisterSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Successful registration",
                examples=[OpenApiExample(
                    name="Success",
                    value={"message": "The temporary password has been sent to the email."},
                )],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation error",
                examples=[
                    OpenApiExample(name="MissingField", value={"first_name": ["This field is required."]}),
                    OpenApiExample(name="MissingField", value={"last_name": ["This field is required."]}),
                    OpenApiExample(name="InvalidNationalId", value={"national_id": ["National ID must be exactly 10 digits."]}),
                    OpenApiExample(name="InvalidPersonnelCode", value={"personnel_code": ["Personnel code cannot be more than 10 characters."]}),
                    OpenApiExample(name="InvalidEmail", value={"email": ["Enter a valid email address."]}),
                    OpenApiExample(name="DuplicatePersonnelCode", value={"personnel_code": ["This personnel code already exists."]}),
                    OpenApiExample(name="DuplicateNationalId", value={"national_id": ["This national ID already exists."]}),
                    OpenApiExample(name="AlreadyRegistered", value={"error": "This staff is already registered."}),
                ],
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Staff not found or email/name mismatch",
                examples=[OpenApiExample(
                    name="StaffNotFound",
                    value={"error": "Staff not found or details do not match the registered data."},
                )],
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error while sending email or persisting data",
                examples=[
                    OpenApiExample(name="EmailSendError", value={"error": "Failed to send verification email."}),
                    OpenApiExample(name="AccountConflict", value={"error": "Account conflict. Contact admin."}),
                ],
            ),
        },
        description="Staff registration via university email + personnel code. Creates/updates the User(username=personnel_code), sets a temporary password, links Staff→User, emails the password."
    )
    @transaction.atomic
    def post(self, request):
        serializer = StaffRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        first_name = _norm(data.get('first_name'))
        last_name  = _norm(data.get('last_name'))
        email      = _norm(data.get('email')).lower()
        personnel_code = _norm(data.get('personnel_code'))
        national_id    = _norm(data.get('national_id'))

        staff = Staff.objects.filter(email__iexact=email, is_registered=False).first()
        if staff is None:
            return Response({"error": "Staff not found or details do not match the registered data."},
                            status=status.HTTP_404_NOT_FOUND)

        if _norm(staff.first_name).lower() != first_name.lower() or _norm(staff.last_name).lower() != last_name.lower():
            return Response({"error": "Staff not found or details do not match the registered data."},
                            status=status.HTTP_404_NOT_FOUND)

        if Staff.objects.filter(personnel_code=personnel_code).exclude(pk=staff.pk).exists():
            return Response({"personnel_code": ["This personnel code already exists."]},
                            status=status.HTTP_400_BAD_REQUEST)

        if national_id:
            if Staff.objects.filter(national_id=national_id).exclude(pk=staff.pk).exists():
                return Response({"national_id": ["This national ID already exists."]},
                                status=status.HTTP_400_BAD_REQUEST)

        existing_user = User.objects.filter(username=personnel_code).first()
        if existing_user and (not staff.user_id or staff.user_id != existing_user.id):
            return Response({"error": "Account conflict. Contact admin."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        temp_password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*')

        user = staff.user
        if user is None:
            if existing_user:
                return Response({"error": "Account conflict. Contact admin."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            user = User.objects.create_user(
                username=personnel_code,
                password=temp_password,
                first_name=staff.first_name,
                last_name=staff.last_name,
                email=staff.email,
            )
        else:
            if user.username != personnel_code:
                if existing_user and existing_user.id != user.id:
                    return Response({"error": "Account conflict. Contact admin."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                user.username = personnel_code
            user.set_password(temp_password)
            user.first_name = staff.first_name
            user.last_name  = staff.last_name
            user.email      = staff.email
            user.save()

        staff.personnel_code = personnel_code
        staff.national_id = national_id
        staff.user = user
        staff.is_registered = True
        staff.save(update_fields=['personnel_code', 'national_id', 'user', 'is_registered'])

        try:
            cache.set(f"staff_password_{personnel_code}", temp_password, timeout=3600*24)  # 24h
            cache.set(f"staff_tmp_pass_{personnel_code}", temp_password, timeout=3600*24)
        except Exception:
            pass

        try:
            send_mail(
                subject="رمز موقت ثبت‌نام کارمند",
                message=(
                    f"{staff.first_name} {staff.last_name} عزیز،\n\n"
                    f"ثبت‌نام شما انجام شد.\n"
                    f"کد پرسنلی (نام کاربری): {personnel_code}\n"
                    f"رمز موقت: {temp_password}\n\n"
                    f"لطفاً پس از ورود، رمز خود را تغییر دهید."
                ),
                from_email="no-reply@your-domain.tld",
                recipient_list=[staff.email],
                fail_silently=False,
            )
        except Exception:
            return Response({"warning": "Registered, but failed to send email. Contact support if needed."},
                            status=status.HTTP_200_OK)

        return Response({"message": "The temporary password has been sent to the email."},
                        status=status.HTTP_200_OK)


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