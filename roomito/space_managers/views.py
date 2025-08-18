from django.http import Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from .models import Reservation, Space, Event, SpaceFeature, ReservationNotification, SpaceImage, SpaceManager
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    ErrorResponseSerializer,
    ManagerSpaceDetailSerializer,
    ManagerSpaceListSerializer,
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
                        "Success",
                        value={
                            "first_name": "string",
                            "last_name": "string",
                            "email": "string@example.com",
                            "username": "string",
                        },
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a space manager.",
                examples=[
                    OpenApiExample(
                        "NotSpaceManager",
                        value={"error": "User is not a space manager."},
                        response_only=True
                    )
                ]
            )
        },
            description="Retrieves the authenticated space manager's profile.",
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
                        name="UsernameError",
                        value={"username": ["This username is already in use."]}
                    ),
                    OpenApiExample(
                        name="EmailError",
                        value={"email": ["This email is already in use."]}
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
        description="Update profile information of the authenticated space manager"
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
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
                examples=[OpenApiExample(
                    name="ServerErrorExample",
                    value={"error": "An unexpected error occurred."}
                )]
            )
        },
        description="Retrieves the list of all available spaces for authenticated users."
    )
    
    def get(self, request):
        qs = (
            Space.objects
            .select_related("space_manager", "space_manager__user")
            .prefetch_related("images")
            .order_by("id")
        )
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
                                "space": {"id": 1, "name": "string", "address": "string", "capacity": 50},
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
        description="Retrieves the current and available features for a space managed by the authenticated space manager.",
        request=None,
        responses={
            200: OpenApiResponse(
                response=SpaceFeatureSerializer,
                description="space features retrieved Successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "space_name": "string",
                            "current_features": [""],
                            "available_features": [
                                {"id": 1, "name": "string1"},
                                {"id": 2, "name": "string2"}
                            ]
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found or user is not the manager",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"error": "Space not found or you are not authorized to manage it."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"error": "An unexpected error occurred."}
                    )
                ]
            )
        }
    )
    def get(self, request, space_id):
        space = get_object_or_404(Space, id=space_id, space_manager__user=request.user)
        features = SpaceFeature.objects.all()
        space_features = space.features.all()

        return Response({
            "space_name": space.name,
            "current_features": [feature.name for feature in space_features],
            "available_features": SpaceFeatureSerializer(features, many=True).data
        }, status=status.HTTP_200_OK) 
   
   
@extend_schema(tags=['space_manager'])
class SpaceUpdateFeatureView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Allows a space manager to add existing features to a space using their IDs.",
        request=FeatureIdsSerializer, 
        responses={
            200: OpenApiResponse(
                description="Features updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "message": "Features updated successfully.",
                            "updated_features": ["string1", "string2"]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid data or no feature IDs provided",
                examples=[
                    OpenApiExample(
                        "invalid_error",
                        value={"error": "No feature IDs provided."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found, user is not the manager, or feature ID is invalid",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"error": "Space not found or you are not authorized to manage it."}
                    ),
                    OpenApiExample(
                        "InvalidFeature",
                        value={"error": "One or more feature IDs are invalid: [999]"}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"error": "An unexpected error occurred."}
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
            return Response(
                {"error": f"One or more feature IDs are invalid: {invalid_features}"},
                status=status.HTTP_404_NOT_FOUND
            )

        features_to_add = SpaceFeature.objects.filter(id__in=feature_ids)
        space.features.add(*features_to_add)

        return Response({
            "message": "Features updated successfully.",
            "updated_features": [f.name for f in space.features.all()]
        }, status=status.HTTP_200_OK)
        

@extend_schema(tags=['reservation'])
class ReservationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a reservation request for a specific space by authenticated user (student or staff).",
        request=ReservationCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=ReservationCreateSerializer,
                description="Reservation request created successfully and sent to space manager for review.",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "reservation_type": "class",
                            "reservee_type": "student",
                            "phone_number": "09123456789",
                            "description": "stirng",
                            "schedule": {
                                "start_time": "09:00:00",
                                "end_time": "11:00:00",
                                "date": "2025-08-15"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid data provided (e.g., invalid time range or missing required fields).",
                examples=[
                    OpenApiExample(
                    name="SameTime",
                    value={"schedule": "Start and end time cannot be the same."},
                    response_only=True
                    ),
                    OpenApiExample(
                        name="BadRequest",
                        value={"shcedule": "Start time must be before end time."}
                    ),
                    OpenApiExample(
                        name="ValidationError",
                        value={"reservee_type": ["You must be a student to select this reservee type."]}
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
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
                        value={"error": "Space not found."}
                    )
                ]
            ),
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Time conflict with existing reservations.",
                examples=[
                    OpenApiExample(
                        name="Conflict",
                        value={"error": "This time conflicts with another schedule on the same date."}
                    )
                ]
            ),
            422: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unprocessable entity (e.g., invalid reservation type or reservee type).",
                examples=[
                    OpenApiExample(
                        name="Unprocessable",
                        value={"reservation_type": ["Invalid reservation type."]}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Internal server error (e.g., database failure).",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"error": "An unexpected error occurred."}
                    )
                ]
            )
        }
    )        
    def post(self, request, space_id):
        space = get_object_or_404(Space, id=space_id)
        request_data = request.data.copy()
        request_data['space'] = space.id

        serializer = ReservationCreateSerializer(
            data=request_data,
            context={'request': request, 'space': space}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            reservation = serializer.save()

            if space.space_manager and space.space_manager.email:
                send_mail(
                    subject='درخواست رزرو جدید',
                    message=f'درخواستی جدید برای رزرو {space.name} در تاریخ {reservation.schedule.date} از ساعت {reservation.schedule.start_time} تا {reservation.schedule.end_time} ثبت شده است. لطفاً آن را بررسی کنید.',
                    from_email="mahyajfri37@gmail.com",
                    recipient_list=[space.space_manager.email],
                    fail_silently=True,
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
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
                                "reservation_type": "string",
                                "description": "string",
                                "reservee_name": "string"
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not authenticated.",
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={"error": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User is not a space manager or has no managed spaces.",
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={"error": "You are not authorized to view this list."}
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
            return Response({"error": "You are not authorized to view this list."}, status=status.HTTP_403_FORBIDDEN)

        managed_spaces = Space.objects.filter(space_manager=space_manager)
        if not managed_spaces.exists():
            return Response({"message": "No spaces managed by you."}, status=status.HTTP_200_OK)

        reservations = Reservation.objects.filter(space__in=managed_spaces).select_related('schedule', 'space', 'student', 'staff')
        serializer = ReservationListSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@extend_schema(tags=['space'])
class SpaceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve the details of a specific space for the authenticated users",
        responses={
            200: OpenApiResponse(
                response=SpaceSerializer(),
                description="Space details retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="success",
                        value={
                            "id": 1,
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
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid space ID provided (e.g., negative or non-integer value).",
                examples=[
                    OpenApiExample(
                        name="bad_request",
                        value={"error": "Invalid space ID. Must be a positive integer."}
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
        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

@extend_schema(tags=["space_manager"])
class ManagerSpaceListView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="List spaces managed by the authenticated space manager.",
        responses={
            200: OpenApiResponse(
                response=ManagerSpaceListSerializer(many=True),
                description="Managed spaces retrieved successfully.",
                examples=[OpenApiExample(
                    "Example",
                    value=[{
                        "id": 3,
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
                )
            ]
        ),
        403: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Forbidden – User is not the manager of this space.",
            examples=[OpenApiExample(
                name="ForbiddenExample",
                value={"error": "You are not authorized to view this space."}
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Not Found – The requested space does not exist or is not managed by the user.",
            examples=[OpenApiExample(
                name="NotFoundExample",
                value={"error": "Space not found."}
            )]
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Unexpected server error.",
            examples=[OpenApiExample(
                name="ServerErrorExample",
                value={"error": "An unexpected error occurred."}
            )]
        )
    }
)
    def get(self, request):
        try:
            manager = request.user.spacemanager  
        except Exception:
            return Response({"error": "You are not a space manager."}, status=status.HTTP_403_FORBIDDEN)

        qs = (
            Space.objects
            .filter(space_manager=manager)
            .prefetch_related("images")
            .order_by("id")
        )
        data = ManagerSpaceListSerializer(qs, many=True).data
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
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "description": "string",
                        "features": [{"id":1,"name":"string"}],
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
                )]
        ),
        403: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Forbidden – User is not a space manager.",
            examples=[OpenApiExample(
                name="ForbiddenExample",
                value={"error": "You are not authorized to view this list."}
            )]
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Unexpected server error.",
            examples=[OpenApiExample(
                name="ServerErrorExample",
                value={"error": "An unexpected error occurred."}
            )]
        )
    }
)
    def get(self, request, space_id: int):
        manager = getattr(request.user, 'spacemanager', None)
        if not manager:
            return Response({"error": "You are not a space manager."}, status=status.HTTP_403_FORBIDDEN)

        space = get_object_or_404(
            Space.objects
            .prefetch_related("features", "images")
            .select_related("space_manager", "space_manager__user"),
            pk=space_id, space_manager=manager
        )
        data = ManagerSpaceDetailSerializer(space, context={'request': request}).data
        return Response(data, status=status.HTTP_200_OK)
        

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
                description="Validation error",
                examples=[OpenApiExample(
                    "BadRequest",
                    value={"capacity": ["Capacity must be greater than zero."]}
                )]
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized",
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
                description="Server error",
                examples=[OpenApiExample(
                    "ServerError",
                    value={"error": "An unexpected error occurred."}
                )]
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
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "CapacityError",
                        value={"capacity": ["Capacity must be greater than zero."]}
                    ),
                    OpenApiExample(
                        "InvalidFeatureError",
                        value={"features": ["Invalid pk '999' - object does not exist."]}
                    )
                ]
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden – Not space manager of this space",
                examples=[
                    OpenApiExample(
                        "ForbiddenExample",
                        value={"error": "You are not authorized to update this space."}
                    )
                ]
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Space not found",
                examples=[
                    OpenApiExample(
                        "NotFoundExample",
                        value={"error": "Space with ID 77 not found."}
                    )
                ]
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error",
                examples=[
                    OpenApiExample(
                        "ServerErrorExample",
                        value={"error": "An unexpected error occurred."}
                    )
                ]
            ),
        }
    )
    def patch(self, request, space_id: int):
        space = get_object_or_404(Space, id=space_id, space_manager__user=request.user)

        data = request.data.copy()

        for key in ["name", "address", "description"]:
            if key in data and data.get(key) == "":
                data.pop(key)

        if "phone_number" in data and data.get("phone_number") == "":
            data["phone_number"] = None

        if "capacity" in data and data.get("capacity") in ("", None):
            data.pop("capacity")

        if hasattr(request.data, "getlist"):
            raw_features = request.data.getlist("features")
        else:
            raw_features = data.get("features", [])

        if isinstance(raw_features, str):
            raw_features = [x.strip() for x in raw_features.split(",") if x.strip()]

        cleaned_feature_ids = []
        for f in raw_features or []:
            if f not in ("", None):
                try:
                    cleaned_feature_ids.append(int(f))
                except (TypeError, ValueError):
                    pass

        data.pop("features", None)

        new_images = request.FILES.getlist("images") if hasattr(request.FILES, "getlist") else []
        data.pop("images", None)

        serializer = SpaceUpdateSerializer(
            instance=space,
            data=data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        space = serializer.save()

        if cleaned_feature_ids:
            qs = SpaceFeature.objects.filter(id__in=cleaned_feature_ids)
            valid_ids = {obj.id for obj in qs}
            missing = [fid for fid in set(cleaned_feature_ids) if fid not in valid_ids]
            if missing:
                return Response(
                    {"features": [f"Invalid feature id(s): {missing}"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            space.features.add(*qs)

        for img in new_images:
            if img:
                SpaceImage.objects.create(space=space, image=img)

        return Response(SpaceSerializer(space, context={"request": request}).data, status=status.HTTP_200_OK)
