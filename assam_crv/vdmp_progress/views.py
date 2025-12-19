from django.shortcuts import render
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import tblVDMP_Activity, tblVDMP_Activity_Status
from .serializers import VDMPActivitySerializer, VDMPActivityStatusSerializer, ListVDMPActivityStatusSerializer, VDMPActivityStatusSummarySerializer, DropdownVDMPActivitySerializer
from utils import is_admin_or_superuser, apply_location_filters, apply_role_filters
from django.db.models import Count, Q
from django.utils.translation import get_language

from .data_pipeline import process_household_survey_data
from village_profile.models import district_village_mapping

@api_view(['GET'])
def get_vdmp_activity_status(request):
    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)
    status_val = request.query_params.get('status', None)

    # <-- CHANGE: getlist to collect multiple activity_id values
    activity_ids = request.query_params.getlist('activity_id')

    data = tblVDMP_Activity_Status.objects.select_related(
        'activity',
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
        'updated_by'
    ).all().order_by(
        'village__gram_panchayat__circle__district__name',
        'village__name'
    )

    data = apply_location_filters(data, district_id=district_id, circle_id=circle_id,
                                  gram_panchayat_id=gram_panchayat_id, village_id=village_id)

    if status_val:
        data = data.filter(status=status_val)

    if activity_ids:
        # sanitize -> convert to ints where possible
        try:
            activity_ids_int = [int(x) for x in activity_ids]
        except ValueError:
            activity_ids_int = [int(x) for x in activity_ids if str(x).isdigit()]
        if activity_ids_int:
            data = data.filter(activity_id__in=activity_ids_int)

    serializer = ListVDMPActivityStatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_vdmp_activity_status_data(request):
    """Aggregate VDMP activity status counts.
    Returns count of activities grouped by status and activity name."""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    activity_ids = request.query_params.get('activity_ids')

    qs = tblVDMP_Activity_Status.objects.select_related('activity', 'village')
    qs = apply_location_filters(qs, district_id, circle_id, gram_panchayat_id, village_id)
    
    if activity_ids:
        activity_id_list = [int(id.strip()) for id in activity_ids.split(',') if id.strip().isdigit()]
        if activity_id_list:
            qs = qs.filter(activity_id__in=activity_id_list)

    lang = get_language()
    
    if lang == 'as':
        name_field = 'activity__name_as'
    elif lang == 'bn':
        name_field = 'activity__name_bn'
    else:
        name_field = 'activity__name'
    
    aggregated = qs.values(
        name_field,
        'activity__order'
    ).annotate(
        not_started=Count('id', filter=Q(status='Not Started')),
        in_progress=Count('id', filter=Q(status='In Progress')),
        completed=Count('id', filter=Q(status='Completed')),
    ).order_by('activity__order')   # ✅ sort by activity order

    formatted = [
        {
            'activity': item[name_field],
            'not_started': item['not_started'],
            'in_progress': item['in_progress'],
            'completed': item['completed']
        }
        for item in aggregated
    ]

    serializer = VDMPActivityStatusSummarySerializer(formatted, many=True)
    return Response(serializer.data)


@login_required
@api_view(['GET'])
def admin_get_vdmp_activity_status(request):
    """Admin view to retrieve filtered VDMP activity status.
    Applies both role-based and location-based filters."""

    user = request.user
    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)
    status_val = request.query_params.get('status')    
    activity_id = request.query_params.get('activity_id', None)  

    if not user.is_authenticated:
        return Response([], status=status.HTTP_200_OK)

    queryset = tblVDMP_Activity_Status.objects.select_related(
        'activity',
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
        'updated_by'
    ).order_by(
        'village__gram_panchayat__circle__district__name',
        'village__name'
    )

    role = user.role.name if user.role else None
    data = apply_role_filters(user, role, queryset)

    data = apply_location_filters(data, district_id=district_id, circle_id=circle_id,
                                  gram_panchayat_id=gram_panchayat_id, village_id=village_id)

    if status_val:
        data = data.filter(status=status_val)

    if activity_id:
        data = data.filter(activity_id=activity_id)

    serializer = ListVDMPActivityStatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@api_view(['POST'])
@user_passes_test(is_admin_or_superuser)
def create_vdmp_activity(request):
    """Create a new VDMP activity entry.
    Accepts activity details as JSON payload (admin only)."""

    serializer = VDMPActivitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['PATCH'])
def update_vdmp_activity(request, activity_id):
    """Update an existing VDMP activity.
    Accepts partial update by activity ID."""

    try:
        activity = tblVDMP_Activity.objects.get(id=activity_id)
    except tblVDMP_Activity.DoesNotExist:
        return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = VDMPActivitySerializer(activity, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_vdmp_activity(request, activity_id):
    """Delete a VDMP activity entry.
    Deletes the activity by given activity ID."""

    try:
        activity = tblVDMP_Activity.objects.get(id=activity_id)
    except tblVDMP_Activity.DoesNotExist:
        return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

    activity.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
@api_view(['PATCH'])
def update_vdmp_activity_status(request, status_id):
    """Update a VDMP activity status entry.
    Accepts partial update by status ID."""

    try:
        activity_status = tblVDMP_Activity_Status.objects.get(id=status_id)
    except tblVDMP_Activity_Status.DoesNotExist:
        return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = VDMPActivityStatusSerializer(activity_status, data=request.data, partial=True)
    if serializer.is_valid():
        # Trigger data pipeline if status is marked as 'Completed'
        if serializer.validated_data.get('status') == 'Completed':
            if activity_status.activity.name == 'Household survey':
                try:
                    from .data_pipeline import process_household_survey_data
                    from village_profile.models import district_village_mapping
                    
                    village_id = activity_status.village.id
                    print("activity_status.village.id -> ", village_id)
                    
                    # Get mapping record
                    mapping = district_village_mapping.objects.get(village_id=village_id)
                    mobile_village_id = mapping.mobileDBVillageID
                    district_id = mapping.district.id
                    district_code = mapping.district_code
                    village_code = mapping.village_code
                    
                    print(f"Mobile Village ID: {mobile_village_id}")
                    print(f"District ID: {district_id}, District Code: {district_code}")
                    print(f"Village Code: {village_code}")
                    
                    # Process data pipeline with import status tracking
                    import_status, records_processed = process_household_survey_data(
                        activity_status.activity.name,
                        village_id,
                        district_id,
                        mobile_village_id,
                        district_code,
                        village_code,
                        activity_status
                    )
                    
                    # Save status only after successful pipeline completion
                    serializer.save()
                    
                    return Response({
                        **serializer.data,
                        'pipeline_status': 'success',
                        'records_processed': records_processed,
                        'import_status_id': import_status.id
                    })
                    
                except Exception as e:
                    # Return error without saving status
                    return Response({
                        'error': 'Pipeline processing failed',
                        'pipeline_error': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # For non-household survey activities, just save
                serializer.save()
                return Response(serializer.data)
        else:
            # Save status for non-Completed statuses
            serializer.save()
            return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_vdmp_activity_status(request, status_id):
    """Delete a VDMP activity status entry.
    Deletes the status entry by given ID."""

    try:
        activity = tblVDMP_Activity_Status.objects.get(id=status_id)
    except tblVDMP_Activity_Status.DoesNotExist:
        return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

    activity.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def vdmp_progress_page(request):
    """Render the VDMP progress dashboard page.
    Returns an HTML template view for visualizing progress."""
    
    # Get all VDMP activities for the master table
    vdmp_activities = tblVDMP_Activity.objects.all().order_by('name')
    
    context = {
        'vdmp_activities': vdmp_activities
    }
    
    return render(request, 'vdmp_progress/dashboard.html', context)


@api_view(['GET'])
def dropdown_vdmp_activity(request):
    """Retrieve a list of VDMP activities for dropdown.
    Returns a list of activities with ID and name."""

    activities = tblVDMP_Activity.objects.all().order_by('name')
    serializer = DropdownVDMPActivitySerializer(activities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


