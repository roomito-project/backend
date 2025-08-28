from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from staffs.models import Staff
from students.models import Student
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import UnifiedLoginSerializer, TokenResponseSerializer, ErrorResponseSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import MyReservationListSerializer
from space_managers.models import Reservation


@extend_schema(tags=['auth'])
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
                        value={"access": "access_token", "refresh": "refresh_token", "role": "staff"},
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
                        value={"error": "Invalid role. Must be one of: staff, student, space_manager."},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized – invalid credentials or account status",
                examples=[
                    OpenApiExample(
                        "InvalidCredentials", 
                        value={"error": "Invalid credentials."}, 
                        response_only=True),
                    OpenApiExample(
                        "StudentNotApproved", 
                        value={"error": "Your student card is not yet approved."}, 
                        response_only=True),
                    OpenApiExample(
                        "NotSpaceManager", 
                        value={"error": "User is not a space manager."}, 
                        response_only=True),
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal Server Error – token generation failed",
                examples=[
                    OpenApiExample(
                        "TokenGenerationError", 
                        value={"error": "Failed to generate token."}, 
                        response_only=True)
                ]
            )
        },
        description="Unified login for staffs, students, and space managers (use personnel code for staff and student id for student as usernames)."
    )
    def post(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        role = (serializer.validated_data['role'] or '').strip().lower()
        username = (serializer.validated_data['username'] or '').strip()
        password = serializer.validated_data['password'] 
    
        try:
            if role == 'staff':
                try:
                    staff = Staff.objects.get(personnel_code=username)
                except Staff.DoesNotExist:
                    return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                user = staff.user

                if user is None:
                    cached_pw = cache.get(f"staff_password_{staff.email}") or \
                                cache.get(f"staff_password_{staff.personnel_code}") or \
                                cache.get(f"staff_tmp_pass_{staff.personnel_code}")

                    if not cached_pw or cached_pw != password:
                        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

                    user = User.objects.create_user(
                        username=staff.personnel_code,
                        password=password,
                        first_name=staff.first_name,
                        last_name=staff.last_name,
                        email=staff.email,
                    )
                    staff.user = user
                    staff.is_registered = True
                    staff.save(update_fields=['user', 'is_registered'])

                    cache.delete(f"staff_password_{staff.email}")
                    cache.delete(f"staff_password_{staff.personnel_code}")
                    cache.delete(f"prof_tmp_pass_{staff.personnel_code}")

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
                    {"error": "Invalid role. Must be one of: staff, student, space_manager."},
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


@extend_schema(tags=['reservation'])
class MyReservationsListView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve all reservation requests created by the authenticated user (student or staff).",
        responses={
            200: OpenApiResponse(
                response=MyReservationListSerializer(many=True),
                description="List of user's reservations retrieved successfully.",
                examples=[
                    OpenApiExample(
                        'SuccessExample',
                        value=[
                            {
                                "id": 5,
                                "space_name": "string",
                                "date": "2025-09-01",
                                "start_time": "09:00:00",
                                "end_time": "11:00:00",
                                "status_display": "Under Review",
                                "reservation_type": "event",
                                "description": "string",
                                "phone_number": "09123456789"
                            },
                            {
                                "id": 6,
                                "space_name": "string",
                                "date": "2025-09-02",
                                "start_time": "14:00:00",
                                "end_time": "16:00:00",
                                "status_display": "Approved",
                                "reservation_type": "class",
                                "description": "string",
                                "phone_number": "09351234567"
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="User is not authenticated.",
                examples=[OpenApiExample('Unauthorized', value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                description="User is neither student nor staff.",
                examples=[OpenApiExample('Forbidden', value={"error": "Only students or staff can view their reservations."})]
            ),
            500: OpenApiResponse(
                description="Unexpected server error.",
                examples=[OpenApiExample('ServerError', value={"error": "An unexpected error occurred."})]
            ),
        }
    )
    def get(self, request):
        user = request.user

        if hasattr(user, 'student_profile') and user.student_profile is not None:
            qs = Reservation.objects.filter(student=user.student_profile)
        elif hasattr(user, 'staff') and user.staff is not None:
            qs = Reservation.objects.filter(staff=user.staff)
        else:
            return Response({"error": "Only students or staff can view their reservations."},
                            status=status.HTTP_403_FORBIDDEN)

        qs = qs.select_related(
            'schedule', 'schedule__start_hour_code', 'schedule__end_hour_code',
            'space', 'student__user', 'staff'
        ).order_by('-schedule__date', '-id')

        return Response(MyReservationListSerializer(qs, many=True).data, status=status.HTTP_200_OK)