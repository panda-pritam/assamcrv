from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import tbl_Training_Activities, tbl_Training_Activities_Status
from .serializers import TrainingActivityStatusSerializer, TrainingActivitySerializer, CustomTrainingActivityStatusSerializer
from utils import is_admin_or_superuser, apply_location_filters, apply_role_filters
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q


@api_view(['GET'])
def get_training_activity_status(request):
    """Retrieve training activity status data with optional filters.
    Filters include location, status, and activities; returns serialized results."""
    
    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)
    status_val = request.query_params.get('status')
    activity_ids = request.query_params.get('activity_ids')
    
    data = tbl_Training_Activities_Status.objects.select_related(
        'activity',
        'village',
        'village__gram_panchayat',
        'village__gram_panchayat__circle',
        'village__gram_panchayat__circle__district',
        'updated_by'
    ).all().order_by('village__gram_panchayat__circle__district__name', 'village__name')

    data = apply_location_filters(data, district_id=district_id, circle_id=circle_id, 
                                  gram_panchayat_id=gram_panchayat_id, village_id=village_id)
    if status_val:
        data = data.filter(status=status_val)
    if activity_ids:
        activity_id_list = [int(id.strip()) for id in activity_ids.split(',') if id.strip()]
        data = data.filter(activity_id__in=activity_id_list)
        
    serializer = TrainingActivityStatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@api_view(['GET'])
def admin_get_training_activity_status(request):
    """Admin-only view to retrieve training activity statuses.
    Applies user role and location filters for controlled access."""
    
    user = request.user
    district_id = request.query_params.get('district_id', None)
    circle_id = request.query_params.get('circle_id', None)
    gram_panchayat_id = request.query_params.get('gram_panchayat_id', None)
    village_id = request.query_params.get('village_id', None)
    status_val = request.query_params.get('status')    

    if not user.is_authenticated:
        return Response([], status=status.HTTP_200_OK)

    queryset = tbl_Training_Activities_Status.objects.select_related(
        'activity',
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
    if status_val:
        data = data.filter(status=status_val)

    serializer = TrainingActivityStatusSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_training_activities(request):
    """Render the training activity status HTML page.
    Used to show the admin training activity dashboard."""
    return render(request, 'training/training_activities_status.html')


@login_required
@user_passes_test(is_admin_or_superuser)
def delete_training_activity(request, activity_id):
    """Delete a training activity from the admin panel.
    Redirects to admin training activity list after deletion."""
    activity = tbl_Training_Activities.objects.get(id=activity_id)
    activity.delete()
    return redirect('admin_get_training_activities')


@api_view(['POST'])
def create_training_activity(request):
    """Create a new training activity from POSTed JSON.
    Returns the created object or validation errors."""
    serializer = TrainingActivitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_training_activity(request, activity_id):
    """Update an existing training activity by ID.
    Allows partial updates using PATCH method."""
    try:
        activity = tbl_Training_Activities.objects.get(id=activity_id)
    except tbl_Training_Activities.DoesNotExist:
        return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TrainingActivitySerializer(activity, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_training_activity_status(request):
    """Create status for a training activity for a village.
    Prevents duplicates and returns the created object."""
    
    activity = request.data.get('activity')
    village = request.data.get('village')
    status_val = request.data.get('status')

    if tbl_Training_Activities_Status.objects.filter(activity_id=activity, village_id=village).exists():
        return Response(
            {"error": "This training activity status already exists for the selected village."},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CustomTrainingActivityStatusSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_training_activity_status(request, status_id):
    """Update a training activity status by ID.
    Accepts partial data using PATCH and returns updated status."""
    
    try:
        activity_status = tbl_Training_Activities_Status.objects.get(id=status_id)
    except tbl_Training_Activities_Status.DoesNotExist:
        return Response({'error': 'Activity status not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CustomTrainingActivityStatusSerializer(activity_status, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@api_view(['DELETE'])
def delete_training_activity_api(request, activity_id):
    """Delete a training activity via API by ID.
    Returns a success or not-found message in JSON format."""
    
    try:
        activity = tbl_Training_Activities.objects.get(id=activity_id)
        activity.delete()
        return Response({'message': 'Training activity deleted successfully'}, status=status.HTTP_200_OK)
    except tbl_Training_Activities.DoesNotExist:
        return Response({'error': 'Training activity not found'}, status=status.HTTP_404_NOT_FOUND)


@login_required
@api_view(['DELETE'])
def delete_training_activity_status_api(request, status_id):
    """Delete a training activity status via API by ID.
    Returns success confirmation or error if not found."""
    
    try:
        activity_status = tbl_Training_Activities_Status.objects.get(id=status_id)
        activity_status.delete()
        return Response({'message': 'Training activity status deleted successfully'}, status=status.HTTP_200_OK)
    except tbl_Training_Activities_Status.DoesNotExist:
        return Response({'error': 'Activity status not found'}, status=status.HTTP_404_NOT_FOUND)


def delete_training_activity_status(request, status_id):
    """Delete a training activity status from admin panel.
    Redirects to admin training activity list after deletion."""
    
    activity_status = tbl_Training_Activities_Status.objects.get(id=status_id)
    activity_status.delete()
    return redirect('admin_get_training_activities')


@api_view(['GET'])
def get_training_chart_data(request):
    """Get chart data for training activities grouped by activity."""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    activity_ids = request.query_params.get('activity_ids')
    
    queryset = tbl_Training_Activities_Status.objects.select_related('activity', 'village')
    queryset = apply_location_filters(queryset, district_id=district_id, circle_id=circle_id,
                                    gram_panchayat_id=gram_panchayat_id, village_id=village_id)
    
    if activity_ids:
        activity_id_list = [int(id.strip()) for id in activity_ids.split(',') if id.strip()]
        queryset = queryset.filter(activity_id__in=activity_id_list)
    
    aggregated = queryset.values('activity__name').annotate(
        completed=Count('id', filter=Q(status='Completed')),
        remaining=Count('id', filter=Q(status='Scheduled'))
    )
    
    formatted = [
        {
            'activity': item['activity__name'],
            'completed': item['completed'],
            'remaining': item['remaining']
        }
        for item in aggregated
    ]
    
    return Response(formatted)


@api_view(['GET'])
def get_activities_dropdown(request):
    """Get list of activities for dropdown."""
    
    activities = tbl_Training_Activities.objects.all().values('id', 'name')
    return Response(list(activities))


