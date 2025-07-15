from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    student_id = models.CharField(max_length=10, unique=True, verbose_name="شماره دانشجویی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    student_card_photo = models.ImageField(upload_to="student_cards/", verbose_name="عکس کارت دانشجویی")
    is_approved = models.BooleanField(default=False, verbose_name="وضعیت تأیید")
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} (ID: {self.student_id})"