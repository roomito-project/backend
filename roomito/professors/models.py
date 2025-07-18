from django.db import models
from django.contrib.auth.models import User

class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    email = models.EmailField(unique=True, verbose_name="ایمیل")
    personnel_code = models.CharField(max_length=20, unique=True, verbose_name="کد پرسنلی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    password = models.CharField(max_length=128, verbose_name="رمز عبور", blank=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True, verbose_name="کد تأیید")
    is_verified = models.BooleanField(default=False, verbose_name="تأیید شده")
    is_registered = models.BooleanField(default=False, verbose_name="ثبت‌نام کامل شده")

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.personnel_code}"
