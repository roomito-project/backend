from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    student_id = models.CharField(max_length=10, unique=True, verbose_name="شماره دانشجویی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    email = models.EmailField(max_length=100, unique=True, verbose_name="ایمیل")
    student_card_photo = models.ImageField(upload_to="student_cards/", verbose_name="عکس کارت دانشجویی")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.student_id})"