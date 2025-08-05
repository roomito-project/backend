from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from .models import Space, Event
from .serializers import (
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    SpaceManagerProfileSerializer,
    SpaceListSerializer,
    EventSerializer,
    EventDetailSerializer,
    SpaceManagerProfileUpdateSerializer,
)

class SpaceManagerProfileView(APIView):
    permission_classes = [IsAuthenticated]

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
                            "spaces": [1, 2]
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
                                "space_manager": {
                                    "first_name": "string",
                                    "last_name": "string",
                                    "email": "string@example.com",
                                    "username": "string",
                                    "spaces": [1]
                                }
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
                        value={"error": "Invalid event data in database."},
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
    
    
class SpaceManagerProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
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