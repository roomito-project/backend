from django.conf import settings
from django.db import migrations
from django.contrib.auth.models import User

def fix_null_users(apps, schema_editor):
    Student = apps.get_model('students', 'Student')
    for student in Student.objects.filter(user__isnull=True):
        # ساخت یه User جدید با username و email
        username = f"temp_{student.student_id}"
        email = f"temp_{student.student_id}@example.com"
        # استفاده از create برای اطمینان از ذخیره کامل
        user = User.objects.create(
            username=username,
            email=email,
            password='defaultpass123'
        )
        # وصل کردن user به student
        student.user = apps.get_model(settings.AUTH_USER_MODEL)._default_manager.get(pk=user.pk)
        student.save()

class Migration(migrations.Migration):
    dependencies = [
        ('students', '0004_student_is_approved'),
    ]
    operations = [
        migrations.RunPython(fix_null_users),
    ]