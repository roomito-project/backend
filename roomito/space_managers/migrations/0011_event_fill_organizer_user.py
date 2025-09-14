# space_managers/migrations/0011_event_fill_organizer_user.py
from django.db import migrations


def forwards(apps, schema_editor):
    Event = apps.get_model('space_managers', 'Event')
    Student = apps.get_model('students', 'Student')
    Staff = apps.get_model('staffs', 'Staff')

    for ev in Event.objects.all().only('id', 'organizer', 'student_organizer_id', 'staff_organizer_id'):
        user_id = None
        if ev.organizer == 'student' and ev.student_organizer_id:
            stu = Student.objects.filter(id=ev.student_organizer_id).select_related('user').first()
            if stu and getattr(stu, 'user_id', None):
                user_id = stu.user_id
        elif ev.organizer == 'staff' and ev.staff_organizer_id:
            stf = Staff.objects.filter(id=ev.staff_organizer_id).select_related('user').first()
            if stf and getattr(stf, 'user_id', None):
                user_id = stf.user_id

        if user_id:
            Event.objects.filter(id=ev.id).update(organizer_user_id=user_id)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('space_managers', '0010_event_add_new_fields'),
        ('students', '0001_initial'),
        ('staffs', '0002_alter_staff_user'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
