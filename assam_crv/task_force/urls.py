from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskForceViewSet, task_force_admin, task_force_client, get_taskforce_chart_data, get_team_types_dropdown

router = DefaultRouter()
router.register(r"taskforce", TaskForceViewSet, basename="taskforce")

urlpatterns = [
    path('task_force/', task_force_client, name='task_force'),
    path('api/', include(router.urls)),
    path('api/taskforce_chart_data', get_taskforce_chart_data, name='get_taskforce_chart_data'),
    path('api/team_types_dropdown/', get_team_types_dropdown, name='get_team_types_dropdown'),
]
