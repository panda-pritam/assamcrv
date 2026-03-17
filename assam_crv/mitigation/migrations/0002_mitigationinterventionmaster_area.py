from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mitigation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mitigationinterventionmaster",
            name="area",
            field=models.DecimalField(default=450.0, max_digits=12, decimal_places=2),
        ),
    ]
