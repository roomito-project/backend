from django.db import migrations

def add_hour_slots(apps, schema_editor):
    HourSlot = apps.get_model('space_managers', 'HourSlot')
    hour_slots = [
        (1, "7:00-8:00"),
        (2, "8:00-9:00"),
        (3, "9:00-10:00"),
        (4, "10:00-11:00"),
        (5, "11:00-12:00"),
        (6, "12:00-13:00"),
        (7, "13:00-14:00"),
        (8, "14:00-15:00"),
        (9, "15:00-16:00"),
        (10, "16:00-17:00"),
        (11, "17:00-18:00"),
        (12, "18:00-19:00"),
    ]
    
    for code, time_range in hour_slots:
        HourSlot.objects.get_or_create(code=code, defaults={'time_range': time_range})

class Migration(migrations.Migration):
    dependencies = [
        ('space_managers', '0005_hourslot_alter_schedule_end_hour_code_and_more'),
    ]

    operations = [
        migrations.RunPython(add_hour_slots),
    ]