from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from staffs.models import Staff
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
    SPACE_TYPES = (
        ('hall', 'hall'),
        ('class', 'Class'),
        ('labratory', 'Labratory'),
        ('office', 'Office')
    )
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    phone_number = models.CharField(max_length=11, null=True, blank=True)
    description = models.TextField(default="no description")
    space_type = models.CharField(choices=SPACE_TYPES,max_length=20)
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


class HourSlot(models.Model):
    code = models.PositiveSmallIntegerField(primary_key=True)
    time_range = models.CharField(max_length=11, unique=True)  

    def __str__(self):
        return self.time_range

    class Meta:
        ordering = ['code']


class Schedule(models.Model):
    start_hour_code = models.ForeignKey(HourSlot, on_delete=models.PROTECT, related_name='start_schedules')
    end_hour_code = models.ForeignKey(HourSlot, on_delete=models.PROTECT, related_name='end_schedules')
    date = models.DateField(default=timezone.now)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.space.name} - {self.date} - {self.start_hour_code} till {self.end_hour_code}"

    def clean(self):
        if self.start_hour_code.code == self.end_hour_code.code:
            raise ValidationError("Start and end hour codes cannot be the same.")
        if self.end_hour_code.code < self.start_hour_code.code:
            raise ValidationError("End hour code must be after start hour code.")

        existing = Schedule.objects.filter(
            space=self.space,
            date=self.date
        ).exclude(pk=self.pk)
        for schedule in existing:
            if (self.start_hour_code.code <= schedule.end_hour_code.code and
                self.end_hour_code.code >= schedule.start_hour_code.code):
                raise ValidationError("This time conflicts with another schedule on the same date.")

    @property
    def is_locked(self):
        existing = Schedule.objects.filter(
            space=self.space,
            date=self.date
        ).exclude(pk=self.pk)
        for schedule in existing:
            if (self.start_hour_code.code <= schedule.end_hour_code.code and
                self.end_hour_code.code >= schedule.start_hour_code.code):
                return True
        return False

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
        ('staff', 'Staff'),
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
    hosting_association = models.CharField(max_length=100, null=True, blank=True)
    hosting_organizations = models.CharField(max_length=200, null=True, blank=True)
    responsible_organizer = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    manager_comment = models.TextField(null=True, blank=True)

    def __str__(self):
        reservee_name = self.student.first_name if self.student else (self.staff.first_name if self.staff else "unknown")
        if self.schedule:
            return (f"{self.reservation_type} - {self.schedule.date} "
                    f"{self.schedule.start_hour_code.time_range} to {self.schedule.end_hour_code.time_range} "
                    f"(reservee: {reservee_name}, status: {self.status})")
        return f"{self.reservation_type} - no schedule (reservee: {reservee_name}, status: {self.status})"


    def save(self, *args, **kwargs):
        if self.student and self.staff:
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
    description = models.CharField(max_length=500, default='no description')
    schedule = models.OneToOneField(Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_instance')

    def __str__(self):
        organizer = (
            self.student_organizer.first_name if self.student_organizer else
            self.staff_organizer.first_name if self.staff_organizer else "unknown"
        )
        if self.schedule:
            return f"{self.title} (organizer: {organizer}, {self.schedule.date})"
        return f"{self.title} (organizer: {organizer}, no schedule)"

    def save(self, *args, **kwargs):
        if self.organizer == 'student' and not self.student_organizer:
            raise ValueError("For the organizer, you must select a student.")
        if self.organizer == 'staff' and not self.staff_organizer:
            raise ValueError("For the organizer, you must select a staff.")
        if self.student_organizer and self.staff_organizer:
            raise ValueError("You can only choose one organizer (student or staff).")
        super().save(*args, **kwargs)


class ReservationNotification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_reservation = models.ForeignKey('Reservation', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.recipient.username} at {self.created_at}"        