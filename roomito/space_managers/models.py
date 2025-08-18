from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from professors.models import Staff
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models.functions import Lower


class SpaceManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SpaceFeature(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Space(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    description = models.TextField(default="no description")
    space_manager = models.ForeignKey(
        SpaceManager,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    features = models.ManyToManyField(SpaceFeature, blank=True, related_name="spaces")

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"

    @property
    def first_image(self):
        return self.images.order_by('id').first()


class SpaceImage(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='space_photos/')

    class Meta:
        ordering = ['id'] 

    def __str__(self):
        return f"{self.space.name} - image #{self.id}"


class Schedule(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField(default=timezone.now)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.space.name} - {self.date} - {self.start_time} till {self.end_time}"

    def clean(self):
        if self.end_time == self.start_time:
            raise ValidationError("Start and end time cannot be the same.")
        if self.end_time < self.start_time:
            raise ValidationError("End time must be after start time.")

        existing = Schedule.objects.filter(space=self.space, date=self.date).exclude(pk=self.pk)
        if existing.filter(start_time__lt=self.end_time, end_time__gt=self.start_time).exists():
            raise ValidationError("This time conflicts with another schedule on the same date.")
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Reservation(models.Model):
    RESERVATION_TYPES = (
        ('event', 'Event'),
        ('class', 'Class'),
        ('gathering', 'Gathering'),
    )

    RESERVEE_TYPES = (
        ('student', 'Student'),
        ('Staff', 'Staff'),
    )

    STATUSES = (
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPES)
    reservee_type = models.CharField(max_length=20, choices=RESERVEE_TYPES)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    description = models.CharField(max_length=255, default='no description')
    status = models.CharField(max_length=20, choices=STATUSES, default='under_review')
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    schedule = models.OneToOneField(Schedule, on_delete=models.CASCADE, null=True, blank=True, related_name='reservation_instance')

    def __str__(self):
        reservee_name = self.student.first_name if self.student else self.staff.first_name if self.staff else "unknown"
        if self.schedule:
            return f"{self.reservation_type} - {self.schedule.date} {self.schedule.start_time} to {self.schedule.end_time} (reservee: {reservee_name}, status: {self.status})"
        return f"{self.reservation_type} - no schedule (reservee: {reservee_name}, status: {self.status})"

    def save(self, *args, **kwargs):
        if self.student and self.Staff:
            raise ValueError("You can only choose one student or one staff as the reservee.")
        if self.reservee_type == 'student' and not self.student:
            raise ValueError("For the student reservee type, you must select a student.")
        if self.reservee_type == 'staff' and not self.staff:
            raise ValueError("For the staff reservee type, you must select a staff.")
        self.clean()
        super().save(*args, **kwargs)


class Event(models.Model):
    EVENT_TYPES = (
        ('event', 'Event'),
        ('class', 'Class'),
        ('gathering', 'Gathering'),
    )

    ORGANIZER_TYPES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
    )
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    poster = models.ImageField(upload_to="event_posters/", null=True, blank=True)
    organizer = models.CharField(max_length=20, choices=ORGANIZER_TYPES)
    student_organizer = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    staff_organizer = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(default='no description')
    schedule = models.OneToOneField(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_instance')

    def __str__(self):
        organizer = self.student_organizer.first_name if self.student_organizer else self.staff_organizer.first_name if self.staff_organizer else "unknown"
        if self.schedule:
            return f"{self.title} (organizer: {organizer}, {self.schedule.date} {self.schedule.start_time} to {self.schedule.end_time})"
        return f"{self.title} (organizer: {organizer}, no schedule)"

    def save(self, *args, **kwargs):
        if self.organizer == 'student' and not self.student_organizer:
            raise ValueError("For the organizer, you must select a student.")
        if self.organizer == 'Staff' and not self.staff_organizer:
            raise ValueError("For the organizer of the master, you must choose a master.")
        if self.student_organizer and self.staff_organizer:
            raise ValueError("You can only choose one organizer (student or teacher).")
        super().save(*args, **kwargs)


class ReservationNotification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_reservation = models.ForeignKey('Reservation', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.recipient.username} at {self.created_at}"        