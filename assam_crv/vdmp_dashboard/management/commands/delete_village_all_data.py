from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from village_profile.models import tblVillage
from vdmp_dashboard.models import (
    HouseholdSurvey,
    Commercial,
    Transformer,
    Critical_Facility,
    ElectricPole,
    VillageListOfAllTheDistricts,
    VillageRoadInfo,
    VillageRoadInfoErosion,
    VillageRoadInfoEQ,
    VillageRoadInfoWind,
    BridgeSurvey,
    Risk_Assesment,
    Risk_Assessment_with_MRD_mapping,
    villageAgricultureLandFloodInfo,
    villageAgricultureLandErosionInfo,
    villageAgricultureLandWindInfo,
    villageAgricultureLandEQInfo,
    VdmpVillageMapData,
)
from administrator.models import (
    PRA_main,
    PRA_assets,
    PRA_shelter,
    FGD_wash_summary,
    FGD_livelihood_summary,
)
from field_images.models import FieldImage
from layers.models import village_flood_raster_Files
from vdmp_progress.models import Risk_Assessment_Result


MODEL_GROUPS = {
    "survey": [
        HouseholdSurvey,
        Commercial,
        Transformer,
        Critical_Facility,
        ElectricPole,
        VillageListOfAllTheDistricts,
        VillageRoadInfo,
        VillageRoadInfoErosion,
        VillageRoadInfoEQ,
        VillageRoadInfoWind,
        BridgeSurvey,
        PRA_main,
        PRA_assets,
        PRA_shelter,
        FGD_wash_summary,
        FGD_livelihood_summary,
    ],
    "hazard": [
        Risk_Assesment,
        Risk_Assessment_with_MRD_mapping,
        Risk_Assessment_Result,
        villageAgricultureLandFloodInfo,
        villageAgricultureLandErosionInfo,
        villageAgricultureLandWindInfo,
        villageAgricultureLandEQInfo,
    ],
    "gis": [
        VdmpVillageMapData,
        village_flood_raster_Files,
    ],
    "images": [
        FieldImage,
    ],
}

FILE_FIELD_MAP = {
    VdmpVillageMapData: [
        "distribution_of_building",
        "road_infrastructure",
        "landuse",
        "flood_erosion",
        "essential_facilities",
        "electrical_infrastructure",
    ],
    village_flood_raster_Files: ["raster_file"],
    FieldImage: ["image"],
}


def delete_files(queryset, model):
    fields = FILE_FIELD_MAP.get(model, [])
    if not fields:
        return
    for obj in queryset:
        for field in fields:
            file_field = getattr(obj, field, None)
            if file_field:
                file_field.delete(save=False)


class Command(BaseCommand):
    help = "Delete village data (images, survey, hazard, GIS) for a village."

    def add_arguments(self, parser):
        parser.add_argument("--village-id", type=int, help="Village ID.")
        parser.add_argument("--village-code", help="Village code.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show counts without deleting.",
        )
        parser.add_argument(
            "--no-delete-files",
            action="store_true",
            help="Do not delete media files, only database records.",
        )

    def handle(self, *args, **options):
        village_id = options.get("village_id")
        village_code = options.get("village_code")
        dry_run = options.get("dry_run")
        delete_files_flag = not options.get("no_delete_files")

        if not village_id and not village_code:
            raise CommandError("Provide --village-id or --village-code.")
        if village_id and village_code:
            raise CommandError("Provide only one of --village-id or --village-code.")

        if village_id:
            village = tblVillage.objects.filter(id=village_id).first()
        else:
            village = tblVillage.objects.filter(code=village_code).first()

        if not village:
            raise CommandError("Village not found.")

        totals = {}

        with transaction.atomic():
            for group_name, models in MODEL_GROUPS.items():
                group_total = 0
                for model in models:
                    qs = model.objects.filter(village=village)
                    count = qs.count()
                    if count and not dry_run:
                        if delete_files_flag:
                            delete_files(qs, model)
                        deleted, _ = qs.delete()
                        count = deleted
                    group_total += count
                totals[group_name] = group_total

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Village: {village.id} ({village.code}) - "
                f"survey={totals.get('survey', 0)}, "
                f"hazard={totals.get('hazard', 0)}, "
                f"gis={totals.get('gis', 0)}, "
                f"images={totals.get('images', 0)}"
            )
        )
