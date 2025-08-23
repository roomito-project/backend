from django.http import Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from .models import HourSlot, Reservation, Schedule, Space, Event, SpaceFeature, ReservationNotification, SpaceImage, SpaceManager
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from .serializers import (
    ErrorResponseSerializer,
    ManagerSpaceDetailSerializer,
    ManagerSpaceListSerializer,
    ScheduleAvailabilitySerializer,
    SpaceSerializer,
    SpaceUpdateFeatureSerializer,
    SpaceUpdateSerializer,
    SuccessResponseSerializer,
    SpaceManagerProfileSerializer,
    SpaceListSerializer,
    EventSerializer,
    EventDetailSerializer,
    SpaceManagerProfileUpdateSerializer,
    SpaceFeatureSerializer,
    SpaceUpdateFeatureSerializer,
    ReservationCreateSerializer,
    ReservationListSerializer,
    SpaceCreateSerializer,
    FeatureIdsSerializer
)

class IsSpaceManagerUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and hasattr(request.user, 'spacemanager')
    

@extend_schema(tags=['space_manager'])
class SpaceManagerProfileView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=SpaceManagerProfileSerializer,
                description="Space manager profile retrieved successfully.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "first_name": "string",
                            "last_name": "string",
                            "email": "string@example.com",
                            "username": "string"
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
                description="User is not a space manager.",
                examples=[
                    OpenApiExample(
                        name="NotSpaceManager",
                        value={"error": "User is not a space manager."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error while retrieving profile.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred while retrieving profile."}
                    )
                ]
            )
        },
        description="Retrieves the authenticated space manager's profile."
    )
    def get(self, request):
        user = request.user

        if not hasattr(user, 'spacemanager'):
            return Response({"error": "User is not a space manager."}, status=status.HTTP_403_FORBIDDEN)

        manager = user.spacemanager
        serializer = SpaceManagerProfileSerializer(manager)
        return Response(serializer.data, status=status.HTTP_200_OK)  
    

@extend_schema(tags=['space_manager'])    
class SpaceManagerProfileUpdateView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        request=SpaceManagerProfileUpdateSerializer,
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
                        name="DuplicateUsername",
                        value={"username": ["This username is already in use."]}
                    ),
                    # OpenApiExample( 
                    #     name="DuplicateEmail",
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
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a space manager.",
                examples=[
                    OpenApiExample(
                        name="NotSpaceManager",
                        value={"error": "User is not a space manager."}
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
        description="Update profile information of the authenticated space manager."
    )    
    
    def patch(self, request):
        spaceManager = request.user.spacemanager
        serializer = SpaceManagerProfileUpdateSerializer(
            instance=spaceManager,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

@extend_schema(tags=['space'])      
class SpaceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='space_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter spaces by type',
                required=False,
                enum=['hall', 'class', 'labratory', 'office'] 
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SpaceListSerializer(many=True),
                description="List of all available spaces with details.",
                examples=[
                    OpenApiExample(
                        name="RetrieveSpaceListSuccess",
                        value=[
                            {
                                "id": 1,
                                "space_type": "hall",
                                "name": "string",
                                "address": "string",
                                "capacity": 50,
                                "description": "string",
                                "space_manager": {
                                    "first_name": "string",
                                    "last_name": "string",
                                    "email": "string@example.com",
                                    "username": "string",
                                },
                                "first_image_url": "http://localhost:8000/media/space_photos/1.jpg"
                            }
                        ],
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="No spaces found in the database.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "No spaces available."},
                        response_only=True
                    ),
                    OpenApiExample(
                        name="InvalidSpaceType",
                        value={"error": "No spaces found for the specified space type."}  # اگه `space_type` نامعتبر باشه
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[
                    OpenApiExample(
                        name="ServerErrorExample",
                        value={"error": "An unexpected error occurred."}
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to retrieve space data from database."}
                    )
                ]
            )
        },
        description="Retrieves the list of all available spaces for authenticated users."
    )
    
    def get(self, request):
        space_type = request.query_params.get('space_type', None)

        qs = Space.objects.select_related("space_manager", "space_manager__user").prefetch_related("images").order_by("id")

        if space_type:
            qs = qs.filter(space_type=space_type)

        if not qs.exists():
            return Response({"error": "No spaces available."}, status=status.HTTP_404_NOT_FOUND)

        data = SpaceListSerializer(qs, many=True, context={'request': request}).data
        return Response(data, status=status.HTTP_200_OK)
    

@extend_schema(tags=['event'])      
class EventListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=EventSerializer(many=True),
                description="List of all available events with details.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value=[
                            {
                                "id": 1,
                                "title": "string",
                                "event_type": "string",
                                "date": "2025-07-27",
                                "start_time": "02:48:04.892Z",
                                "end_time": "02:48:04.892Z",
                                "space": {"id": 1, "space_type": "string", "name": "string", "address": "string", "capacity": 50},
                                "poster": "string.jpg",
                                "organizer": "staff",
                                "student": None,
                                "staff": {"first_name": "string", "last_name": "string", "email": "string@example.com"},
                                "description": "string"
                            }
                        ],
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Data inconsistency detected (e.g., missing organizer).",
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        value={"error": "Invalid event data."},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="No events found in the database.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "No events available."},
                        response_only=True
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error while retrieving events.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected server error occurred."},
                        response_only=True
                    )
                ]
            )
        },
        description="Retrieves the list of all available events for authenticated users."
    )

    def get(self, request):
        try:
            events = Event.objects.all()
            if not events.exists():
                return Response({"error": "No events available."}, status=status.HTTP_404_NOT_FOUND)

            serializer = EventSerializer(events, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "An unexpected server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
  
  
@extend_schema(tags=['event'])      
class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="event_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=EventDetailSerializer,
                description="Detailed event data retrieved successfully.",
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Event not found.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "Event with this ID does not exist."},
                        response_only=True,
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error while retrieving events.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected server error occurred."},
                        response_only=True
                    )
                ]
            )
        },
        description="Retrieves detailed information of a specific event by ID for authenticated user."
    )

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event with this ID does not exist."}, status=404)
        except Exception:
            return Response({"error": "An unexpected server error occurred."}, status=500)

        serializer = EventDetailSerializer(event)
        return Response(serializer.data, status=200)


@extend_schema(tags=['space_manager'])
class SpaceFeatureView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Retrieves the available features for a space managed by the authenticated space manager.",
        request=None,
        responses={
            200: OpenApiResponse(
                response=SpaceFeatureSerializer(many=True), 
                description="Space features retrieved successfully.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value=[
                            {"id": 1, "name": "string1"},
                            {"id": 2, "name": "string2"}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated or not a space manager.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."}
                    ),
                    OpenApiExample(
                        name="NotSpaceManager",
                        value={"error": "User is not a space manager."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found or user is not the manager.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "Space not found or you are not authorized to manage it."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."}
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to retrieve feature data from database."}
                    )
                ]
            )
        }
    )
    def get(self, request, space_id):
        try:
            space = get_object_or_404(Space, id=space_id, space_manager__user=request.user)
            current_features = space.features.all() 
            all_features = SpaceFeature.objects.all() 
            available_features = all_features.exclude(id__in=current_features.values('id'))

            return Response(
                SpaceFeatureSerializer(available_features, many=True).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

@extend_schema(tags=['space_manager'])
class SpaceUpdateFeatureView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Allows a space manager to add existing features to a space using their IDs.",
        request=FeatureIdsSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Features updated successfully.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "message": "Features updated successfully.",
                            "updated_features": ["string1", "string2"]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid data or no feature IDs provided.",
                examples=[
                    OpenApiExample(
                        name="InvalidData",
                        value={"error": "No feature IDs provided."}
                    ),
                    OpenApiExample(
                        name="InvalidFormat",
                        value={"feature_ids": ["A valid list of integers is required."]}  
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found, user is not the manager, or feature ID is invalid.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "Space not found or you are not authorized to manage it."}
                    ),
                    OpenApiExample(
                        name="InvalidFeature",
                        value={"error": "One or more feature IDs are invalid: [999]"}
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated or not a space manager.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."}
                    ),
                    OpenApiExample(
                        name="NotSpaceManager",
                        value={"error": "User is not a space manager."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."}
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to update features in database."}
                    )
                ]
            )
        }
    )
    def post(self, request, space_id):
        space = get_object_or_404(Space, id=space_id, space_manager__user=request.user)
        
        serializer = FeatureIdsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        feature_ids = serializer.validated_data['feature_ids']

        invalid_features = [fid for fid in feature_ids if not SpaceFeature.objects.filter(id=fid).exists()]
        if invalid_features:
            return Response
                        
                        
@extend_schema(tags=['reservation'])
class ReservationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a reservation request for a specific space by authenticated user (student or staff) with a list of consecutive hour codes.",
        request=ReservationCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=ReservationCreateSerializer,
                description="Reservation request created successfully and sent to space manager for review."
            ),

            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid data provided (serializer-level validation).",
                examples=[
                    OpenApiExample(
                        name="DuplicateHours",
                        value={"schedule": {"hour_codes": ["Duplicate hour codes are not allowed."]}}
                    ),
                    OpenApiExample(
                        name="NonAscending",
                        value={"schedule": {"hour_codes": ["Hour codes must be in ascending order."]}}
                    ),
                    OpenApiExample(
                        name="NonConsecutive",
                        value={"schedule": {"hour_codes": ["Hour codes must be consecutive."]}}
                    ),
                    OpenApiExample(
                        name="InvalidPhoneNumber",
                        value={"phone_number": ["Phone number must be exactly 11 digits."]}
                    ),
                    OpenApiExample(
                        name="MissingField",
                        value={"reservation_type": ["This field is required."]}
                    ),
                    OpenApiExample(
                        name="WrongTypeForHourCodes",
                        value={"schedule": {"hour_codes": { "0": ["Incorrect type. Expected pk value, received str."]}}}
                    ),
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Authenticated but not allowed to perform this action.",
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={"detail": "You do not have permission to perform this action."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found with the given ID.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "Space not found."}
                    )
                ]
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Time conflict with existing reservations on the same date/space.",
                examples=[
                    OpenApiExample(
                        name="Conflict",
                        value={"error": "This time conflicts with another schedule on the same date."}
                    )
                ]
            ),
            422: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unprocessable entity (e.g., invalid reservation/reservee type, role mismatch).",
                examples=[
                    OpenApiExample(
                        name="InvalidReservationType",
                        value={"reservation_type": ["Invalid reservation type."]}
                    ),
                    OpenApiExample(
                        name="InvalidReserveeType",
                        value={"reservee_type": ["You must be a student or staff to create a reservation."]}
                    ),
                    OpenApiExample(
                        name="RoleMismatch",
                        value={"error": "For the staff reservee type, you must select a staff."}
                    ),
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error (database/mail/unexpected).",
                examples=[
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Database connection failed."}
                    ),
                    OpenApiExample(
                        name="EmailError",
                        value={"error": "Failed to send reservation request to space manager."}
                    ),
                    OpenApiExample(
                        name="UnexpectedError",
                        value={"error": "An unexpected error occurred."}
                    )
                ]
            ),
        }
    )
    def post(self, request, space_id):
        space = get_object_or_404(Space, id=space_id)
        serializer = ReservationCreateSerializer(
            data=request.data,
            context={'request': request, 'space': space}
        )
        try:
            serializer.is_valid(raise_exception=True)
            reservation = serializer.save()
        except DjangoValidationError as e:
            return Response({"error": e.message if hasattr(e, "message") else e.messages[0]},
                            status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if space.space_manager and space.space_manager.email:
            try:
                send_mail(
                    subject='درخواست رزرو جدید',
                    message=(
                        f'درخواستی جدید برای رزرو {space.name} در تاریخ {reservation.schedule.date} '
                        f'از {reservation.schedule.start_hour_code.time_range} تا '
                        f'{reservation.schedule.end_hour_code.time_range} ثبت شده است.'
                    ),
                    from_email="mahyajfri37@gmail.com",
                    recipient_list=[space.space_manager.email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({"error": f"Failed to send reservation request to space manager: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            ReservationCreateSerializer(reservation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .models import Reservation, Space, SpaceManager

# ====== Serializer ======

class ReservationListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    date = serializers.DateField(source='schedule.date', read_only=True)
    # این دو فیلد را از HourSlot.time_range استخراج می‌کنیم
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reservee_name = serializers.SerializerMethodField()
    reservee_type = serializers.SerializerMethodField()
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'space_name',
            'date',
            'start_time',
            'end_time',
            'status_display',
            'reservation_type',
            'description',
            'reservee_name',
            'reservee_type',
            'phone_number',
        ]

    # ---- helpers ----
    def _parse_time_range(self, time_range_str, pick='start'):
        """
        time_range_str مثل '07:00-08:00'
        خروجی: '07:00:00' یا '08:00:00'
        """
        if not time_range_str or '-' not in time_range_str:
            return None
        parts = time_range_str.split('-')
        val = parts[0] if pick == 'start' else parts[-1]
        # نرمال‌سازی به HH:MM:SS
        if len(val) == 5:  # 'HH:MM'
            return f"{val}:00"
        return val  # اگر قبلاً 'HH:MM:SS' بود

    def get_start_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'start_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='start')

    def get_end_time(self, obj):
        slot = getattr(getattr(obj, 'schedule', None), 'end_hour_code', None)
        return self._parse_time_range(getattr(slot, 'time_range', None), pick='end')

    def get_reservee_name(self, obj):
        # با توجه به مدل‌های شما: Student معمولاً به User وصل است
        if obj.student and getattr(obj.student, 'user', None):
            return f"{obj.student.user.first_name} {obj.student.user.last_name}".strip() or "unknown"
        if obj.staff:
            # اگر Staff مستقیماً نام و نام‌خانوادگی دارد
            full = f"{obj.staff.first_name} {obj.staff.last_name}".strip()
            return full or "unknown"
        return "unknown"

    def get_reservee_type(self, obj):
        if obj.student:
            return "student"
        if obj.staff:
            return "staff"
        return "unknown"


@extend_schema(tags=['space_manager'])
class ManagerReservationListView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Retrieve the list of reservation requests for spaces managed by the authenticated space manager.",
        responses={
            200: OpenApiResponse(
                response=ReservationListSerializer(many=True),
                description="List of reservation requests successfully retrieved.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value=[
                            {
                                "id": 1,
                                "space_name": "string",
                                "date": "2025-08-15",
                                "start_time": "09:00:00",
                                "end_time": "11:00:00",
                                "status_display": "Under Review",
                                "reservation_type": "event",
                                "description": "string",
                                "reservee_name": "string",
                                "reservee_type": "student",
                                "phone_number": "09123456789"
                            }
                        ]
                    ),
                    OpenApiExample(
                        name="NoReservations",
                        value=[]
                    ),
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a space manager or has no managed spaces.",
                examples=[
                    OpenApiExample(
                        name="Forbidden_NotManager",
                        value={"error": "You are not authorized to view this list."}
                    ),
                    OpenApiExample(
                        name="Forbidden_NoManagedSpaces",
                        value={"error": "You do not manage any spaces."}
                    ),
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."}
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to retrieve reservation data from database."}
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        try:
            space_manager = user.spacemanager
        except SpaceManager.DoesNotExist:
            return Response({"error": "You are not authorized to view this list."},
                            status=status.HTTP_403_FORBIDDEN)

        managed_spaces = Space.objects.filter(space_manager=space_manager)

        if not managed_spaces.exists():
            return Response([],
                            status=status.HTTP_200_OK)

        reservations = (
            Reservation.objects
            .filter(space__in=managed_spaces)
            .select_related(
                'space',
                'schedule',
                'schedule__start_hour_code',
                'schedule__end_hour_code',
                'student', 'student__user',
                'staff'
            )
            .order_by('-schedule__date', '-schedule__start_hour_code__code', '-id')
        )

        serializer = ReservationListSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@extend_schema(tags=['space'])
class SpaceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve the details of a specific space for the authenticated users.",
        responses={
            200: OpenApiResponse(
                response=SpaceSerializer(),
                description="Space details retrieved successfully.",
                examples=[
                    OpenApiExample(
                        name="success",
                        value={
                            "id": 1,
                            "space_type": "string",
                            "name": "string",
                            "address": "string",
                            "capacity": 50,
                            "description": "string",
                            "space_manager": {
                                "id": 1,
                                "first_name": "string",
                                "last_name": "string",
                                "username": "string",
                                "email": "string@example.com"
                            },
                            "features": [
                                {"id": 1, "name": "string"},
                                {"id": 2, "name": "string"}
                            ],
                            "images": [
                                {"id": 1, "url": "http://localhost:8000/media/space_photos/1.jpg"}
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Authentication credentials were not provided or are invalid.",
                examples=[
                    OpenApiExample(
                        name="unauthorized",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid space ID provided (e.g., negative or non-integer value).",
                examples=[
                    OpenApiExample(
                        name="bad_request",
                        value={"error": "Invalid space ID. Must be a positive integer."}
                    ),
                    OpenApiExample(
                        name="NonInteger",
                        value={"error": "Space ID must be an integer."}  # اگه `space_id` رشته باشه
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found with the given ID.",
                examples=[
                    OpenApiExample(
                        name="not_found",
                        value={"error": "Space with ID 10 not found."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="An unexpected internal server error occurred.",
                examples=[
                    OpenApiExample(
                        name="internal_error",
                        value={"error": "An unexpected error occurred. Please try again later."}
                    ),
                    OpenApiExample(
                        name="DatabaseError",
                        value={"error": "Failed to retrieve space details from database."}
                    )
                ]
            )
        }
    )
    def get(self, request, space_id: int):
        try:
            if space_id <= 0:
                return Response(
                    {"error": "Invalid space ID. Must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            space = get_object_or_404(
                Space.objects
                     .select_related("space_manager", "space_manager__user")
                     .prefetch_related("features", "images"),
                id=space_id
            )

            serializer = SpaceSerializer(space, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Space.DoesNotExist:
            return Response(
                {"error": f"Space with ID {space_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Space ID must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                        

@extend_schema(tags=["space_manager"])
class ManagerSpaceListView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='space_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter spaces by type',
                required=False,
                enum=['hall', 'class', 'labratory', 'office']
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ManagerSpaceListSerializer(many=True),
                description="Managed spaces retrieved successfully.",
                examples=[OpenApiExample(
                    "Example",
                    value=[{
                        "id": 3,
                        "space_type": "string",
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "description": "string",
                        "phone_number": "string",
                        "first_image_url": "http://localhost:8000/media/space_photos/1.jpg"
                    }]
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized – Authentication credentials were not provided.",
                examples=[OpenApiExample(
                    name="UnauthorizedExample",
                    value={"error": "Authentication credentials were not provided."}
                )]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden – User is not the manager of this space.",
                examples=[OpenApiExample(
                    name="ForbiddenExample",
                    value={"error": "You are not a space manager."}
                )]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not Found – The requested space does not exist or is not managed by the user.",
                examples=[OpenApiExample(
                    name="NotFoundExample",
                    value={"error": "No spaces managed by you."}
                )]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample(
                    name="ServerErrorExample",
                    value={"error": "An unexpected error occurred."}
                ),
                OpenApiExample(
                    name="DatabaseError",
                    value={"error": "Failed to retrieve managed spaces from database."}
                )]
            )
        },
        description="List spaces managed by the authenticated space manager.",
    )
    def get(self, request):
        try:
            manager = request.user.spacemanager
        except Exception:
            return Response({"error": "You are not a space manager."}, status=status.HTTP_403_FORBIDDEN)

        space_type = request.query_params.get('space_type', None)

        queryset = Space.objects.filter(space_manager=manager).prefetch_related("images").order_by("id")
        
        if space_type:
            queryset = queryset.filter(space_type=space_type)

        if not queryset.exists(): 
            return Response({"error": "No spaces managed by you."}, status=status.HTTP_404_NOT_FOUND)

        data = ManagerSpaceListSerializer(queryset, many=True).data
        return Response(data, status=status.HTTP_200_OK)
    

@extend_schema(tags=["space_manager"])
class ManagerSpaceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSpaceManagerUser]

    @extend_schema(
        description="Retrieve details of a specific managed space by ID.",
        responses={
            200: OpenApiResponse(
                response=ManagerSpaceDetailSerializer,
                description="Space detail retrieved successfully.",
                examples=[OpenApiExample(
                    "Example",
                    value={
                        "id": 1,
                        "space_type": "string",
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "description": "string",
                        "features": [{"id": 1, "name": "string"}],
                        "phone_number": "string",
                        "images": [
                            {"id": 1, "url": "http://localhost:8000/media/space_photos/1.jpg"}
                        ]
                    }
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized – Authentication credentials were not provided.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden – User is not a space manager.",
                examples=[OpenApiExample(
                    name="ForbiddenExample",
                    value={"error": "You are not a space manager."}
                )]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Not Found – The requested space does not exist or is not managed by the user.",
                examples=[OpenApiExample(
                    name="NotFoundExample",
                    value={"error": "Space with ID 10 not found or not managed by you."}
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid space ID provided (e.g., negative or non-integer value).",
                examples=[
                    OpenApiExample(
                        name="bad_request",
                        value={"error": "Invalid space ID. Must be a positive integer."}
                    ),
                    OpenApiExample(
                        name="NonInteger",
                        value={"error": "Space ID must be an integer."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample(
                    name="ServerErrorExample",
                    value={"error": "An unexpected error occurred."}
                ),
                OpenApiExample(
                    name="DatabaseError",
                    value={"error": "Failed to retrieve space details from database."}
                )]
            )
        }
    )
    def get(self, request, space_id: int):
        manager = getattr(request.user, 'spacemanager', None)
        if not manager:
            return Response({"error": "You are not a space manager."}, status=status.HTTP_403_FORBIDDEN)

        try:
            if space_id <= 0:
                return Response(
                    {"error": "Invalid space ID. Must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            space = get_object_or_404(
                Space.objects
                .prefetch_related("features", "images")
                .select_related("space_manager", "space_manager__user"),
                pk=space_id, space_manager=manager
            )
            data = ManagerSpaceDetailSerializer(space, context={'request': request}).data
            return Response(data, status=status.HTTP_200_OK)

        except ValueError: 
            return Response(
                {"error": "Space ID must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                    
                    
@extend_schema(tags=['space_manager'])
class ManagerSpaceCreateView(APIView):
    permission_classes = [IsSpaceManagerUser]
    parser_classes = [MultiPartParser, FormParser]  

    @extend_schema(
        description="Create a new space by authenticated space manager.",
        request=SpaceCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=SpaceSerializer,
                description="Space created successfully.",
                examples=[OpenApiExample(
                    "Success",
                    value={
                        "id": 1,
                        "space_type": "string",
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "phone_number": "string",
                        "description": "string",
                        "features": [
                            {"id": 1, "name": "string1"},
                            {"id": 2, "name": "string2"}
                        ]
                    }
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation error.",
                examples=[OpenApiExample(
                    "BadRequest",
                    value={"capacity": ["Capacity must be greater than zero."]}
                ),
                OpenApiExample(
                    "MissingRequired",
                    value={"space_type": ["This field is required."]}
                ),
                OpenApiExample(
                    "InvalidFeatures",
                    value={"features": ["Invalid pk '999' - object does not exist."]}
                ),
                OpenApiExample(
                    "InvalidImages",
                    value={"images": ["No file was submitted. Check the encoding type on the form."]}
                ),
                OpenApiExample(
                    "InvalidFormat",
                    value={"features": ["A valid list of integers or comma-separated string is required."]}
                )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized.",
                examples=[OpenApiExample(
                    "Unauthorized",
                    value={"error": "Authentication credentials were not provided."}
                )]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden – User is not a space manager.",
                examples=[OpenApiExample(
                    "Forbidden",
                    value={"error": "You are not authorized to create spaces."}
                )]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error.",
                examples=[OpenApiExample(
                    "ServerError",
                    value={"error": "An unexpected error occurred."}
                ),
                OpenApiExample(
                    "DatabaseError",
                    value={"error": "Failed to save space to database."}
                ),
                OpenApiExample(
                    "ImageError",
                    value={"error": "Failed to process uploaded images."}
                )
                ]
            )
        }
    )
    def post(self, request):
        serializer = SpaceCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            space = serializer.save()
            return Response(SpaceSerializer(space, context={"request": request}).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Unexpected error:", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["space_manager"])
class ManagerSpaceUpdateView(APIView):
    permission_classes = [IsSpaceManagerUser]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        description="Partially update a space managed by the authenticated manager.",
        request=SpaceUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=SpaceSerializer,
                description="Space updated successfully.",
                examples=[OpenApiExample(
                    "Success",
                    value={
                        "id": 1,
                        "space_type": "string",
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "phone_number": "09123456789",
                        "description": "string",
                        "features": [
                            {"id": 1, "name": "string1"},
                            {"id": 2, "name": "string2"}
                        ],
                        "images": [
                            {"id": 1, "url": "/media/space_photos/1.jpg"},
                            {"id": 2, "url": "/media/space_photos/2.jpg"}
                        ]
                    }
                )]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation error.",
                examples=[
                    OpenApiExample(
                        "CapacityError",
                        value={"capacity": ["Capacity must be greater than zero."]}
                    ),
                    OpenApiExample(
                        "InvalidFeatureError",
                        value={"features": ["Invalid pk '999' - object does not exist."]}
                    ),
                    OpenApiExample(
                        "MissingRequired",
                        value={"space_type": ["This field is required."]}
                    ),
                    OpenApiExample(
                        "InvalidImages",
                        value={"images": ["No file was submitted. Check the encoding type on the form."]}
                    ),
                    OpenApiExample(
                        "InvalidFormat",
                        value={"features": ["A valid list of integers or comma-separated string is required."]}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden – Not space manager of this space.",
                examples=[
                    OpenApiExample(
                        "ForbiddenExample",
                        value={"error": "You are not authorized to update this space."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found.",
                examples=[
                    OpenApiExample(
                        "NotFoundExample",
                        value={"error": "Space with ID 77 not found."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[
                    OpenApiExample(
                        "ServerErrorExample",
                        value={"error": "An unexpected error occurred."}
                    ),
                    OpenApiExample(
                        "DatabaseError",
                        value={"error": "Failed to update space in database."}
                    ),
                    OpenApiExample(
                        "ImageError",
                        value={"error": "Failed to process uploaded images."}
                    )
                ]
            ),
        }
    )
    def put(self, request, space_id):
        try:
            space = Space.objects.get(id=space_id)
            if not request.user == space.space_manager.user:
                return Response(
                    {"error": "You are not authorized to update this space."},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = SpaceUpdateSerializer(instance=space, data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            updated_space = serializer.save()

            return Response(SpaceSerializer(updated_space).data, status=status.HTTP_200_OK)

        except Space.DoesNotExist:
            return Response({"error": "Space not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@extend_schema(tags=['reservation'])
class ScheduleAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]  

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='The date to check available hours (YYYY-MM-DD)',
                required=True,
            ),
            OpenApiParameter(
                name='space_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='The ID of the space to check availability for',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ScheduleAvailabilitySerializer(many=True),
                description="List of available hours for the specified date and space.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value=[
                            {"hour_code": 1, "time_range": "7:00-8:00", "is_locked": False},
                            {"hour_code": 2, "time_range": "8:00-9:00", "is_locked": True},
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid date or space ID format.",
                examples=[
                    OpenApiExample(
                        name="BadRequest",
                        value={"error": "Date must be in YYYY-MM-DD format."}
                    ),
                    OpenApiExample(
                        name="InvalidSpaceId",
                        value={"error": "Invalid space ID."}
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Authentication credentials were not provided.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found.",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"error": "Space with ID 10 not found."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."}
                    )
                ]
            )
        },
        description="Retrieve the list of available hours for a specific date and space."
    )
    def get(self, request):
        date_str = request.query_params.get('date')
        space_id = request.query_params.get('space_id')

        if not date_str or not space_id:
            return Response({"error": "Date and space ID are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            space_id = int(space_id)
            if space_id <= 0:
                return Response({"error": "Invalid space ID."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Date must be in YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            space = get_object_or_404(Space, id=space_id)
        except Exception:
            return Response({"error": f"Space with ID {space_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        reserved_schedules = Schedule.objects.filter(space=space, date=date).values_list('start_hour_code__code', 'end_hour_code__code')

        hours = []
        hour_slots = HourSlot.objects.all()  
        for slot in hour_slots:
            is_locked = any(
                schedule[0] <= slot.code <= schedule[1]
                for schedule in reserved_schedules
            )
            hours.append({
                "hour_code": slot.code,
                "time_range": slot.time_range,
                "is_locked": is_locked
            })

        serializer = ScheduleAvailabilitySerializer(hours, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)