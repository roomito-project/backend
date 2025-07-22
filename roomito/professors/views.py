from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema
from .models import Professor
from .serializers import ProfessorRegisterSerializer, ProfessorVerifySerializer, ProfessorLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers

class ProfessorRegisterView(APIView):
    @extend_schema(
        request=ProfessorRegisterSerializer,
        responses={200: dict, 400: dict}
    )
    def post(self, request):
        serializer = ProfessorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        professor = Professor.objects.get(
            first_name=data['first_name'],
            last_name=data['last_name'],
            national_id=data['national_id'],
            personnel_code=data['personnel_code']
        )

        code = get_random_string(length=6, allowed_chars='0123456789')
        professor.verification_code = code
        professor.set_password(data['password'])
        professor.save()

        send_mail(
            subject="کد تأیید ثبت‌نام در رومیتو",
            message=f"کد تأیید شما: {code}",
            from_email="mahyajfri37@gmail.com",
            recipient_list=[professor.email],
            fail_silently=False
        )

        return Response({"message": "The verification code has been sent to the email."}, status=200)


class ProfessorVerifyView(APIView):
    @extend_schema(
        request=ProfessorVerifySerializer,
        responses={200: dict, 400: dict}
    )
    def post(self, request):
        serializer = ProfessorVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        personnel_code = serializer.validated_data['personnel_code']
        code = serializer.validated_data['verification_code']

        try:
            professor = Professor.objects.get(personnel_code=personnel_code)
        except Professor.DoesNotExist:
            return Response({"error": "The professor could not be found."}, status=404)

        if professor.verification_code != code:
            return Response({"error": "The verification code is incorrect."}, status=400)

        if professor.is_registered:
            return Response({"message": "This professor has registered before."}, status=400)

        user = User.objects.create_user(
            username=professor.personnel_code,
            password=professor.password, 
        )
        professor.user = user
        professor.is_registered = True
        professor.is_verified = True
        professor.verification_code = None
        professor.save()
        
        return Response({"message": "The professor has been successfully registered."}, status=200)
    
class ProfessorLoginView(APIView):
    @extend_schema(
        request=ProfessorLoginSerializer,
        responses={
            200: serializers.DictField(),
            401: serializers.DictField(),
        },
        examples=[
            OpenApiExample(
                "Login example",
                value={"personnel_code": "string", "password": "string"},
                request_only=True
            )
        ],
        description="Professor login using personnel code and password"
    )
    
    def post(self, request):
        serializer = ProfessorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        personnel_code = serializer.validated_data['personnel_code']
        password = serializer.validated_data['password']

        user = authenticate(username=personnel_code, password=password)
        if user is None:
            return Response({"error": "Invalid personnel code or password."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)    