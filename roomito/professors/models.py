from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxLengthValidator

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    personnel_code = models.CharField(max_length=10, unique=True, null=True, validators=[MaxLengthValidator(10, message="Personnel code cannot be more than 10 characters.")])
    national_id = models.CharField(max_length=10, unique=True, null=True, validators=[RegexValidator(regex=r'^\d{10}$',message="National ID must be exactly 10 digits.")])
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.personnel_code}"
