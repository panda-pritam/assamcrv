from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("vdmp_progress", "0014_roadtype_bridgetype_electrictype"),
        ("mitigation", "0002_mitigationinterventionmaster_area"),
    ]

    operations = [
        migrations.AddField(
            model_name="mitigationinterventionmaster",
            name="bridge_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="vdmp_progress.bridgetype",
            ),
        ),
        migrations.AddField(
            model_name="mitigationinterventionmaster",
            name="electric_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="vdmp_progress.electrictype",
            ),
        ),
        migrations.AddField(
            model_name="mitigationinterventionmaster",
            name="housing_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="vdmp_progress.house_type",
            ),
        ),
        migrations.AddField(
            model_name="mitigationinterventionmaster",
            name="road_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="vdmp_progress.roadtype",
            ),
        ),
        migrations.RemoveField(
            model_name="mitigationinterventionmaster",
            name="vulnerable_asset",
        ),
    ]
