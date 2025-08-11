from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=12, unique=True, validators=[MaxLengthValidator(12, message="student ID cannot be more than 10 characters.")])
    national_id = models.CharField(max_length=10, unique=True, validators=[RegexValidator(regex=r'^\d{10}$',message="National ID must be exactly 10 digits.")])
    student_card_photo = models.ImageField(upload_to="student_cards/")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"
