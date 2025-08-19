from django.db import migrations

def create_default_features(apps, schema_editor):
    SpaceFeature = apps.get_model('space_managers', 'SpaceFeature')
    features = [
        'نمازخونه',
        'سیستم صوتی و میکروفون',
        'پروژکتور',
        'شبکه وایفای و یا کابل LAN',
        'تخته هوشمند',
        'تخته وایتبرد',
        'سیستم تهویه',         
        'میز و صندلی قابل جابه جایی',
        'صندلی های چرمی',
        'امکان تبدیل به کارگاه عملی',
        'امکان تبدیل به فضای نمایشگاهی',
        'سالن انتظار برای استراحت'
    ]
    for feature_name in features:
        SpaceFeature.objects.get_or_create(name=feature_name)

class Migration(migrations.Migration):
    dependencies = [
        ('space_managers', '0001_initial'),  
    ]

    operations = [
        migrations.RunPython(create_default_features),
    ]