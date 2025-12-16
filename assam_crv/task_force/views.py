from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from django.db.models import Count, Q
from .models import TaskForce
from .serializers import TaskForceSerializer
from utils import apply_location_filters, village_apply_location_filters
from village_profile.models import tblVillage


from django.contrib.auth.decorators import login_required

@login_required
def task_force_admin(request):
    return render(request, 'administrator/task_force/index.html')

def task_force_client(request):
    return render(request, 'task_force/index.html')


from rest_framework.permissions import AllowAny, IsAuthenticated

class TaskForceViewSet(viewsets.ModelViewSet):
    queryset = TaskForce.objects.all().select_related(
        "village__gram_panchayat__circle__district"
    )
    serializer_class = TaskForceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:  # GET endpoints
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        district_id = self.request.query_params.get("district_id")
        circle_id = self.request.query_params.get("circle_id")
        gp_id = self.request.query_params.get("gram_panchayat_id")
        village_id = self.request.query_params.get("village_id")
        team_type = self.request.query_params.get("team_type")

        queryset = apply_location_filters(
            queryset,
            district_id=district_id,
            circle_id=circle_id,
            gram_panchayat_id=gp_id,
            village_id=village_id
        )
        
        if team_type:
            queryset = queryset.filter(team_type=team_type)
            
        return queryset


    @action(detail=False, methods=['post'])
    def upload(self, request):
        try:
            file = request.FILES.get('file')
            team_type = request.data.get('team_type')
            
            if not file or not team_type:
                return Response({'detail': 'File and team type are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Read Excel/CSV file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Find village by ID
                    village = None
                    if pd.notna(row.get('Village_Id')):
                        village = tblVillage.objects.filter(code=row['Village_Id']).first()
                    
                    if not village:
                        errors.append(f"Row {index + 1}: Village not found")
                        continue
                    
                    # Handle position responsibility
                    position = row.get('Position/Responsibility', 'Team member')
                    if position and position.lower() == 'member':
                        position = 'Team member'
                    elif position and position.lower() not in ['team member', 'team leader']:
                        position = 'Team member'
                    
                    TaskForce.objects.create(
                        village=village,
                        fullname=row.get('Name', ''),
                        father_name=row.get('Father_name', ''),
                        gender=row.get('Gender', 'Male'),
                        mobile_number=row.get('Phone_number', ''),
                        position_responsibility=position,
                        occupation=row.get('Occupation', ''),
                        team_type=team_type
                    )
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            response_data = {'created_count': created_count}
            if errors:
                response_data['errors'] = errors[:10]  # Limit to first 10 errors
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_taskforce_chart_data(request):
    """Get chart data for task force teams grouped by team type."""
    
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    team_types = request.query_params.get('team_types')
    
    # Get distinct villages with task force teams
    queryset = TaskForce.objects.select_related('village').values('village_id', 'team_type').distinct()
    queryset = apply_location_filters(queryset, district_id=district_id, circle_id=circle_id,
                                     gram_panchayat_id=gram_panchayat_id, village_id=village_id)
    
    if team_types:
        team_type_list = [t.strip() for t in team_types.split(',') if t.strip()]
        queryset = queryset.filter(team_type__in=team_type_list)
    else:
        team_type_list = None  # Will use all team types below

    # All possible team types
    all_team_types = [choice[0] for choice in TaskForce.TeamType.choices]
    
    # Only consider requested team types if provided
    team_types_to_iterate = team_type_list if team_type_list else all_team_types

    # Get all villages in the filtered area
    village_queryset = tblVillage.objects.all()
    village_queryset = village_apply_location_filters(village_queryset, district_id=district_id, 
                                                     circle_id=circle_id, gram_panchayat_id=gram_panchayat_id, 
                                                     village_id=village_id)
    total_villages = village_queryset.count()
    
    formatted = []
    for team_type in team_types_to_iterate:
        villages_with_team = queryset.filter(team_type=team_type).values('village_id').distinct().count()
        villages_without_team = total_villages - villages_with_team
        
        formatted.append({
            'team_type': team_type,
            'created': villages_with_team,
            'not_created': villages_without_team
        })
    
    return Response(formatted)



@api_view(['GET'])
def get_team_types_dropdown(request):
    """Get list of team types for dropdown."""
    
    team_types = [
        {'value': choice[0], 'name': choice[1]} 
        for choice in TaskForce.TeamType.choices
    ]
    return Response(team_types)
