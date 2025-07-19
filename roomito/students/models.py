from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=10, unique=True)
    national_id = models.CharField(max_length=10, unique=True)
    student_card_photo = models.ImageField(upload_to="student_cards/")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"

    def send_approval_email(self):
        send_mail(
            subject="تأیید ثبت‌نام در رومیتو",
            message=(
                f"دانشجوی گرامی {self.user.first_name} {self.user.last_name}،\n"
                "ثبت‌نام شما توسط مدیر سامانه تأیید شد. اکنون می‌توانید وارد حساب کاربری خود شوید."
            ),
            from_email="mahyajfri37@gmail.com",
            recipient_list=[self.user.email],
            fail_silently=False
        )