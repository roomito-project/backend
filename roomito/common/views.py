from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from staffs.models import Staff
from students.models import Student
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from .serializers import EventDetailSerializer, MyEventListSerializer, MyEventUpdateSerializer, MyReservationDetailSerializer, ReservationUpdateSerializer, SuccessResponseSerializer, UnifiedLoginSerializer, TokenResponseSerializer, ErrorResponseSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import MyReservationListSerializer
from space_managers.models import Reservation, Event
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError as DRFValidationError
from space_managers.models import Space, Event
from .serializers import SearchResultSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample, OpenApiTypes


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
                                "manager_comment": "string",
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
                                "manager_comment": "string",
                                "reservation_type": "class",
                                "description": "string",
                                "phone_number": "09351234567"
                            }
                        ]
                    ),
                    OpenApiExample(
                        'EmptyList',
                        value={"message": "You have no reservations."}
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[OpenApiExample('Unauthorized', value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is neither student nor staff.",
                examples=[OpenApiExample('Forbidden', value={"error": "Only students or staff can view their reservations."})]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
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

        if not qs.exists():
            return Response({"message": "You have no reservations."}, status=status.HTTP_200_OK)
        
        return Response(MyReservationListSerializer(qs, many=True).data, status=status.HTTP_200_OK)
    

@extend_schema(tags=['reservation'])
class MyReservationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve a single reservation (only if it belongs to the authenticated user).",
        parameters=[
            OpenApiParameter(
                name="reservation_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
                description="Reservation ID"
            )
        ],
        responses={
            200: OpenApiResponse(
                response=MyReservationDetailSerializer,
                description="Reservation retrieved successfully.",
                examples=[OpenApiExample(
                    "Success",
                    value={
                        "id": 2,
                        "reservation_type": "event",
                        "description": "string",
                        "status_display": "Rejected",
                        "phone_number": "09123456789",
                        "manager_comment": "string",
                        "date": "2025-09-01",
                        "space": {
                                "name": "string",
                                "capacity": 50,
                                "address": "string",
                                "space_type": "hall",
                                "description": "string"
                            },
                        "hosting_association": "string",
                        "hosting_organizations": "string",
                        "responsible_organizer": "string",
                        "position": "Professor"
                    }
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not authenticated.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Reservation does not belong to the user.",
                examples=[OpenApiExample("Forbidden", value={"error": "You are not authorized to view this reservation."})]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Reservation not found.",
                examples=[OpenApiExample("NotFound", value={"error": "Reservation with this ID does not exist."})]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample("ServerError", value={"error": "An unexpected error occurred."})]
            ),
        }
    )
    def get(self, request, reservation_id):
        user = request.user
        student_id = getattr(getattr(user, 'student_profile', None), 'id', None)
        staff_id   = getattr(getattr(user, 'staff', None), 'id', None)

        try:
            reservation = (
                Reservation.objects
                .select_related('schedule', 'schedule__start_hour_code', 'schedule__end_hour_code',
                                'space', 'student__user', 'staff')
                .filter(id=reservation_id)
                .filter(
                    Q(student_id=student_id) | Q(staff_id=staff_id)
                )
                .first()
            )

            if reservation is None:
                return Response({"error": "Reservation with this ID does not exist."},
                                status=status.HTTP_404_NOT_FOUND)

            data = MyReservationDetailSerializer(reservation).data
            return Response(data, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "An unexpected error occurred."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

@extend_schema(tags=['reservation'])
class MyReservationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description=(
            "Delete a reservation created by the authenticated user (student or staff). "
        ),
        parameters=[
            OpenApiParameter(
                name="reservation_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the reservation to delete"
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Reservation deleted successfully.",
                examples=[OpenApiExample("Deleted", value={"message": "Reservation deleted successfully."})]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Reservation does not belong to the user.",
                examples=[OpenApiExample("Forbidden", value={"error": "You are not authorized to delete this reservation."})]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Reservation not found.",
                examples=[OpenApiExample("NotFound", value={"error": "Reservation with this ID does not exist."})]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample("ServerError", value={"error": "An unexpected error occurred."})]
            ),
        }
    )
    def delete(self, request, reservation_id):
        user = request.user
        student_id = getattr(getattr(user, 'student_profile', None), 'id', None)
        staff_id   = getattr(getattr(user, 'staff', None), 'id', None)

        reservation = Reservation.objects.filter(
            Q(student_id=student_id) | Q(staff_id=staff_id),
            id=reservation_id
        ).select_related('schedule').first()

        if reservation is None:
            return Response({"error": "Reservation with this ID does not exist."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                sch = reservation.schedule
                if sch:
                    Event.objects.filter(schedule=sch).delete()

                reservation.delete()

            return Response({"message": "Reservation deleted successfully."}, status=200)

        except Exception:
            return Response({"error": "An unexpected error occurred."}, status=500)
        

@extend_schema(tags=['reservation'])
class MyReservationUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Update a reservation created by the authenticated user. Allowed only while status is 'under_review'. Space is NOT editable.",
        parameters=[
            OpenApiParameter(
                name="reservation_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the reservation to edit"
            ),
        ],
        request=ReservationUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Reservation updated successfully.",
                examples=[OpenApiExample("Success", value={"message": "Reservation updated successfully."})]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation error or not editable.",
                examples=[
                    OpenApiExample("NotEditable", value={"error": "Reservation is not editable."}),
                    OpenApiExample("BadPhone", value={"phone_number": ["Phone number must be exactly 11 digits."]}),
                    OpenApiExample("BadSchedule", value={"schedule": ["This reservation has no schedule to update."]}),
                    OpenApiExample("BadHourCodes", value={"hour_codes": ["Hour codes must be consecutive."]}),
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not authenticated.",
                examples=[OpenApiExample("Unauthorized", value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not owner.",
                examples=[OpenApiExample("Forbidden", value={"error": "You are not authorized to update this reservation."})]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Reservation not found.",
                examples=[OpenApiExample("NotFound", value={"error": "Reservation with this ID does not exist."})]
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Schedule time conflict.",
                examples=[OpenApiExample("Conflict", value={"error": "This time conflicts with another schedule on the same date."})]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error.",
                examples=[OpenApiExample("ServerError", value={"error": "An unexpected error occurred."})]
            ),
        }
    )
    def put(self, request, reservation_id: int):
        user = request.user
        student = getattr(user, 'student_profile', None)
        staff = getattr(user, 'staff', None)

        reservation = (
            Reservation.objects
            .select_related('schedule', 'schedule__start_hour_code', 'schedule__end_hour_code',
                            'space', 'student__user', 'staff')
            .filter(id=reservation_id)
            .filter(Q(student=student) | Q(staff=staff))
            .first()
        )
        if reservation is None:
            return Response({"error": "Reservation with this ID does not exist."},
                            status=status.HTTP_404_NOT_FOUND)

        if reservation.status != 'under_review':
            return Response({"error": "Reservation is not editable."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = ReservationUpdateSerializer(instance=reservation, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except DRFValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError:
            return Response({"error": "This time conflicts with another schedule on the same date."},
                            status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({"error": "An unexpected error occurred."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Reservation updated successfully."}, status=status.HTTP_200_OK)
    
        
@extend_schema(tags=['event'])
class MyEventsListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="List events organized by the authenticated user (student or staff).",
        responses={
            200: OpenApiResponse(
                response=MyEventListSerializer(many=True),
                description="My events retrieved successfully.",
                examples=[OpenApiExample(
                    "Success",
                    value=[{
                        "id": 10,
                        "title": "string",
                        "event_type": "event",
                        "description": "string",
                        "poster": "/media/event_posters/10.jpg",
                        "space_name": "string",
                        "date": "2025-09-05",
                        "start_time": "10:00:00",
                        "end_time": "12:00:00"
                    }]
                ),
                    OpenApiExample(
                        "EmptyList",
                        value={"message": "You have no events."}
                    )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not authenticated.",
                examples=[OpenApiExample(
                    "Unauthorized", value={"detail": "Authentication credentials were not provided."})]),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not a student/staff.",
                examples=[OpenApiExample(
                    "Forbidden", value={"error": "Only students or staff can view their events."})]),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error.",
                examples=[OpenApiExample(
                    "ServerError", value={"error": "An unexpected error occurred."})]),
        }
    )
    def get(self, request):
        try:
            user = request.user
            student = getattr(user, 'student_profile', None)
            staff   = getattr(user, 'staff', None)

            events = Event.objects.filter(
                Q(student_organizer=student) | Q(staff_organizer=staff)
            ).select_related('space', 'schedule__start_hour_code', 'schedule__end_hour_code')

            if not events.exists():
                return Response({"message": "You have no events."}, status=status.HTTP_200_OK)
            
            serializer = MyEventListSerializer(events, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=['event'])
class MyEventDetailView(APIView):
 
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve an event details owned by the authenticated user",
        parameters=[
            OpenApiParameter(
                name="event_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
                description="Event ID"
            )
        ],
        responses={
            200: OpenApiResponse(
                response=EventDetailSerializer,
                description="Event details retrieved successfully.",
                examples=[OpenApiExample(
                    "Success",
                    value={
                        "id": 11,
                        "title": "string",
                        "event_type": "class",
                        "description": "string",
                        "poster": None,
                        "organizer": "staff",
                        "organizer_display": "Staff",
                        "space": {
                            "id": 2,
                            "space_type": "class",
                            "name": "string",
                            "address": "string",
                            "capacity": 40,
                            "phone_number": "09123456789",
                            "description": "string",
                            "features": [{"id": 1, "name": "Projector"}],
                            "images": [{"id": 5, "url": "/media/space_photos/5.jpg"}]
                        },
                        "date": "2025-09-07",
                        "start_time": "14:00:00",
                        "end_time": "16:00:00"
                    }
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not authenticated.",
                examples=[OpenApiExample(
                    "Unauthorized", value={"detail": "Authentication credentials were not provided."})]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Event is not owned by the user.",
                examples=[OpenApiExample(
                    "Forbidden", value={"error": "You are not authorized to view this event."})]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Event not found.",
                examples=[OpenApiExample(
                    "NotFound", value={"error": "Event with this ID does not exist."})]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample(
                    "ServerError", value={"error": "An unexpected error occurred."})]
            ),
        }
    )
    def get(self, request, event_id):
        user = request.user
        student = getattr(user, 'student_profile', None)
        staff   = getattr(user, 'staff', None)

        if not student and not staff:
            return Response({"error": "Only students or staff can view their events."},
                            status=status.HTTP_403_FORBIDDEN)

        qs = Event.objects.select_related(
            'space',
            'schedule', 'schedule__start_hour_code', 'schedule__end_hour_code',
            'student_organizer__user', 'staff_organizer'
        ).prefetch_related(
            'space__features', 'space__images'
        )

        if student:
            qs = qs.filter(organizer='student', student_organizer=student)
        else:
            qs = qs.filter(organizer='staff', staff_organizer=staff)

        event = qs.filter(id=event_id).first()
        if event is None:
            return Response({"error": "Event with this ID does not exist."},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(EventDetailSerializer(event).data, status=status.HTTP_200_OK)


@extend_schema(tags=['event'])
class MyEventUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = MyEventUpdateSerializer
    lookup_url_kwarg = 'event_id'
    http_method_names = ['put']

    def _truthy(self, v):
        if v is None:
            return False
        return str(v).strip().lower() in {"true"}

    def get_object(self):
        event = get_object_or_404(
            Event.objects.select_related(
                'student_organizer__user', 'staff_organizer__user'
            ).filter(event_type='event'),
            id=self.kwargs[self.lookup_url_kwarg]
        )

        u = self.request.user
        is_owner = False
        if event.organizer == 'student' and getattr(event, 'student_organizer', None):
            is_owner = getattr(event.student_organizer, 'user', None) == u
        elif event.organizer == 'staff' and getattr(event, 'staff_organizer', None):
            is_owner = getattr(event.staff_organizer, 'user', None) == u

        if not is_owner:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not allowed to edit this event.")

        return event

    @extend_schema(
        tags=['event'],
        description="Update an event created by the authenticated user.",
        parameters=[OpenApiParameter(name='event_id', required=True, type=int, location=OpenApiParameter.PATH)],
        request=MyEventUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=EventDetailSerializer,
                description="Event updated successfully.",
                examples=[OpenApiExample(
                    name="Success",
                    value={
                        "id": 12,
                        "title": "کارگاه Django - ویرایش شده",
                        "event_type": "event",
                        "date": "2025-08-25",
                        "start_time": "09:00:00",
                        "end_time": "11:00:00",
                        "space_name": "تالار برآنی",
                        "poster_url": None,
                        "organizer": {"type": "staff", "id": 3, "first_name": "Ali", "last_name": "Ahmadi", "email": "ali@example.com"},
                        "contact_info": "0913xxxxxxx",
                        "registration_link": "https://example.com/register",
                        "description": "متن جدید"
                    },
                    response_only=True
                )]
            ),
            400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Validation error",
            examples=[
                OpenApiExample(name="BadURL", value={"registration_link": ["Enter a valid URL."]}, response_only=True),
                OpenApiExample(name="EmptyTitle", value={"title": ["This field may not be blank."]}, response_only=True),
                OpenApiExample(name="InvalidImage", value={"poster": ["Invalid image."]}, response_only=True),
            ]
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Unauthorized",
            examples=[OpenApiExample(
                name="Unauthorized",
                value={"detail": "Authentication credentials were not provided."},
                response_only=True
            )]
        ),
        403: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Forbidden (not owner)",
            examples=[OpenApiExample(
                name="Forbidden",
                value={"error": "You are not allowed to edit this event."},
                response_only=True
            )]
        ),
        404: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Not found or not an event",
            examples=[OpenApiExample(
                name="NotFound",
                value={"error": "Event not found or not editable (not an 'event')."},
                response_only=True
            )]
        ),
        405: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Method not allowed",
            examples=[OpenApiExample(
                name="MethodNotAllowed",
                value={"detail": "Method \"POST\" not allowed."},
                response_only=True
            )]
        ),
        415: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Unsupported media type",
            examples=[OpenApiExample(
                name="UnsupportedMediaType",
                value={"detail": "Unsupported media type \"application/json\" in request."},
                response_only=True
            )]
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Internal server error",
            examples=[OpenApiExample(
                name="ServerError",
                value={"error": "An unexpected server error occurred."},
                response_only=True
            )]
        ),
        }
    )
    def put(self, request, event_id):
        event = get_object_or_404(
            Event.objects.select_related(
                "space",
                "schedule", "schedule__start_hour_code", "schedule__end_hour_code",
                "student_organizer__user",
                "staff_organizer",
            ),
            id=event_id,
        )
        if event.event_type != 'event':
            return Response(
                {"error": "Event not found or not editable (not an 'event')."},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if event.organizer == 'student':
            owner_user = getattr(getattr(event, 'student_organizer', None), 'user', None)
        else:  
            owner_user = getattr(getattr(event, 'staff_organizer', None), 'user', None)

        if owner_user is None or owner_user != user:
            return Response(
                {"error": "You are not allowed to edit this event."},
                status=status.HTTP_403_FORBIDDEN
            )

        allowed_fields = {"title", "contact_info", "registration_link", "description"}
        for f in allowed_fields:
            if f in request.data:
                setattr(event, f, request.data.get(f))

        incoming_file = request.FILES.get('image') or request.FILES.get('poster')
        remove_flag = self._truthy(request.data.get('removeImage'))

        try:
            if incoming_file:
                if event.poster:
                    event.poster.delete(save=False)
                event.poster = incoming_file

            elif remove_flag:
                if event.poster:
                    event.poster.delete(save=False)
                event.poster = None

            event.full_clean()
            event.save()
        except Exception:
            return Response({"error": "Invalid payload."}, status=status.HTTP_400_BAD_REQUEST)

        data = EventDetailSerializer(event, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Search spaces and events by a query string.",
        parameters=[
            OpenApiParameter(
                name='search',
                required=True,
                type=OpenApiTypes.STR,
                description="Query string to search in Space.name and Event.title",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SearchResultSerializer(many=True),
                description="Search results returned successfully.",
                examples=[
                    OpenApiExample(
                        name="SuccessExample",
                        value=[
                            {"type": "space", "id": 1, "title": "تالار برآنی"},
                            {"type": "event", "id": 7, "title": "کارگاه Django"},
                        ],
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid request (e.g., missing/invalid query).",
                examples=[
                    OpenApiExample(
                        name="MissingQuery",
                        value={"error": "Search query parameter 'search' is required."},
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="TooShort",
                        value={"error": "Search query must be at least 2 characters long."},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Authentication required.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"detail": "Authentication credentials were not provided."},
                        response_only=True,
                    )
                ],
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="No matching spaces or events found.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "No results found for the given query."},
                        response_only=True,
                    )
                ],
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."},
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to query database."},
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        q = (request.query_params.get('search') or '').strip()
        if not q:
            return Response(
                {"error": "Search query parameter 'search' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(q) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters long."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            spaces_qs = Space.objects.filter(name__icontains=q).values('id', 'name')
            space_results = [{"type": "space", "id": s["id"], "title": s["name"]} for s in spaces_qs]

            events_qs = Event.objects.filter(title__icontains=q).values('id', 'title')
            event_results = [{"type": "event", "id": e["id"], "title": e["title"]} for e in events_qs]

            combined = space_results + event_results

            if not combined:
                return Response(
                    {"error": "No results found for the given query."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            q_lower = q.lower()
            def sort_key(item):
                title = (item.get("title") or "").lower()
                starts = title.startswith(q_lower)
                return (0 if starts else 1, title)

            combined.sort(key=sort_key)
            return Response(combined, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
