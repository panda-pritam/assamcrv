# Generated migration for adding geojson_file field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('village_profile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tblvillage',
            name='geojson_file',
            field=models.FileField(blank=True, null=True, upload_to='village_geojson/'),
        ),
    ]