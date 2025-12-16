from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required, user_passes_test
from .serializers import  HouseholdSurveySerializer
from utils import (
    HOUSEHOLD_MAPPING, apply_location_filters, get_village_codes, BRIDGE_SURVEY_INFO, TRANSFORMER_MAPPING, 
    CRITICAL_FACILITY, COMMERCIAL_MAPPING, ELECTRIC_POLES,VILLAGES_OF_ALL_THE_DISTRICTS,VILLAGE_ROAD_INFO_MAPPING,VILLAGE_ROAD_INFO_EROSION
    ,RISK_ASSESMENT_MAPPING)
import pandas as pd
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from .models import (HouseholdSurvey, tblVillage, Transformer, Commercial,Critical_Facility,ElectricPole,VillageListOfAllTheDistricts,
                     VillageRoadInfo,VillageRoadInfoErosion, BridgeSurvey, Risk_Assesment)
from django.db.models.functions import Cast
from django.db.models import Sum, Count, Q, FloatField, Avg, Max
from django.db import models as django_models
from .pdf.main import generate_pdf
import time
from datetime import datetime
import requests
from collections import defaultdict
from shapefiles.models import PraBoundary,ExposureRiver
import re

def vdmp_dashboard(request):
    """Render the VDMP dashboard page.
    Returns the HTML page for the VDMP dashboard view."""
    user_location = {
        'district_id': getattr(request.user, 'district', None) and request.user.district.id,
        'district_name': getattr(request.user, 'district', None) and request.user.district.name,
        'circle_id': getattr(request.user, 'circle', None) and request.user.circle.id,
        'circle_name': getattr(request.user, 'circle', None) and request.user.circle.name,
        'gram_panchayat_id': getattr(request.user, 'gram_panchayat', None) and request.user.gram_panchayat.id,
        'gram_panchayat_name': getattr(request.user, 'gram_panchayat', None) and request.user.gram_panchayat.name,
        'village_id': getattr(request.user, 'village', None) and request.user.village.id,
        'village_name': getattr(request.user, 'village', None) and request.user.village.name,
    }
    return render(request, 'vdmp_dashboard/dashboard.html', {'user_location': user_location})

@csrf_exempt
@require_POST
def upload_data_vdmp(request):
    start_time = time.time()
    print("===== Upload started =====")
    
    try:
        file = request.FILES.get("file")
        data_type = request.POST.get("data_type")
        # print(f"File name: {file.name if file else 'None'}")
        # print(f"Data type: {data_type}")

        if not file:
            print("No file uploaded")
            return JsonResponse({"status": "error", "error": "No file uploaded"}, status=400)
        if data_type not in ["household", "transformer", "critical_facility", "commercial", "electric_poles", "villagesOfAllTheDistricts", 
                             "VillageRoadInfo","VillageRoadInfoErosion", "bridge_survey", "risk_assesment"]:
            print("Invalid data type")
            return JsonResponse({"status": "error", "error": "Invalid data_type"}, status=400)

        try:
            read_start = time.time()
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"status": "error", "error": "Unsupported file format"}, status=400)
            print(f"File read completed in {time.time() - read_start:.2f} seconds")
            print(f"Total rows: {len(df)}")

            df.columns = [col.strip().lower() for col in df.columns]
        except Exception as e:
            print("File read error:", e)
            return JsonResponse({"status": "error", "error": f"Failed to read file: {str(e)}"}, status=400)

        MODEL_MAP = {
            "household": (HOUSEHOLD_MAPPING, HouseholdSurvey),
            "transformer": (TRANSFORMER_MAPPING, Transformer),
            "critical_facility": (CRITICAL_FACILITY, Critical_Facility),
            "commercial": (COMMERCIAL_MAPPING, Commercial),
            "electric_poles": (ELECTRIC_POLES, ElectricPole),
            "villagesOfAllTheDistricts": (VILLAGES_OF_ALL_THE_DISTRICTS, VillageListOfAllTheDistricts),
            "VillageRoadInfo": (VILLAGE_ROAD_INFO_MAPPING, VillageRoadInfo),
            "VillageRoadInfoErosion": (VILLAGE_ROAD_INFO_EROSION, VillageRoadInfoErosion),
            "bridge_survey": (BRIDGE_SURVEY_INFO, BridgeSurvey),
            "risk_assesment": (RISK_ASSESMENT_MAPPING, Risk_Assesment),
        }

        mapping, model_class = MODEL_MAP[data_type]
        created = 0
        updated = 0
        failed = []
        village_cache = {}

        for index, row in df.iterrows():
            try:
                # if index % 500 == 0:
                #     print(f"Processing row {index}/{len(df)} ... elapsed {time.time() - start_time:.2f} sec")

                data = {}
                for excel_field, model_field in mapping.items():
                    excel_field = excel_field.lower()
                    data[model_field] = str(row.get(excel_field, '')).strip()

                # for excel_field, model_field in mapping.items():
                #     value = str(row.get(excel_field, '')).strip()
                #     value = re.sub(r'\s+', ' ', value)   # normalize spaces
                #     if value.lower() == "nan":
                #         value = ""
                #     data[model_field] = value

                vill_code = data.get("village_code")
                if vill_code:
                    vill_code = str(vill_code).strip()  # remove leading/trailing spaces
                    vill_code = vill_code.replace("_x000D_", "").replace("\r", "").replace("\n", "")
                    vill_code = re.sub(r"\s+", "", vill_code)  # remove all whitespace
                else:
                    failed.append(f"Row {index+2}: Missing village_code")
                    continue

                if vill_code in village_cache:
                    village = village_cache[vill_code]
                else:
                    village = tblVillage.objects.get(code=vill_code)
                    village_cache[vill_code] = village

                data["village"] = village
                
                # Get unique identifier for the record
                point_id = data.get("point_id")
                uid = data.get("uid")
                spatial_id = data.get("spatial_id")
                polygon_id = data.get("polygon_id")
                
                # Try to find existing record
                existing_record = None
                if point_id:
                    existing_record = model_class.objects.filter(village=village, point_id=point_id).first()
                elif uid:
                    existing_record = model_class.objects.filter(village=village, uid=uid).first()

                elif spatial_id:
                    existing_record = model_class.objects.filter(village=village, spatial_id=spatial_id).first()
                elif polygon_id:
                    existing_record = model_class.objects.filter(village=village, polygon_id=polygon_id).first()
                else:
                    # For models without point_id/uid, check by village only
                    pass
                
                if existing_record:
                    # Update existing record
                    for field, value in data.items():
                        setattr(existing_record, field, value)
                    existing_record.save()
                    updated += 1
                else:
                    # Create new record
                    model_class.objects.create(**data)
                    created += 1

            except ObjectDoesNotExist:
                failed.append(f"Row {index+2}: tblVillage not found for village_code = {vill_code}")
            except Exception as e:
                failed.append(f"Row {index+2}: {str(e)}")

        print(f"===== Upload completed in {time.time() - start_time:.2f} seconds =====")
        print("failed records:", failed)
        return JsonResponse({
            "status": "success",
            "records_created": created,
            "records_updated": updated,
            "errors": failed
        })
    
    except Exception as e:
        print("Unexpected error:", e)
        return JsonResponse({
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }, status=500)

@api_view(['POST'])
def delete_vdmp_data(request):
    village_id = request.POST.get("village_id")
    data_type = request.POST.get("data_type")

    if not village_id or not data_type:
        return Response({"error": "Missing 'village_id' or 'data_type'."}, status=status.HTTP_400_BAD_REQUEST)
    
    if data_type not in ["household", "transformer", "critical_facility", "commercial", "electric_poles",
                         "villagesOfAllTheDistricts", "VillageRoadInfo", "VillageRoadInfoErosion", "bridge_survey",
                         "risk_assesment"]:
        return JsonResponse({"error": "Invalid data_type. Must be 'household', 'transformer', 'critical_facility', 'commercial', or 'electric_poles'."}, status=400)

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
    }

    if data_type not in MODEL_MAP:
        return Response({"error": "Invalid data_type."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the village or return 404
    village = get_object_or_404(tblVillage, id=village_id)
    model_class = MODEL_MAP[data_type]

    # Delete all related entries
    deleted_count, _ = model_class.objects.filter(village=village).delete()

    return Response(
        {
            "status": "success",
            "message": f"{deleted_count} record(s) deleted successfully."
        },
        status=status.HTTP_200_OK
    )


from django.db.models import Sum, Func, F
class CastDecimal(Func):
    function = 'CAST'
    template = "%(expressions)s::decimal"

@api_view(['GET'])
def get_household_summary_data(request):
    """
    VDMP Dashboard Summary Data API
    
    This API aggregates and processes data from multiple models to provide comprehensive
    village-level summary statistics for the VDMP dashboard.
    
    Data Sources:
    - HouseholdSurvey: Demographics, population, livestock, housing, vulnerability
    - Critical_Facility: Educational and religious facilities
    - VillageRoadInfo: Road infrastructure and flood vulnerability
    - VillageRoadInfoErosion: Road erosion vulnerability
    - GeoServer WFS: Road network spatial data
    
    Processing Steps:
    1. Extract location filters from request parameters
    2. Query and filter household survey data
    3. Calculate demographic statistics (population, households)
    4. Process housing type distributions
    5. Query critical facilities data
    6. Calculate infrastructure statistics
    7. Process vulnerability assessments
    8. Fetch spatial road data from GeoServer
    9. Aggregate all statistics into summary response
    """
    
    # STEP 1: Extract location filter parameters from request
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')

    # STEP 2: Query HouseholdSurvey data with optimized joins
    # Select related fields to avoid N+1 queries and get only required fields
    data = HouseholdSurvey.objects.select_related(
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
    ).all().values('number_of_males_including_children', 'number_of_females_including_children', 'children_below_6_years',
                   'senior_citizens', 'persons_with_disability_or_chronic_disease', 'house_type')

    # STEP 3: Apply hierarchical location filters (district -> circle -> gram panchayat -> village)
    data = apply_location_filters(data, district_id, circle_id, gram_panchayat_id, village_id)
    
    # STEP 4: Calculate housing type distribution
    # Count houses by construction type for asset summary
    kachcha_houses = data.filter(house_type='Kachcha').count()
    semi_pucca_houses = data.filter(house_type='Semi Pucca').count()
    pucca_houses = data.filter(house_type='Pucca').count()

    # STEP 5: Query Critical Facilities data for educational/religious infrastructure
    ca_data = Critical_Facility.objects.select_related(
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
    ).all().values('occupancy_type')

    # Apply same location filters to critical facilities
    ca_data = apply_location_filters(ca_data, district_id, circle_id, gram_panchayat_id, village_id)

    # STEP 6: Count facilities by type for asset summary
    school = ca_data.filter(occupancy_type='School').count()
    religous_places = ca_data.filter(occupancy_type='Religious Place').count()
    anganwadi = ca_data.filter(occupancy_type='Anganwadi').count()
    gov_office = ca_data.filter(occupancy_type='Govt Office').count()
    others = ca_data.filter(occupancy_type='Others').count()

    # STEP 7: Define safe aggregation function to handle null/empty values
    # Excludes null, empty string, and 'nan' values before summing
    def safe_sum(field):
        return data.exclude(
            Q(**{f"{field}__isnull": True}) |
            Q(**{f"{field}__in": ['', 'nan']})
        ).aggregate(
            total=Sum(Cast(field, FloatField()))  # Cast to float for numeric operations
        )['total'] or 0

    # STEP 8: Calculate demographic statistics from household survey data
    # Sum population counts across all households in filtered area
    male_pop = int(safe_sum('number_of_males_including_children'))
    female_pop = int(safe_sum('number_of_females_including_children'))
    senior_pop = int(safe_sum('senior_citizens'))
    pregnant_count = int(safe_sum('pregnant_women'))
    disabled_count = int(safe_sum('persons_with_disability_or_chronic_disease'))
    
    # Calculate total population (male + female, excluding seniors to avoid double counting)
    total_pop = male_pop + female_pop 
    
    # STEP 9: Calculate vulnerable household categories
    # Count households by economic status for priority targeting
    priority_households = data.filter(economic_status='Phh Priority Household').count()
    bpl_households = data.filter(economic_status='Bpl Below Poverty Line').count()
    
    # STEP 10: Calculate maternal health statistics
    # Combine pregnant and lactating women counts
    lactating_count = int(safe_sum('lactating_women'))
    pregnant_lactating = pregnant_count + lactating_count
    
    # STEP 11: Calculate total household count
    total_households = data.count()

    #Commercial data
    commercial_buildings_data = Commercial.objects.all()
    commercial_buildings_data = apply_location_filters(commercial_buildings_data, district_id, circle_id, gram_panchayat_id, village_id) 
    commercial_buildings_count = commercial_buildings_data.count()   

    #Transformer data
    transformer_data = Transformer.objects.all()
    transformer_data = apply_location_filters(transformer_data, district_id, circle_id, gram_panchayat_id, village_id)
    transformer_count = transformer_data.count()

    bridge_data = BridgeSurvey.objects.all()
    bridge_data = apply_location_filters(bridge_data, district_id, circle_id, gram_panchayat_id, village_id)
    bridges_count = bridge_data.count()


    total_bridge_length = (
        bridge_data.exclude(length_meters__isnull=True)
                .exclude(length_meters__in=['', 'nan'])
                .annotate(length_val=CastDecimal(F('length_meters')))
                .aggregate(total=Sum('length_val'))['total']
    )

    bridge_length_km = round(total_bridge_length, 2) if total_bridge_length else None

    village_codes = get_village_codes(district_id, circle_id, gram_panchayat_id, village_id)

    bank_erosion_data = ExposureRiver.objects.filter(vill_id__in=village_codes).values('length_m', 'erosion_m')
    total_erosion_m = sum([x['erosion_m'] for x in bank_erosion_data if x['erosion_m'] is not None])
    total_erosion_m = round(total_erosion_m/1000, 2) if total_erosion_m else None
    # STEP 12: Build initial summary data structure
    # Organize all calculated statistics into response format
    summary = {
        # Demographic Summary - Population counts by category
        'male_population': male_pop,
        'female_population': female_pop,
        'total_population': total_pop,
        'total_households': total_households,

        # Vulnerable Populations - Special categories for targeting
        'population_bl_six': int(safe_sum('children_below_6_years')),  # Children under 6
        'senior_citizens': senior_pop,
        'total_disabled': disabled_count,        
        'priority_households': priority_households,
        'bpl_households': bpl_households,
        'pregnant_lactating': pregnant_lactating,
        'lactating_women': lactating_count,
        
        # Livestock Assets - Agricultural resources
        'big_cattles': int(safe_sum('number_of_big_cattle_animals')),
        'small_cattles': int(safe_sum('number_of_small_cattle_animals')),
        'poultry_animals': int(safe_sum('number_of_poultry_animals')),

        # Housing Assets - Infrastructure by construction type
        'kachcha_houses': kachcha_houses,
        'semi_pucca_houses': semi_pucca_houses,
        'pucca_houses': pucca_houses,

        # Critical Facilities - Educational and community infrastructure
        'school': school,
        'religous_places': religous_places,
        'anganwadi': anganwadi,
        'gov_office': gov_office,
        'others': others,

        'commercial_buildings':commercial_buildings_count,
        'transformer_count':transformer_count,
        # 'bridge_length_km': f"{bridge_length_km/1000} km" if bridge_length_km else '-',
        'bridge_count': bridges_count,
        'river_erosion_length_km': f"{total_erosion_m} km" if total_erosion_m else '-',
    }

    # STEP 13: Get road infrastructure data from GeoServer spatial database
    # Fetches total road length using WFS service based on location filters
    total_road_length = get_total_road_length(district_id, circle_id, gram_panchayat_id, village_id)
    
    # Calculate flood depth statistics
    def safe_avg(field):
        return data.exclude(
            Q(**{f"{field}__isnull": True}) |
            Q(**{f"{field}__in": ['', 'nan', '0']})
        ).aggregate(
            avg=Avg(Cast(field, FloatField()))
        )['avg'] or 0
    
    def safe_max(field):
        return data.exclude(
            Q(**{f"{field}__isnull": True}) |
            Q(**{f"{field}__in": ['', 'nan', '0']})
        ).aggregate(
            max=Max(Cast(field, FloatField()))
        )['max'] or 0
    
    avg_flood_depth_m = safe_avg('flood_depth_m')
    max_flood_depth_m = safe_max('flood_depth_m')
    
    # Convert meters to feet (1 meter = 3.28084 feet)
    avg_flood_depth_ft = round(avg_flood_depth_m * 3.28084, 1) if avg_flood_depth_m else 0
    max_flood_depth_ft = round(max_flood_depth_m * 3.28084, 1) if max_flood_depth_m else 0
    
    # Calculate vulnerability data
    # Flood vulnerable houses (flood_class: 0.5 - 1.0 M, >1.0 M)
    flood_vulnerable_houses = data.filter(
        flood_class__in=['0.5 - 1.0 M', '>1.0 M']
    ).count()
    
    # Erosion vulnerable houses (erosion_class: 100, 50)
    erosion_vulnerable_houses = data.filter(
        erosion_class__in=['100', '50']
    ).count()
    
    # Get road data for vulnerability calculations
    road_data = VillageRoadInfo.objects.select_related(
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
    ).all()
    
    road_erosion_data = VillageRoadInfoErosion.objects.select_related(
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
    ).all()
    
    road_data = apply_location_filters(road_data, district_id, circle_id, gram_panchayat_id, village_id)
    road_erosion_data = apply_location_filters(road_erosion_data, district_id, circle_id, gram_panchayat_id, village_id)
    
    # Flood vulnerable roads (sum of road_length_m for flood_class: 0.5 - 1.0 M, >1.0 M)
    flood_vulnerable_roads_m = road_data.filter(
        flood_class__in=['0.5 - 1.0 m', '>1.0 m']
    ).aggregate(total=Sum('road_length_m'))['total'] or 0
    flood_vulnerable_roads = round(flood_vulnerable_roads_m / 1000, 2)  # Convert to km
    
    # Erosion vulnerable roads (sum of road_length_m for erosion_class: 100, 150)
    erosion_vulnerable_roads_m = road_erosion_data.filter(
        erosion_class__in=['100', '150']
    ).aggregate(total=Sum('road_length_m'))['total'] or 0
    erosion_vulnerable_roads = round(erosion_vulnerable_roads_m / 1000, 2)  # Convert to km
    
    summary['total_road_length'] = total_road_length
    summary['avg_flood_depth'] = avg_flood_depth_ft
    summary['max_flood_depth'] = max_flood_depth_ft
    summary['flood_vulnerable_houses'] = flood_vulnerable_houses
    summary['erosion_vulnerable_houses'] = erosion_vulnerable_houses
    summary['flood_vulnerable_roads'] = flood_vulnerable_roads
    summary['erosion_vulnerable_roads'] = erosion_vulnerable_roads
    return Response(summary)

def get_total_road_length(district_id=None, circle_id=None, gram_panchayat_id=None, village_id=None):
    """Get total road length based on location filters"""
    try:
        # Get village codes based on filters
        villages = tblVillage.objects.all()
        
        if village_id:
            villages = villages.filter(id=village_id)
        elif gram_panchayat_id:
            villages = villages.filter(gram_panchayat_id=gram_panchayat_id)
        elif circle_id:
            villages = villages.filter(gram_panchayat__circle_id=circle_id)
        elif district_id:
            villages = villages.filter(gram_panchayat__circle__district_id=district_id)
        
        village_codes = list(villages.values_list('code', flat=True))
        
        if not village_codes:
            return 0
            
        # Build CQL filter for multiple villages
        if len(village_codes) == 1:
            cql_filter = f"vill_id='{village_codes[0]}'"
        else:
            codes_str = "','".join(village_codes)
            cql_filter = f"vill_id IN ('{codes_str}')"
        
        wfs_url = "http://localhost:8080/geoserver/assam/ows"
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "assam:road_network",
            "outputFormat": "application/json",
            "CQL_FILTER": cql_filter
        }
        
        response = requests.get(wfs_url, params=params)
        if response.status_code != 200:
            return 0
            
        geojson = response.json()
        features = geojson.get("features", [])
        
        total_length_m = 0
        for feature in features:
            props = feature.get("properties", {})
            length_m = props.get("length", 0.0) or 0.0
            total_length_m += float(length_m)
            
        return round(total_length_m / 1000, 2)  # Convert to km
        
    except Exception as e:
        print(f"Error getting road length: {e}")
        return 0


def generate_pdf_view(request):
    village_id = request.GET.get('village_id')
    
    village = get_object_or_404(tblVillage, id=village_id) if village_id else None
    buffer = generate_pdf(village_id=village_id, village=village)
    return HttpResponse(buffer, content_type='application/pdf')


@api_view(['GET'])
def download_report(request):
    village_id = request.query_params.get('village_id')
    
    village = get_object_or_404(tblVillage, id=village_id)
    buffer = generate_pdf(village_id=village_id, village=village)
    filename = f"{village.name}_vdmp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return FileResponse(buffer, content_type='application/pdf', as_attachment=True, filename=filename)

# from django.http import StreamingHttpResponse

# @login_required
# @api_view(['GET'])
# def download_report(request):
#     village_id = request.query_params.get('village_id')

#     village = get_object_or_404(tblVillage, id=village_id)
#     buffer = generate_pdf(village_id=village_id, village=village)
#     response = StreamingHttpResponse(buffer, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="report.pdf"'
#     return response


from django.http import HttpResponse
from openpyxl import Workbook
from io import BytesIO
import zipfile
from utils import VDMP_ACTIVITIES, RESCUE_EQUEP_MASTER_LIST, TRAINING_MASTER_LIST
from training.models import tbl_Training_Activities
from rescue_equipment.models import tbl_Rescue_Equipment
from vdmp_progress.models import tblVDMP_Activity
# your mappings dictionary
TABLES_MAPPING = {
    "household": (HOUSEHOLD_MAPPING, HouseholdSurvey),
    "transformer": (TRANSFORMER_MAPPING, Transformer),
    "critical_facility": (CRITICAL_FACILITY, Critical_Facility),
    "commercial": (COMMERCIAL_MAPPING, Commercial),
    "electric_poles": (ELECTRIC_POLES, ElectricPole),
    "villagesOfAllTheDistricts": (VILLAGES_OF_ALL_THE_DISTRICTS, VillageListOfAllTheDistricts),
    "road_flood": (VILLAGE_ROAD_INFO_MAPPING, VillageRoadInfo),
    "road_erosion": (VILLAGE_ROAD_INFO_EROSION, VillageRoadInfoErosion),
    "bridge_survey": (BRIDGE_SURVEY_INFO, BridgeSurvey),
    "risk_assesment": (RISK_ASSESMENT_MAPPING, Risk_Assesment),

    "vdmp_activities": (VDMP_ACTIVITIES, tblVDMP_Activity),
    "rescue_equipments": (RESCUE_EQUEP_MASTER_LIST, tbl_Rescue_Equipment),
    "training_master": (TRAINING_MASTER_LIST, tbl_Training_Activities),
}


def generate_excel(mapping: dict, model):
    """Generate an Excel file for given mapping + model with first 3 rows"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"

    # Write headers (Excel columns)
    headers = list(mapping.keys())
    ws.append(headers)

    # Fetch first 3 rows from DB
    rows = model.objects.all()[:3]

    for row in rows:
        values = [getattr(row, mapping[col], "") for col in headers]
        ws.append(values)

    # Save to memory
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return file_stream


def download_excels_format(request):
    """API endpoint: download all excels inside a zip"""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for name, (mapping, model) in TABLES_MAPPING.items():
            file_stream = generate_excel(mapping, model)
            zf.writestr(f"{name}.xlsx", file_stream.getvalue())

    zip_buffer.seek(0)

    response = HttpResponse(
        zip_buffer,
        content_type="application/x-zip-compressed"
    )
    response["Content-Disposition"] = 'attachment; filename="all_excels.zip"'
    return response
