import random
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes
from .models import Professor
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone
from datetime import timedelta

class ProfessorRegisterView(APIView):
    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "personnel_code": {"type": "string"},
                    "national_id": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["first_name", "last_name", "personnel_code", "national_id", "password"]
            }
        },
        responses={201: OpenApiTypes.STR},
        examples=[
            OpenApiExample(
                'درخواست نمونه',
                value={
                    "first_name": "mahya",
                    "last_name": "jafari",
                    "personnel_code": "123456",
                    "national_id": "0012345678",
                    "password": "securePass123"
                },
                request_only=True
            ),
        ]
    )
    def post(self, request):
        data = request.data
        required_fields = ['first_name', 'last_name', 'personnel_code', 'national_id', 'password']
        if not all(field in data and data[field] for field in required_fields):
            return Response({"error": "همه‌ی فیلدها الزامی هستند."}, status=400)

        # بررسی اینکه ایمیل استاد در دیتابیس موجود باشد
        try:
            professor = Professor.objects.get(
                first_name=data["first_name"],
                last_name=data["last_name"],
                personnel_code=data["personnel_code"],
                national_id=data["national_id"]
            )
        except Professor.DoesNotExist:
            return Response({"error": "اطلاعات وارد شده با هیچ استادی در سیستم مطابقت ندارد."}, status=404)

        if professor.is_registered:
            return Response({"error": "این استاد قبلاً ثبت‌نام کرده است."}, status=400)

        # تولید کد تأیید
        code = random.randint(100000, 999999)

        # ذخیره کد تأیید در مدل جداگانه
        ProfessorVerificationCode.objects.update_or_create(
            professor=professor,
            defaults={"code": code}
        )

        # هش کردن رمز
        hashed_password = make_password(data["password"])

        # ذخیره رمز هش شده به صورت موقت تا بعد از تأیید ایمیل ثبت نهایی شود
        professor.hashed_password = hashed_password
        professor.save()

        # ارسال ایمیل
        send_mail(
            "کد تأیید ثبت‌نام",
            f"کد تأیید شما: {code}",
            "mahyajfri37@gmail.com",  # حتماً در تنظیمات Django تنظیمش کن
            [professor.email],
            fail_silently=False,
        )

        return Response({"message": "کد تأیید به ایمیل شما ارسال شد."}, status=201)
    
class ProfessorVerificationCode(models.Model):
    professor = models.OneToOneField("Professor", on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)
    
class ProfessorVerifyView(APIView):
    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "verification_code": {"type": "string"},
                },
                "required": ["email", "verification_code"]
            }
        },
        responses={200: OpenApiTypes.STR}
    )
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("verification_code")

        if not email or not code:
            return Response({"error": "ایمیل و کد تأیید الزامی هستند."}, status=400)

        try:
            professor = Professor.objects.get(email=email)
        except Professor.DoesNotExist:
            return Response({"error": "استادی با این ایمیل یافت نشد."}, status=404)

        try:
            verification = ProfessorVerificationCode.objects.get(professor=professor)
        except ProfessorVerificationCode.DoesNotExist:
            return Response({"error": "کد تأیید برای این استاد یافت نشد."}, status=404)

        if verification.code != code:
            return Response({"error": "کد تأیید اشتباه است."}, status=400)

        if verification.is_expired():
            return Response({"error": "کد تأیید منقضی شده است."}, status=400)

        # نهایی‌سازی ثبت‌نام
        professor.password = professor.hashed_password
        professor.is_registered = True
        professor.hashed_password = ""
        professor.save()

        # حذف کد تأیید
        verification.delete()

        return Response({"message": "تأیید با موفقیت انجام شد."}, status=200)
    
