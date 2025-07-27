from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from professors.models import Professor

class SpaceManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True) 
    email = models.EmailField()
    spaces = models.ManyToManyField('Space', help_text="managed spaces")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Space(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.IntegerField()
    space_manager = models.ForeignKey(SpaceManager, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"      

class Reservation(models.Model):
    RESERVATION_TYPES = (
        ('event', 'Event'),
        ('class', 'Class'),
        ('gathering', 'Gathering'),
    )

    RESERVEE_TYPES = (
        ('student', 'Student'),
        ('professor', 'Professor'),
    )

    STATUSES = (
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPES)
    date = models.DateField()
    reservee_type = models.CharField(max_length=20, choices=RESERVEE_TYPES)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(default='no description')            
    status = models.CharField(max_length=20, choices=STATUSES, default='under_review')
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True, )
    schedule = models.OneToOneField('Schedule', on_delete=models.CASCADE, null=True, blank=True, related_name='reservation_instance')
    
    def __str__(self):
        reservee_name = self.student.first_name if self.student else self.professor.first_name if self.professor else "unknown"
        return f"{self.reservation_type} - {self.date} (reservee: {reservee_name}, status: {self.status})"

    def save(self, *args, **kwargs):
        if self.student and self.professor:
            raise ValueError("You can only choose one student or one professor as the reservee.")
        if self.reservee_type == 'student' and not self.student:
            raise ValueError("For the student reservee type, you must select a student.")
        if self.reservee_type == 'professor' and not self.professor:
            raise ValueError("For the type of the reservee, you must select a teacher.")
        super().save(*args, **kwargs)
    
class Schedule(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='schedule_instance')
    
    def __str__(self):
        return f"{self.space.name} - {self.start_time} till {self.end_time}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time <= self.start_time:
            raise ValidationError("The end time must be after the start time.")
        existing_schedules = Schedule.objects.filter(space=self.space).exclude(id=self.id if self.id else None)
        for schedule in existing_schedules:
            if self.start_time < schedule.end_time and self.end_time > schedule.start_time:
                raise ValidationError("This time conflicts with another schedule.")

    def save(self, *args, **kwargs):
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
        ('professor', 'Professor'),
    )
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    date = models.DateField()
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    poster = models.ImageField(upload_to="event_posters/", null=True, blank=True)
    organizer = models.CharField(max_length=20, choices=ORGANIZER_TYPES)
    student_organizer = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    professor_organizer = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(default='no description')            

    def __str__(self):
        organizer = self.student_organizer.first_name if self.student_organizer else self.professor_organizer.first_name if self.professor_organizer else "unknown"
        return f"{self.title} (organizer: {organizer})"

    def save(self, *args, **kwargs):
        if self.organizer == 'student' and not self.student:
            raise ValueError("For the organizer, you must select a student.")
        if self.organizer == 'professor' and not self.professor:
            raise ValueError("For the organizer of the master, you must choose a master.")
        if self.student and self.professor:
            raise ValueError("You can only choose one organizer (student or teacher).")
        super().save(*args, **kwargs)