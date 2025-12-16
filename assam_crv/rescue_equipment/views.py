from django.shortcuts import render,redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from .models import tbl_Rescue_Equipment_Status, tbl_Rescue_Equipment
from .serializers import Rescue_Equipment_StatusSerializer, Rescue_EquipmentSerializer , DropdownRescue_EquipmentSerializer
from utils import is_admin_or_superuser, apply_location_filters, apply_role_filters
from django.contrib.auth.decorators import login_required, user_passes_test
from village_profile.models import tblVillage

@api_view(['GET'])
def get_rescue_equipment_status(request):
    """Retrieve rescue equipment statuses with location filters.
    Returns serialized data for use in frontend or API clients."""

    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)

    equipment_id = request.query_params.get('equipment_id', None)

    data = tbl_Rescue_Equipment_Status.objects.select_related(
        'equipment',
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
        'updated_by'
    ).all()

    data = apply_location_filters(data, district_id=district_id, circle_id=circle_id, 
                                  gram_panchayat_id=gram_panchayat_id, village_id=village_id)

    if equipment_id:
        data = data.filter(equipment_id=equipment_id)

    serializer = Rescue_Equipment_StatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def admin_get_rescue_equipment_status(request):
    """Admin view to retrieve rescue equipment status data.
    Applies both role and location-based filtering."""

    user = request.user
    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)
    equipment_id = request.query_params.get('equipment_id', None)

    if not user.is_authenticated:
        return Response([], status=status.HTTP_200_OK)

    queryset = tbl_Rescue_Equipment_Status.objects.select_related(
        'equipment',
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
        'updated_by'
    ).order_by('village__gram_panchayat__circle__district__name', 'village__name')

    role = user.role.name if user.role else None
    data = apply_role_filters(user, role, queryset)

    data = apply_location_filters(data, district_id=district_id, circle_id=circle_id, 
                                  gram_panchayat_id=gram_panchayat_id, village_id=village_id)

    if equipment_id:
        data = data.filter(equipment_id=equipment_id)
        
    serializer = Rescue_Equipment_StatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_rescue_equipment(request):
    """Render the rescue equipment list view for admin.
    Loads all equipment records for display in the UI."""
    
    equipments = tbl_Rescue_Equipment.objects.all()
    return render(request, 'equipment/rescue_equipments.html', {'equipments': equipments})


@login_required
@user_passes_test(is_admin_or_superuser)
@api_view(['POST'])
def create_rescue_equipment(request):
    """Create a new rescue equipment item.
    Requires admin access and returns ID on success."""

    serializer = Rescue_EquipmentSerializer(data=request.data)
    if serializer.is_valid():
        equipment = serializer.save()
        return Response({'message': 'Equipment created successfully', 'id': equipment.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_rescue_equipment_by_id(request, equipment_id):
    """Get details of a specific rescue equipment item.
    Returns serialized data or a 404 error if not found."""

    try:
        equipment = tbl_Rescue_Equipment.objects.get(id=equipment_id)
        serializer = Rescue_EquipmentSerializer(equipment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except tbl_Rescue_Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_all_rescue_equipments(request):
    """Get a list of all rescue equipment entries.
    Useful for dropdowns or equipment inventory views."""

    equipments = tbl_Rescue_Equipment.objects.all()
    serializer = Rescue_EquipmentSerializer(equipments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_rescue_equipment(request, equipment_id):
    """Update an existing rescue equipment item by ID.
    Accepts partial data and returns status message."""

    try:
        equipment = tbl_Rescue_Equipment.objects.get(id=equipment_id)
        serializer = Rescue_EquipmentSerializer(equipment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Equipment updated successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except tbl_Rescue_Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_rescue_equipment(request, equipment_id):
    """Delete a rescue equipment item by ID.
    Returns a success message or error if not found."""

    try:
        equipment = tbl_Rescue_Equipment.objects.get(id=equipment_id)
        equipment.delete()
        return Response({'message': 'Equipment deleted successfully'}, status=status.HTTP_200_OK)
    except tbl_Rescue_Equipment.DoesNotExist:
        return Response({'error': 'Equipment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def update_rescue_equipment_status(request, status_id):
    """Update the status of rescue equipment by ID.
    Includes updated_by field if user is authenticated."""

    try:
        status_obj = tbl_Rescue_Equipment_Status.objects.get(id=status_id)
        data = request.data.copy()
        if request.user.is_authenticated:
            data['updated_by'] = request.user.id
        
        serializer = Rescue_Equipment_StatusSerializer(status_obj, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Equipment status updated successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except tbl_Rescue_Equipment_Status.DoesNotExist:
        return Response({'error': 'Equipment status not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_rescue_equipment_status(request):
    """Create a new rescue equipment status entry.
    Automatically sets 'updated_by' if user is logged in."""

    data = request.data.copy()
    if request.user.is_authenticated:
        data['updated_by'] = request.user.id
    
    serializer = Rescue_Equipment_StatusSerializer(data=data)
    if serializer.is_valid():
        status_obj = serializer.save()
        return Response({'message': 'Equipment status created successfully', 'id': status_obj.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_rescue_equipment_status(request, status_id):
    """Delete a rescue equipment status record by ID.
    Returns a success or error message in the response."""

    try:
        status_obj = tbl_Rescue_Equipment_Status.objects.get(id=status_id)
        status_obj.delete()
        return Response({'message': 'Equipment status deleted successfully'}, status=status.HTTP_200_OK)
    except tbl_Rescue_Equipment_Status.DoesNotExist:
        return Response({'error': 'Equipment status not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
def dropdown_rescue_equipment(request):
    """Retrieve a list of Rescuse Eqp for dropdown.
    Returns a list with ID and name."""

    activities = tbl_Rescue_Equipment.objects.all().order_by('name')
    serializer = DropdownRescue_EquipmentSerializer(activities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

from django.utils.translation import get_language

@api_view(['GET'])
def get_rescue_equipment_chart_data(request):
    """Get chart data for rescue equipment grouped by equipment type."""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    equipment_ids = request.query_params.get('equipment_ids')
    
    queryset = tbl_Rescue_Equipment_Status.objects.select_related('equipment', 'village')
    queryset = apply_location_filters(queryset, district_id=district_id, circle_id=circle_id,
                                    gram_panchayat_id=gram_panchayat_id, village_id=village_id)
    
    if equipment_ids:
        equipment_id_list = [int(id.strip()) for id in equipment_ids.split(',') if id.strip()]
        queryset = queryset.filter(equipment_id__in=equipment_id_list)
    
    # 🔑 Select language-specific field
    lang = get_language()
    lang_map = {
        'en': 'equipment__name',
        'as': 'equipment__name_as',
        'bn': 'equipment__name_bn',
        'brx': 'equipment__name',  # if you also added Bodo
    }
    name_field = lang_map.get(lang, 'equipment__name')  # fallback to English

    aggregated = queryset.values(name_field).annotate(
        available=Count('village_id', filter=Q(count__gt=0), distinct=True),
        total_villages=Count('village_id', distinct=True)
    )
    
    formatted = [
        {
            'equipment': item[name_field],
            'available': item['available'],
            'not_available': item['total_villages'] - item['available']
        }
        for item in aggregated
    ]
    
    return Response(formatted)


@api_view(['GET'])
def get_equipments_dropdown(request):
    """Get list of equipments for dropdown."""
    
    equipments = tbl_Rescue_Equipment.objects.all().values('id', 'name').order_by('name')
    return Response(list(equipments))




# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# import csv, io
# from django.utils.translation import gettext as _
# from googletrans import Translator  


# @api_view(['POST'])
# def upload_rescue_equipment_csv(request):
#     if 'file' not in request.FILES:
#         return Response({"error": "CSV file is required with key 'file'"}, status=status.HTTP_400_BAD_REQUEST)

#     csv_file = request.FILES['file']
#     if not csv_file.name.endswith('.csv'):
#         return Response({"error": "Only CSV files are accepted."}, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         decoded_file = csv_file.read().decode('utf-8')
#         io_string = io.StringIO(decoded_file)
#         reader = csv.DictReader(io_string)

#         created = 0
#         errors = []

#         # Optional: Use Google Translate
#         translator = Translator()
#         tbl_Rescue_Equipment.objects.all().delete()
#         for row_num, row in enumerate(reader, start=2):
#             name = row.get('Item', '').strip()
#             task_force = row.get('TaskForce', '').strip()
#             specification = row.get('Specification', '').strip()

#             if not name:
#                 errors.append(f"Row {row_num}: 'Item' is required.")
#                 continue

#             try:
#                 # Translate values
#                 name_bn = translator.translate(name, dest='bn').text
#                 task_force_bn = translator.translate(task_force, dest='bn').text if task_force else ''
#                 specification_bn = translator.translate(specification, dest='bn').text if specification else ''

#                 # Save record
#                 tbl_Rescue_Equipment.objects.create(
#                     name=name,
#                     name_bn=name_bn,
#                     name_as=name_bn,
#                     task_force=task_force,
#                     task_force_bn=task_force_bn,
#                     task_force_as=task_force_bn,
#                     specification=specification,
#                     specification_bn=specification_bn,
#                     specification_as=specification_bn
#                 )
#                 created += 1

#             except Exception as e:
#                 errors.append(f"Row {row_num}: {str(e)}")

#         if errors:
#             return Response({"message": f"{created} records created", "errors": errors}, status=status.HTTP_207_MULTI_STATUS)
        
#         return Response({"message": f"{created} equipment records uploaded successfully."}, status=status.HTTP_201_CREATED)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
