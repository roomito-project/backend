from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from professors.models import Professor

class SpaceManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    username = models.CharField(max_length=50, unique=True, verbose_name="نام کاربری") 
    spaces = models.ManyToManyField('Space', verbose_name="فضاها", help_text="لیست فضاهای مدیریت شده")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Space(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام")
    address = models.TextField(verbose_name="آدرس")
    capacity = models.IntegerField(verbose_name="ظرفیت")
    space_manager = models.ForeignKey(SpaceManager, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مدیر فضا")

    def __str__(self):
        return f"{self.name} (ظرفیت: {self.capacity})"      

class Reservation(models.Model):
    RESERVATION_TYPES = (
        ('event', 'رویداد'),
        ('class', 'جلسات درسی'),
        ('gathering', 'جلسات دورهمی'),
    )
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPES, verbose_name="نوع رزرو")
    date = models.DateField(verbose_name="تاریخ")
    reservee_type = models.CharField(max_length=20, choices=(('student', 'دانشجو'), ('professor', 'استاد')), verbose_name="رزروکننده")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دانجوی رزروکننده")
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استاد رزروکننده")
    description = models.CharField(verbose_name='توضیحات', default='بدون توضیحات')            
    status = models.CharField(max_length=20, choices=(('under_review', 'در حال بررسی شدن'), ('approved', 'تأیید شده'), ('rejected', 'رد شده')), default='under_review', verbose_name="وضعیت رزرو")
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="محل برگزاری")
    schedule = models.OneToOneField('Schedule', on_delete=models.CASCADE, null=True, blank=True, verbose_name="زمان‌بندی رزرو", related_name='reservation_instance')
    
    def __str__(self):
        reservee_name = self.student.first_name if self.student else self.professor.first_name if self.professor else "نامشخص"
        return f"{self.reservation_type} - {self.date} (رزروکننده: {reservee_name}, وضعیت: {self.status})"

    def save(self, *args, **kwargs):
        if self.student and self.professor:
            raise ValueError("فقط می‌توانید یک دانشجو یا یک استاد به‌عنوان رزروکننده انتخاب کنید.")
        if self.reservee_type == 'student' and not self.student:
            raise ValueError("برای نوع رزروکننده دانشجو، باید دانشجو انتخاب کنید.")
        if self.reservee_type == 'professor' and not self.professor:
            raise ValueError("برای نوع رزروکننده استاد، باید استاد انتخاب کنید.")
        super().save(*args, **kwargs)
    
class Schedule(models.Model):
    start_time = models.DateTimeField(verbose_name="ساعت شروع")
    end_time = models.DateTimeField(verbose_name="ساعت پایان")
    space = models.ForeignKey(Space, on_delete=models.CASCADE, verbose_name="محل برگزاری")
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, verbose_name="رزرو", related_name='schedule_instance')
    
    def __str__(self):
        return f"{self.space.name} - {self.start_time} تا {self.end_time}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time <= self.start_time:
            raise ValidationError("ساعت پایان باید بعد از ساعت شروع باشد.")
        existing_schedules = Schedule.objects.filter(space=self.space).exclude(id=self.id if self.id else None)
        for schedule in existing_schedules:
            if self.start_time < schedule.end_time and self.end_time > schedule.start_time:
                raise ValidationError("این زمان با یک زمان‌بندی دیگر تداخل دارد.")

    def save(self, *args, **kwargs):
        self.clean()  
        super().save(*args, **kwargs)  
    
class Event(models.Model):
    EVENT_TYPES = (
        ('event', 'رویداد'),
        ('class', 'جلسه درسی'),
        ('gathering', 'جلسات دورهمی'),
    )
    title = models.CharField(max_length=200, verbose_name='عنوان')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="نوع")
    date = models.DateField(verbose_name="تاریخ")
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="محل برگزاری")
    poster = models.ImageField(upload_to="event_posters/", null=True, blank=True,  verbose_name="پوستر")
    organizer = models.CharField(max_length=20, choices=(('student', 'دانشجو'), ('professor', 'استاد')), verbose_name="برگزار کننده")
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دانجوی برگزارکننده")
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استاد برگزارکننده")
    description = models.CharField(verbose_name='توضیحات', default='بدون توضیحات')            

    def __str__(self):
        organizer = self.student.first_name if self.student else self.professor.first_name if self.professor else "نامشخص"
        return f"{self.title} (برگزارکننده: {organizer})"

    def save(self, *args, **kwargs):
        if self.organizer == 'student' and not self.student:
            raise ValueError("برای برگزارکننده دانشجو، باید دانشجو انتخاب کنید.")
        if self.organizer == 'professor' and not self.professor:
            raise ValueError("برای برگزارکننده استاد، باید استاد انتخاب کنید.")
        if self.student and self.professor:
            raise ValueError("فقط می‌توانید یک برگزارکننده (دانشجو یا استاد) انتخاب کنید.")
        super().save(*args, **kwargs)