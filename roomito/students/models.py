from django.db import models

class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    email = models.EmailField(unique=True, default='example@example.com', verbose_name='ایمیل')
    student_id = models.CharField(max_length=10, unique=True, verbose_name="شماره دانشجویی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    student_card_photo = models.ImageField(upload_to="student_cards/", verbose_name="عکس کارت دانشجویی")
    is_approved = models.BooleanField(default=False, verbose_name="وضعیت تأیید")
    password = models.CharField(max_length=128, verbose_name='رمز عبور')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.student_id})"