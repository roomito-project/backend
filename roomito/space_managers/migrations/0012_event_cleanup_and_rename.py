# space_managers/migrations/0012_event_cleanup_and_rename.py
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('space_managers', '0011_event_fill_organizer_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='organizer',
        ),
        migrations.RemoveField(
            model_name='event',
            name='student_organizer',
        ),
        migrations.RemoveField(
            model_name='event',
            name='staff_organizer',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='organizer_user',
            new_name='organizer',
        ),
    ]
