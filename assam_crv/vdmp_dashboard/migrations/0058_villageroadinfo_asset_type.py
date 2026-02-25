from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vdmp_dashboard", "0057_otherdata"),
    ]

    operations = [
        migrations.AddField(
            model_name="villageroadinfo",
            name="asset_type",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
