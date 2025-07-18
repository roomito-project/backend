from django.db import models
from django.contrib.auth.models import User

class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    personnel_code = models.CharField(max_length=20, unique=True, verbose_name="کد پرسنلی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    email = models.EmailField(verbose_name="ایمیل", unique=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True, verbose_name="کد تأیید")
    is_verified = models.BooleanField(default=False, verbose_name="وضعیت تأیید")
    is_registered = models.BooleanField(default=False)
    hashed_password = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.personnel_code})"
