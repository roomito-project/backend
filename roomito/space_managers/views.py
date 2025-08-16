from django.http import Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from .models import Reservation, Space, Event, SpaceFeature, ReservationNotification, SpaceManager
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from .serializers import (
    ErrorResponseSerializer,
    SpaceSerializer,
    SpaceUpdateFeatureSerializer,
    SuccessResponseSerializer,
    SpaceManagerProfileSerializer,
    SpaceListSerializer,
    EventSerializer,
    EventDetailSerializer,
    SpaceManagerProfileUpdateSerializer,
    SpaceFeatureSerializer,
    SpaceUpdateFeatureSerializer,
    ReservationCreateSerializer,
    ReservationListSerializer
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
                                "features": [
                                    {"id": 1, "name": "feature1"},
                                    {"id": 2, "name": "feature2"}
                                ]
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
            )
        },
        description="Retrieves the list of all available spaces for authenticated users."
    )
    
    def get(self, request):
        spaces = Space.objects.all()
        serializer = SpaceListSerializer(spaces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
                                "organizer": "professor",
                                "student": None,
                                "professor": {"first_name": "string", "last_name": "string", "email": "string@example.com"},
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

  
@extend_schema(tags=['space'])        
class SpaceFeatureView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Retrieves the current and available features for a specific space by authenticated space manager.",
        request=None,  
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Successfully retrieved space features",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "space_name": "string",
                            "current_features": ["feature1"],
                            "available_features": [
                                {"id": 1, "name": "feature1"}
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
    
    
@extend_schema(tags=['space'])    
class SpaceUpdateFeatureView(APIView):
    permission_classes = [IsSpaceManagerUser]

    @extend_schema(
        description="Add an existing or new feature to a specific space by authenticated space manager.",
        request=SpaceUpdateFeatureSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Feature updated successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "updated_features": ["string1", "string2"]
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="invalid data or validation error..",
                examples=[
                    OpenApiExample(
                        "invalidError",
                        value={
                            "action": ["Please specify the action (add_existing or add_new)."],
                            "feature_name": ["Please provide the feature name."]
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
            409: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Feature already exists when trying to add a new one",
                examples=[
                    OpenApiExample(
                        "Conflict",
                        value={"error": "Feature already exists."}
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
        },
    )
    def post(self, request, space_id):
        space = get_object_or_404(Space, id=space_id, space_manager__user=request.user)
        serializer = SpaceUpdateFeatureSerializer(data=request.data, context={'space': space})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        feature_action = request.data.get('action')
        feature_name = request.data.get('feature_name')

        if feature_action == "add_existing":
            feature = get_object_or_404(SpaceFeature, name=feature_name)
            space.features.add(feature)
        elif feature_action == "add_new":
            if SpaceFeature.objects.filter(name=feature_name).exists():
                return Response({"error": "Feature already exists."}, status=status.HTTP_400_BAD_REQUEST)
            new_feature = SpaceFeature.objects.create(name=feature_name)
            space.features.add(new_feature)

        space.save()
        return Response({"message": "Feature updated successfully.", "updated_features": [f.name for f in space.features.all()]}, status=status.HTTP_200_OK)   


@extend_schema(tags=['reservation'])
class ReservationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a reservation request for a specific space by authenticated user (student or professor).",
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

        reservations = Reservation.objects.filter(space__in=managed_spaces).select_related('schedule', 'space', 'student', 'professor')
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
                            ]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
                examples=[
                    OpenApiExample(
                        name="unauthorized",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Space not found with the given ID.",
                examples=[
                    OpenApiExample(
                        name="not_found",
                        value={"error": "Space with ID 10 not found."}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid space ID provided (e.g., negative or non-integer value).",
                examples=[
                    OpenApiExample(
                        name="bad_request",
                        value={"error": "Invalid space ID. Must be a positive integer."}
                    )
                ]
            ),
            500: OpenApiResponse(
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
    def get(self, request, space_id):
        try:
            if not isinstance(space_id, int) or space_id <= 0:
                return Response(
                    {"error": "Invalid space ID. Must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            space = get_object_or_404(Space, id=space_id)

            serializer = SpaceSerializer(space)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404:
            return Response(
                {"error": f"Space with ID {space_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as ve:
            return Response(
                {"error": f"Validation error: {str(ve)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )