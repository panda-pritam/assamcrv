from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from village_profile.models import tblVillage
import json

@csrf_exempt
@require_POST
def delete_village_data(request):
    try:
        data = json.loads(request.body)
        data_type = data.get('data_type')
        village_codes = data.get('village_codes', [])
        
        if not data_type or not village_codes:
            return JsonResponse({"status": "error", "error": "Missing data_type or village_codes"}, status=400)
        
        from vdmp_dashboard.models import (HouseholdSurvey, Transformer, Commercial, Critical_Facility, 
                                         ElectricPole, VillageListOfAllTheDistricts, VillageRoadInfo, 
                                         VillageRoadInfoErosion, BridgeSurvey, Risk_Assesment)
        from administrator.models import PRA_main, PRA_assets, PRA_shelter, FGD_wash_summary, FGD_livelihood_summary
        
        MODEL_MAP = {
            "household": HouseholdSurvey,
            "transformer": Transformer,
            "critical_facility": Critical_Facility,
            "commercial": Commercial,
            "electric_poles": ElectricPole,
            "villagesOfAllTheDistricts": VillageListOfAllTheDistricts,
            "VillageRoadInfo": VillageRoadInfo,
            "VillageRoadInfoErosion": VillageRoadInfoErosion,
            "bridge_survey": BridgeSurvey,
            "risk_assesment": Risk_Assesment,
            "pra_main": PRA_main,
            "pra_assets": PRA_assets,
            "pra_shelter": PRA_shelter,
            "fgd_wash_summary": FGD_wash_summary,
            "fgd_livelihood_summary": FGD_livelihood_summary,
        }
        
        if data_type not in MODEL_MAP:
            return JsonResponse({"status": "error", "error": "Invalid data_type"}, status=400)
        
        model_class = MODEL_MAP[data_type]
        deleted_count = 0
        
        for vill_code in village_codes:
            try:
                village = tblVillage.objects.get(code=vill_code)
                count, _ = model_class.objects.filter(village=village).delete()
                deleted_count += count
            except ObjectDoesNotExist:
                continue
        
        return JsonResponse({
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} records for {len(village_codes)} villages"
        })
        
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)