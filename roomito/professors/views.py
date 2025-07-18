from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema
from .models import Professor
from .serializers import ProfessorRegisterSerializer, ProfessorVerifySerializer

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
            subject="کد تأیید ثبت‌نام",
            message=f"کد تأیید شما: {code}",
            from_email="mahyajfri37@gmail.com",
            recipient_list=[professor.email],
            fail_silently=False
        )

        return Response({"message": "کد تأیید به ایمیل ارسال شد."}, status=200)


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
            return Response({"error": "استاد پیدا نشد."}, status=404)

        if professor.verification_code != code:
            return Response({"error": "کد تأیید نادرست است."}, status=400)

        if professor.is_registered:
            return Response({"message": "این استاد قبلاً ثبت‌نام کرده است."}, status=400)

        user = User.objects.create_user(
            username=professor.personnel_code,
            password=professor.password, 
        )
        professor.user = user
        professor.is_registered = True
        professor.is_verified = True
        professor.verification_code = None
        professor.save()
        
        return Response({"message": "ثبت‌نام با موفقیت انجام شد."}, status=200)
