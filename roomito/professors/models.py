from django.db import models
from django.contrib.auth.models import User

class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    personnel_code = models.CharField(max_length=20, unique=True, verbose_name="کد پرسنلی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Code: {self.personnel_code})"

    class Meta:
        verbose_name = "استاد"
        verbose_name_plural = "اساتید"
