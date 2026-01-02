from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from .models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage, district_village_mapping
from vdmp_dashboard.models import VillageListOfAllTheDistricts
from .serializers import (DistrictSerializer, CircleSerializer, GramPanchayatSerializer, VillageSerializer,
                          ListCircleSerializer, ListGramPanchayatSerializer, ListVillageSerializer, ListDistrictSerializer)
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import tempfile, os
from utils import import_location_data, is_admin_or_superuser,store_lat_lon
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connections
from django.db import transaction

from vdmp_dashboard.models import HouseholdSurvey, Transformer, Commercial,Critical_Facility,ElectricPole,VillageListOfAllTheDistricts,VillageRoadInfo,VillageRoadInfoErosion
from utils import apply_location_filters, village_apply_location_filters



@api_view(['GET'])
def get_districts(request):
    """Retrieve all districts.
    Returns a list of all districts in the system."""

    if request.method == 'GET':
        districts = tblDistrict.objects.all().order_by('name')
        serializer = DistrictSerializer(districts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_circles(request):
    """Retrieve circles based on district ID.
    Expects `district_id` as query param and returns related circles."""

    district_id = request.query_params.get('district_id')
    if district_id is None:
        return Response({"error": "district_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    circles = tblCircle.objects.select_related("district").filter(district_id=district_id).order_by('name')
    serializer = CircleSerializer(circles, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_gram_panchayats(request):
    """Retrieve gram panchayats based on circle ID.
    Expects `circle_id` as query param and returns related gram panchayats."""

    circle_id = request.query_params.get('circle_id')
    if circle_id is None:
        return Response({"error": "circle_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    gram_panchayats = tblGramPanchayat.objects.select_related("circle").filter(circle_id=circle_id).order_by('name')
    serializer = GramPanchayatSerializer(gram_panchayats, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_villages(request):
    """Retrieve villages based on gram panchayat ID.
    Expects `gram_panchayat_id` as query param and returns related villages."""

    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    if gram_panchayat_id is None:
        return Response({"error": "gram_panchayat_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    villages = tblVillage.objects.select_related("gram_panchayat__circle__district").filter(gram_panchayat_id=gram_panchayat_id).order_by('name')
    serializer = VillageSerializer(villages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def villages_by_district(request):
    """Retrieve all villages under a district.
    Expects `district_id` as query param and returns nested villages."""

    district_id = request.query_params.get('district_id')
    if district_id is None:
        return Response({"error": "district_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    villages = tblVillage.objects.select_related("gram_panchayat__circle__district").filter(gram_panchayat__circle__district_id=district_id).order_by('name')
    serializer = VillageSerializer(villages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@login_required
@api_view(['GET'])
@user_passes_test(is_admin_or_superuser)
def get_all_districts(request):
    """Retrieve all districts.
    Returns a list of all districts in the system."""

    districts = tblDistrict.objects.all().order_by('name')
    serializer = ListDistrictSerializer(districts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@login_required
@api_view(['GET'])
@user_passes_test(is_admin_or_superuser)
def get_all_circles(request):
    """Retrieve circles based on district ID.
    Expects `district_id` as query param and returns related circles."""

    district_id = request.query_params.get('district_id')
    if district_id:
        circles = tblCircle.objects.select_related("district").filter(district_id=district_id).order_by('name')
    else:
        circles = tblCircle.objects.all().order_by('name')

    serializer = ListCircleSerializer(circles, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@api_view(['GET'])
@user_passes_test(is_admin_or_superuser)
def get_all_gram_panchayats(request):
    """
    Retrieve gram panchayats based on circle ID or district ID.
    """
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')

    gram_panchayats = tblGramPanchayat.objects.select_related("circle", "circle__district").order_by('name')

    if circle_id:
        gram_panchayats = gram_panchayats.filter(circle_id=circle_id)
    elif district_id:
        gram_panchayats = gram_panchayats.filter(circle__district_id=district_id)

    serializer = ListGramPanchayatSerializer(gram_panchayats, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@api_view(['GET'])
@user_passes_test(is_admin_or_superuser)
def get_all_villages(request):
    """
    Retrieve villages based on gram panchayat ID or circle ID or district ID.
    """
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')

    villages = tblVillage.objects.select_related(
        "gram_panchayat", "gram_panchayat__circle", "gram_panchayat__circle__district"
    ).order_by('name')

    if gram_panchayat_id:
        villages = villages.filter(gram_panchayat_id=gram_panchayat_id)
    elif circle_id:
        villages = villages.filter(gram_panchayat__circle_id=circle_id)
    elif district_id:
        villages = villages.filter(gram_panchayat__circle__district_id=district_id)

    serializer = ListVillageSerializer(villages, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@api_view(['GET'])
@user_passes_test(is_admin_or_superuser)
def get_village_by_id(request, village_id):
    """Get village details by ID."""
    try:
        village = tblVillage.objects.select_related(
            'gram_panchayat__circle__district'
        ).get(id=village_id)
        serializer = ListVillageSerializer(village)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except tblVillage.DoesNotExist:
        return Response({"error": "Village not found"}, status=status.HTTP_404_NOT_FOUND)



@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
def create_district(request):
    """Create a new district.
    Expects district data in the request body."""
    serializer = ListDistrictSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
def create_circle(request):
    """Create a new circle.
    Expects circle data in the request body."""
    serializer = ListCircleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
def create_gram_panchayat(request):
    """Create a new gram panchayat.
    Expects gram panchayat data in the request body."""
    serializer = ListGramPanchayatSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
@parser_classes([MultiPartParser, FormParser])
def create_village(request):
    """Create a new village.
    Expects village data in the request body."""
    serializer = ListVillageSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                village = serializer.save()
                create_village_with_mobile_db_mapping(village, request.user)
                if village.geojson_file:
                    create_geo_data_entry(village)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def create_geo_data_entry(village):
    """Create entry in mobile_db geo_data table."""
    if not village.geojson_file:
        return
    
    # Get the mobile DB village ID from mapping
    try:
        mapping = district_village_mapping.objects.get(village=village)
        mobile_village_id = mapping.mobileDBVillageID
    except district_village_mapping.DoesNotExist:
        return  # No mapping exists, skip geo_data entry
    
    mobile_db = connections['mobile_db']
    with mobile_db.cursor() as cursor:
        # Get relative file path
        file_path = str(village.geojson_file)
        
        cursor.execute(
            'INSERT INTO public.geo_data ("countryId", "adminLevel", "adminId", lang, shapefile) VALUES (%s, %s, %s, %s, %s)',
            [91, 1, mobile_village_id, 'en', file_path]
        )


def update_geo_data_entry(village):
    """Update entry in mobile_db geo_data table."""
    if not village.geojson_file:
        return
    
    # Get the mobile DB village ID from mapping
    try:
        mapping = district_village_mapping.objects.get(village=village)
        mobile_village_id = mapping.mobileDBVillageID
    except district_village_mapping.DoesNotExist:
        return  # No mapping exists, skip geo_data entry
    
    # Get old file path from database to delete it
    mobile_db = connections['mobile_db']
    with mobile_db.cursor() as cursor:
        cursor.execute(
            'SELECT shapefile FROM public.geo_data WHERE "adminId" = %s AND "countryId" = 91',
            [mobile_village_id]
        )
        result = cursor.fetchone()
        if result:
            old_file_path = result[0]
            # Delete old file if it exists
            if old_file_path and os.path.exists(old_file_path):
                os.remove(old_file_path)
    
    with mobile_db.cursor() as cursor:
        # Get relative file path
        file_path = str(village.geojson_file)
        
        # Check if entry exists
        cursor.execute(
            'SELECT id FROM public.geo_data WHERE "adminId" = %s AND "countryId" = 91',
            [mobile_village_id]
        )
        
        if cursor.fetchone():
            # Update existing entry
            cursor.execute(
                'UPDATE public.geo_data SET shapefile = %s WHERE "adminId" = %s AND "countryId" = 91',
                [file_path, mobile_village_id]
            )
        else:
            # Create new entry
            cursor.execute(
                'INSERT INTO public.geo_data ("countryId", "adminLevel", "adminId", lang, shapefile) VALUES (%s, %s, %s, %s, %s)',
                [91, 1, mobile_village_id, 'en', file_path]
            )


def create_village_with_mobile_db_mapping(village, user):
    """Create village entry in mobile_db and maintain mapping."""
    with transaction.atomic():
        # Get district info
        district = village.gram_panchayat.circle.district
        
        # Insert into mobile_db
        mobile_db = connections['mobile_db']
        with mobile_db.cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO public.villages (district_id, district_name, village_name, created_on, updated_on) VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id",
                    [district.code, district.name, village.name]
                )
                mobile_village_id = cursor.fetchone()[0]
            except Exception as e:
                # Reset sequence and try again
                cursor.execute("SELECT setval('public.villages_id_seq', (SELECT MAX(id) FROM public.villages))")
                cursor.execute(
                    "INSERT INTO public.villages (district_id, district_name, village_name, created_on, updated_on) VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id",
                    [district.code, district.name, village.name]
                )
                mobile_village_id = cursor.fetchone()[0]
        
        # Create mapping record
        district_village_mapping.objects.create(
            district=district,
            district_code=district.code,
            circle=village.gram_panchayat.circle,
            gram_panchayat=village.gram_panchayat,
            village=village,
            village_code=village.code,
            mobileDBVillageID=str(mobile_village_id),
            mobileDBDistrictID=district.code,
            userID=user
        )


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
def create_village_with_mapping(request):
    """Create village in both default DB and mobile_db with mapping."""
    serializer = ListVillageSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                village = serializer.save()
                create_village_with_mobile_db_mapping(village, request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['PATCH'])
@user_passes_test(is_admin_or_superuser)
def update_district(request, district_id):
    """Update an existing district.
    Expects district data in the request body."""
    try:
        district = tblDistrict.objects.get(id=district_id)
    except tblDistrict.DoesNotExist:
        return Response({"error": "District not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ListDistrictSerializer(district, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['PATCH'])
@user_passes_test(is_admin_or_superuser)
def update_circle(request, circle_id):
    """Update an existing circle.
    Expects circle data in the request body."""
    try:
        circle = tblCircle.objects.get(id=circle_id)
    except tblCircle.DoesNotExist:
        return Response({"error": "Circle not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ListCircleSerializer(circle, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['PATCH'])
@user_passes_test(is_admin_or_superuser)
def update_gram_panchayat(request, gram_panchayat_id):
    """Update an existing gram panchayat.
    Expects gram panchayat data in the request body."""
    try:
        gram_panchayat = tblGramPanchayat.objects.get(id=gram_panchayat_id)
    except tblGramPanchayat.DoesNotExist:
        return Response({"error": "Gram Panchayat not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ListGramPanchayatSerializer(gram_panchayat, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['PATCH'])
@user_passes_test(is_admin_or_superuser)
@parser_classes([MultiPartParser, FormParser])
def update_village(request, village_id):
    """Update an existing village.
    Expects village data in the request body."""
    try:
        village = tblVillage.objects.get(id=village_id)
    except tblVillage.DoesNotExist:
        return Response({"error": "Village not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ListVillageSerializer(village, data=request.data, partial=True)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                village = serializer.save()
                if 'geojson_file' in request.data and village.geojson_file:
                    update_geo_data_entry(village)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['DELETE'])
@user_passes_test(is_admin_or_superuser)
def delete_district(request, district_id):
    """Delete an existing district."""
    try:
        district = tblDistrict.objects.get(id=district_id)
    except tblDistrict.DoesNotExist:
        return Response({"error": "District not found"}, status=status.HTTP_404_NOT_FOUND)

    district.delete()
    return Response({"message": "District deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@login_required
@api_view(['DELETE'])
@user_passes_test(is_admin_or_superuser)
def delete_circle(request, circle_id):
    """Delete an existing circle."""
    try:
        circle = tblCircle.objects.get(id=circle_id)
    except tblCircle.DoesNotExist:
        return Response({"error": "Circle not found"}, status=status.HTTP_404_NOT_FOUND)

    circle.delete()
    return Response({"message": "Circle deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@login_required
@api_view(['DELETE'])
@user_passes_test(is_admin_or_superuser)
def delete_gram_panchayat(request, gram_panchayat_id):
    """Delete an existing gram panchayat."""
    try:
        gram_panchayat = tblGramPanchayat.objects.get(id=gram_panchayat_id)
    except tblGramPanchayat.DoesNotExist:
        return Response({"error": "Gram Panchayat not found"}, status=status.HTTP_404_NOT_FOUND)

    gram_panchayat.delete()
    return Response({"message": "Gram Panchayat deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@login_required
@api_view(['DELETE'])
@user_passes_test(is_admin_or_superuser)
def delete_village(request, village_id):
    """Delete an existing village."""
    try:
        village = tblVillage.objects.get(id=village_id)
    except tblVillage.DoesNotExist:
        return Response({"error": "Village not found"}, status=status.HTTP_404_NOT_FOUND)

    village.delete()
    return Response({"message": "Village deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
@parser_classes([MultiPartParser, FormParser])
def add_district_crlcle_gp_vill_by_csv(request):
    csv_file = request.FILES.get('file')
    update_existing = request.POST.get('update_existing', 'false').lower() == 'true'

    if not csv_file:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        for chunk in csv_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        import_location_data(temp_file_path, update_existing)
        os.remove(temp_file_path)
        return Response({"message": "Data imported successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        os.remove(temp_file_path)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_village_count(request):
    """Get count of villages based on selected district, circle, and gram panchayat.
    Accepts optional query params: district_id, circle_id, gram_panchayat_id"""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    
    villages = tblVillage.objects.all()
    
    if gram_panchayat_id:
        villages = villages.filter(gram_panchayat_id=gram_panchayat_id)
        count = villages.count()
        return Response({"village_count": count}, status=status.HTTP_200_OK)
    elif circle_id:
        villages = villages.filter(gram_panchayat__circle_id=circle_id)
        count = villages.count()
        return Response({"village_count": count}, status=status.HTTP_200_OK)
    elif district_id:
        villages = villages.filter(gram_panchayat__circle__district_id=district_id)
        count = villages.count()
        return Response({"village_count": count}, status=status.HTTP_200_OK)
    else:
        # No filters - return total counts
        village_count = VillageListOfAllTheDistricts.objects.values('village_code').distinct().count()
        district_count = VillageListOfAllTheDistricts.objects.values('district_code').distinct().count()
        return Response({
            "village_count": village_count,
            "district_count": district_count
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_location_counts(request):
    """Get counts of districts, circles, gram panchayats, and villages based on filters.
    Returns hierarchical counts for VDMP progress summary."""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    
    if village_id:
        return Response({
            "district_count": 1,
            "circle_count": 1,
            "gram_panchayat_count": 1,
            "village_count": 1
        }, status=status.HTTP_200_OK)
    elif gram_panchayat_id:
        village_count = tblVillage.objects.filter(gram_panchayat_id=gram_panchayat_id).count()
        return Response({
            "district_count": 1,
            "circle_count": 1,
            "gram_panchayat_count": 1,
            "village_count": village_count
        }, status=status.HTTP_200_OK)
    elif circle_id:
        gram_panchayat_count = tblGramPanchayat.objects.filter(circle_id=circle_id).count()
        village_count = tblVillage.objects.filter(gram_panchayat__circle_id=circle_id).count()
        return Response({
            "district_count": 1,
            "circle_count": 1,
            "gram_panchayat_count": gram_panchayat_count,
            "village_count": village_count
        }, status=status.HTTP_200_OK)
    elif district_id:
        circle_count = tblCircle.objects.filter(district_id=district_id).count()
        gram_panchayat_count = tblGramPanchayat.objects.filter(circle__district_id=district_id).count()
        village_count = tblVillage.objects.filter(gram_panchayat__circle__district_id=district_id).count()
        return Response({
            "district_count": 1,
            "circle_count": circle_count,
            "gram_panchayat_count": gram_panchayat_count,
            "village_count": village_count
        }, status=status.HTTP_200_OK)
    else:
        district_count = tblDistrict.objects.count()
        circle_count = tblCircle.objects.count()
        gram_panchayat_count = tblGramPanchayat.objects.count()
        village_count = tblVillage.objects.count()
        return Response({
            "district_count": district_count,
            "circle_count": circle_count,
            "gram_panchayat_count": gram_panchayat_count,
            "village_count": village_count
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_locations(request):
    try:
        store_lat_lon()
        return Response({"message": "Locations updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERRO)


# @login_required
@api_view(['GET', 'POST'])
# @user_passes_test(is_admin_or_superuser)
def sync_mobile_db_villages(request):
    """Sync villages from mobile DB to district_village_mapping table."""
    try:
        result = sync_villages_from_mobile_db(request.user)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def sync_villages_from_mobile_db(user):
    """Read mobile DB villages and create mapping records."""
    mobile_db = connections['mobile_db']
    created_count = 0
    skipped_count = 0
    
    with mobile_db.cursor() as cursor:
        cursor.execute("SELECT id, district_name, village_name FROM public.villages")
        mobile_villages = cursor.fetchall()
    
    for mobile_village_id, district_name, village_name in mobile_villages:
        # Check if mapping already exists
        if district_village_mapping.objects.filter(mobileDBVillageID=str(mobile_village_id)).exists():
            skipped_count += 1
            continue
        
        # Find matching district and village in default DB
        try:
            district = tblDistrict.objects.get(name__iexact=district_name)
            village = tblVillage.objects.filter(
                name__iexact=village_name,
                gram_panchayat__circle__district=district
            ).first()
            
            if village:
                district_village_mapping.objects.create(
                    district=district,
                    district_code=district.code,
                    circle=village.gram_panchayat.circle,
                    gram_panchayat=village.gram_panchayat,
                    village=village,
                    village_code=village.code,
                    mobileDBVillageID=str(mobile_village_id),
                    mobileDBDistrictID=district.code,
                    userID=user if user.is_authenticated else None
                )
                created_count += 1
            else:
                skipped_count += 1
        except tblDistrict.DoesNotExist:
            skipped_count += 1
    
    return {
        "message": "Sync completed",
        "created": created_count,
        "skipped": skipped_count
    }
    


@api_view(['GET'])
def count_of_villages_with_survey(request):
    """
    Get counts of villages with survey/facility data.
    Returns names for selected location and counts of children under it.
    """

    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')

    # Collect distinct village_ids from all sources
    house_h = HouseholdSurvey.objects.values_list('village_id', flat=True).distinct()
    transformer = Transformer.objects.values_list('village_id', flat=True).distinct()
    commercial = Commercial.objects.values_list('village_id', flat=True).distinct()
    critical = Critical_Facility.objects.values_list('village_id', flat=True).distinct()
    electric = ElectricPole.objects.values_list('village_id', flat=True).distinct()
    road = VillageRoadInfo.objects.values_list('village_id', flat=True).distinct()

    village_ids_with_data = (
        set(house_h) |
        set(transformer) |
        set(commercial) |
        set(critical) |
        set(electric) |
        set(road)
    )

    villages_with_data = tblVillage.objects.filter(id__in=village_ids_with_data)

    # Apply location filters
    villages_with_data = village_apply_location_filters(
        villages_with_data,
        district_id=district_id,
        circle_id=circle_id,
        gram_panchayat_id=gram_panchayat_id,
        village_id=village_id
    )

    # --- Case: Village level ---
    if village_id:
        try:
            village = villages_with_data.select_related(
                "gram_panchayat__circle__district"
            ).get(id=village_id)
            return Response({
                "district_val": village.gram_panchayat.circle.district.name,
                "circle_val": village.gram_panchayat.circle.name,
                "gram_panchayat_val": village.gram_panchayat.name,
                "village_val": village.name,
                "has_data": True
            })
        except tblVillage.DoesNotExist:
            village = tblVillage.objects.get(id=village_id)
            return Response({
                "district_val": village.gram_panchayat.circle.district.name,
                "circle_val": village.gram_panchayat.circle.name,
                "gram_panchayat_val": village.gram_panchayat.name,
                "village_val": 0,
                "has_data": False
            })

    # --- Case: Gram Panchayat level ---
    if gram_panchayat_id:
        gp = tblGramPanchayat.objects.select_related("circle__district").get(id=gram_panchayat_id)
        return Response({
            "district_val": gp.circle.district.name,
            "circle_val": gp.circle.name,
            "gram_panchayat_val": gp.name,
            "village_val": villages_with_data.count()
        })

    # --- Case: Circle level ---
    if circle_id:
        circle = tblCircle.objects.select_related("district").get(id=circle_id)
        return Response({
            "district_val": circle.district.name,
            "circle_val": circle.name,
            "gram_panchayat_val": villages_with_data.values("gram_panchayat_id").distinct().count(),
            "village_val": villages_with_data.count()
        })

    # --- Case: District level ---
    if district_id:
        district = tblDistrict.objects.get(id=district_id)
        return Response({
            "district_val": district.name,
            "circle_val": villages_with_data.values("gram_panchayat__circle_id").distinct().count(),
            "gram_panchayat_val": villages_with_data.values("gram_panchayat_id").distinct().count(),
            "village_val": villages_with_data.count()
        })

    # --- Case: No filter, overall counts ---
    return Response({
        "district_val": villages_with_data.values("gram_panchayat__circle__district_id").distinct().count(),
        "circle_val": villages_with_data.values("gram_panchayat__circle_id").distinct().count(),
        "gram_panchayat_val": villages_with_data.values("gram_panchayat_id").distinct().count(),
        "village_val": villages_with_data.count()
    })


