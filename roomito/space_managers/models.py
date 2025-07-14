from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from professors.models import Professor

class SpaceManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    username = models.CharField(max_length=50, unique=True, verbose_name="نام کاربری") 
    spaces = models.TextField(verbose_name="فضاها", help_text="لیست فضاها)")  

    def __str__(self):
        return f"{self.first_name} {self.last_name})"

    class Meta:
        verbose_name = "مدیر فضا"
        verbose_name_plural = "مدیران فضا"
        


class Space(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام")
    address = models.TextField(verbose_name="آدرس")
    capacity = models.IntegerField(verbose_name="ظرفیت")
    space_manager = models.ForeignKey(SpaceManager, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مدیر فضا")

    def __str__(self):
        return f"{self.name} (ظرفیت: {self.capacity})"

    class Meta:
        verbose_name = "فضا"
        verbose_name_plural = "فضاها"        
        

class Reservation(models.Model):
    RESERVATION_TYPES = (
        ('event', 'رویداد'),
        ('class', 'جلسات درسی'),
        ('gathering', 'جلسات دورهمی'),
    )
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPES, verbose_name="نوع رزرو")
    date = models.DateField(verbose_name="تاریخ")
    reservee_type = models.CharField(max_length=20, choices=(('student', 'دانشجو'), ('teacher', 'استاد')), verbose_name="نوع رزروکننده")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دانشجو")
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استاد")
    status = models.CharField(max_length=20, choices=(('under_review', 'در حال بررسی شدن'), ('approved', 'تأیید شده'), ('rejected', 'رد شده')), default='under_review', verbose_name="وضعیت رزرو")
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="فضا")

    def __str__(self):
        reservee_name = self.student.first_name if self.student else self.professor.first_name if self.professor else "نامشخص"
        return f"{self.reservation_type} - {self.date} (رزروکننده: {reservee_name}, وضعیت: {self.status})"

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"

    def save(self, *args, **kwargs):
        if self.student and self.professor:
            raise ValueError("فقط می‌توانید یک دانشجو یا یک استاد به‌عنوان رزروکننده انتخاب کنید.")
        if self.reservee_type == 'student' and not self.student:
            raise ValueError("برای نوع رزروکننده دانشجو، باید دانشجو انتخاب کنید.")
        if self.reservee_type == 'teacher' and not self.professor:
            raise ValueError("برای نوع رزروکننده استاد، باید استاد انتخاب کنید.")
        super().save(*args, **kwargs)