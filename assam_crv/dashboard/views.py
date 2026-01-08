from django.shortcuts import render
from vdmp_dashboard.models import HouseholdSurvey, Transformer, ElectricPole, VillageRoadInfo, Critical_Facility
from utils import apply_location_filters, get_village_codes
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from shapefiles.models import PraBoundary,ExposureRiver
from django.db.models import Count, Q, FloatField
from django.db.models.functions import Cast

def home(request):
    return render(request, 'dashboard/dashboard.html')

def mitigation_intervention(request):
    return render(request, 'mitigation/mitigation_intervention.html')

def other_data(request):
    return render(request, 'other_data/other_data.html')





def calculate_flood_percentage(queryset, threshold=0.5):
    # Filter nulls and cast once
    qs = queryset.filter(flood_depth_m__isnull=False).annotate(
        flood_depth_val=Cast('flood_depth_m', FloatField())
    )

    # Aggregate total and count of floods in a single query
    agg = qs.aggregate(
        total=Count('id'),
        flood_entries=Count('id', filter=Q(flood_depth_val__gte=threshold))
    )

    total = agg['total']
    count_flood = agg['flood_entries']

    percentage = (count_flood / total * 100) if total else 0

    if total == 0:
        return {
            "total_entries": 0,
            "flood_entries": 0,
            "resiliant": 0.0,
            "no_resiliant": 0.0,
        }
    
    resiliant_percentage = round(percentage, 2)
    no_resiliant = round(100 - percentage, 2)

    return {
        "total_entries": total,
        "flood_entries": count_flood,
        "resiliant": resiliant_percentage ,
        "no_resiliant": no_resiliant,
    }



@api_view(['GET'])
def dashboard_chart_data(request):
    # STEP 1: Extract location filter parameters
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')

    # === HouseholdSurvey ===
    hh_data = HouseholdSurvey.objects.select_related(
        'village', 'village__gram_panchayat', 'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district'
    )
    hh_data = apply_location_filters(hh_data, district_id, circle_id, gram_panchayat_id, village_id)
    hh_stats = calculate_flood_percentage(hh_data)

    # === Critical Facility ===
    cf_data = Critical_Facility.objects.select_related(
        'village', 'village__gram_panchayat', 'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district'
    )
    cf_data = apply_location_filters(cf_data, district_id, circle_id, gram_panchayat_id, village_id)
    cf_stats = calculate_flood_percentage(cf_data)

    # === Transformer ===
    tran_data = Transformer.objects.select_related(
        'village', 'village__gram_panchayat', 'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district'
    )
    tran_data = apply_location_filters(tran_data, district_id, circle_id, gram_panchayat_id, village_id)
    tran_stats = calculate_flood_percentage(tran_data)

    # === Electric Pole ===
    ep_data = ElectricPole.objects.select_related(
        'village', 'village__gram_panchayat', 'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district'
    )
    ep_data = apply_location_filters(ep_data, district_id, circle_id, gram_panchayat_id, village_id)
    ep_stats = calculate_flood_percentage(ep_data)

    # === Village Road Info ===
    vr_data = VillageRoadInfo.objects.select_related(
        'village', 'village__gram_panchayat', 'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district'
    )
    vr_data = apply_location_filters(vr_data, district_id, circle_id, gram_panchayat_id, village_id)
    vr_stats = calculate_flood_percentage(vr_data)

    village_codes = get_village_codes(district_id, circle_id, gram_panchayat_id, village_id)
    flood_data = PraBoundary.objects.filter(vill_id__in=village_codes).values('area_ha', 'affarea_ha')
    #sum of lood_data area_ha
    total_area_ha = sum([x['area_ha'] for x in flood_data])
    #sum of flood_data affarea_ha
    total_affarea_ha = sum([x['affarea_ha'] for x in flood_data])
    #flood percentage
    flood_percentage = (total_affarea_ha / total_area_ha * 100) if total_area_ha else 0
    no_flood_percentage = 100 - flood_percentage if flood_percentage else 0

    flood_resiliant = {
        "total_entries": flood_data.count(),
        "flood_entries": flood_data.filter(affarea_ha__gt=0).count(),
        "resiliant": float(round(no_flood_percentage,2)),
        "no_resiliant": float(round(flood_percentage,2)),
    }

    bank_erosion_data = ExposureRiver.objects.filter(vill_id__in=village_codes).values('length_m', 'erosion_m')
    total_erosion_m = sum([x['erosion_m'] for x in bank_erosion_data if x['erosion_m'] is not None])
    total_length_m = sum([x['length_m'] for x in bank_erosion_data if x['length_m'] is not None])
    erosion_percentage = (total_erosion_m / total_length_m * 100) if total_length_m else 0
    no_erosion_percentage = 100 - erosion_percentage if erosion_percentage else 0
    
    # STEP 11: Calculate total bridge length in kilometers
    bank_erosion_data = {
        "total_entries": bank_erosion_data.count(),
        "flood_entries": bank_erosion_data.filter(erosion_m__gt=0).count(),
        "resiliant": float(round(no_erosion_percentage, 2)),
        "no_resiliant": float(round(erosion_percentage, 2)),
    }

    dummy = {
        "total_entries": 50,
        "flood_entries": 40,
        "resiliant": 78.5,
        "no_resiliant": 21.5,
    }

    #This label is used in the frontend so don't change it
    resiliant_housing ={
        "Housing Resilance": hh_stats,
        "Flood Resiliance": flood_resiliant,  # Placeholder for future flood resilience data
        "Riverbank Under Erosion": bank_erosion_data,  # Placeholder for future riverbank erosion data
    }

    resiliant_infrastructure ={
        "Resiliant Critical Facility": cf_stats,
        "Resiliant Transformer": tran_stats,
        "Resiliant Electric Pole": ep_stats,
        "Resiliant Road": vr_stats,
        "Resiliant Bridge": dummy,  # Placeholder for future bridge resilience data
        "Resiliant Shelter": dummy,  # Placeholder for future culvert resilience data
    }



    # Final JSON response
    return Response({
        "resiliant_housing": resiliant_housing,
        "resiliant_infrastructure": resiliant_infrastructure,
    })
