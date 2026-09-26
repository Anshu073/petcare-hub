from django.db import migrations, models

def load_areas(apps, schema_editor):
    Area = apps.get_model('test2', 'Area')
    areas = [
        {'area_name': 'Satellite', 'pincode': 380015},
        {'area_name': 'Vastrapur', 'pincode': 380015},
        {'area_name': 'Prahladnagar', 'pincode': 380015},
        {'area_name': 'Bodakdev', 'pincode': 380054},
        {'area_name': 'Maninagar', 'pincode': 380008},
        {'area_name': 'Naranpura', 'pincode': 380013},
        {'area_name': 'Bopal', 'pincode': 380058},
        {'area_name': 'Ghatlodia', 'pincode': 380061},
        {'area_name': 'Chandkheda', 'pincode': 382424},
        {'area_name': 'usmanpura', 'pincode': 845210},
    ]
    for area in areas:
        Area.objects.get_or_create(**area)

class Migration(migrations.Migration):
    dependencies = [
        ('test2', '0046_feedback_sentiment_feedback_sentiment_reason'),
    ]
    operations = [
        migrations.AlterField(
            model_name='area',
            name='area_name',
            field=models.CharField(max_length=50),
        ),
        migrations.RunPython(load_areas),  # yeh already hai
    ]