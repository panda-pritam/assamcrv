from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vdmp_progress", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="house_type",
            name="building_type",
            field=models.CharField(
                choices=[
                    ("household", "Household"),
                    ("commercial", "Commercial"),
                    ("critical", "Critical"),
                ],
                null=True,
                blank=True,
                max_length=20,
            ),
        ),
    ]
