from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .models import Space
from .serializers import (
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    TokenResponseSerializer,
    SpaceManagerProfileSerializer,
    SpaceManagerPasswordChangeSerializer,
    SpaceManagerLoginSerializer,
    SpaceListSerializer
)


class SpaceManagerLoginView(TokenObtainPairView):
    serializer_class = SpaceManagerLoginSerializer

    @extend_schema(
        request=SpaceManagerLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "LoginSuccess",
                        value={"access": "access_token", "refresh": "refresh_token"},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid credentials or not a space manager",
                examples=[
                    OpenApiExample(
                        "InvalidUser",
                        value={"error": "User is not a space manager."},
                        response_only=True
                    )
                ]
            )
        },
            description="Space manager login with username and password sent to their email."
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


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

class SpaceManagerPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SpaceManagerPasswordChangeSerializer,
        responses={
            200: OpenApiResponse(
                response=SuccessResponseSerializer,
                description="Password changed successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Password updated successfully."},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Invalid old password",
                examples=[
                    OpenApiExample(
                        "WrongPassword",
                        value={"old_password": "Current password is incorrect."},
                        response_only=True
                    )
                ]
            )
        },
            description="Allows an authenticated space manager to change their password by providing the old and new password."
    )
    def post(self, request):
        serializer = SpaceManagerPasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully."}, status=200)
        return Response(serializer.errors, status=400)
    

class SpaceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiExample(
                name="RetrieveSpaceListSuccess",
                value=[
                    {
                        "id": 1,
                        "name": "string",
                        "address": "string",
                        "capacity": 50,
                        "space_manager": {"first_name": "string", "last_name": "string", "email": "string@example.com"}
                    }
                ],
                description="List of all available spaces with details.",
                response_only=True    
            ),
            401: OpenApiExample(
                name="Unauthorized",
                value={"error": "Authentication credentials were not provided."},
                description="User is not authenticated.",
                response_only=True
            )
        },
        description="Retrieve the list of all available spaces for authenticated users"
    )
    
    def get(self, request):
        spaces = Space.objects.all()
        serializer = SpaceListSerializer(spaces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)