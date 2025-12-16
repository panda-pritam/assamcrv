
from django.urls import path
from .views import ( get_training_activity_status, get_training_activities, delete_training_activity, create_training_activity, update_training_activity,

    create_training_activity_status, update_training_activity_status, delete_training_activity_status_api, admin_get_training_activity_status,delete_training_activity_api,
    get_training_chart_data, get_activities_dropdown)


urlpatterns = [
    path('training_activities', get_training_activities, name='get_training_activities'),
    #____APIS____
    path('api/delete_training_activity/<int:activity_id>/', delete_training_activity_api, name='delete_training_activity'),
    path('api/delete_training_activity_status/<int:status_id>/', delete_training_activity_status_api, name='delete_training_activity_status'),

    path('api/create_training_activity', create_training_activity, name='api_create_training_activity'),
    path('api/get_training_activity_status', get_training_activity_status, name='api_get_training_activity_status'),
    path('api/update_training_activity/<int:activity_id>/', update_training_activity, name='api_update_training_activity'),
    path('api/create_training_activity_status', create_training_activity_status, name='api_create_training_activity_status'),
    path('api/update_training_activity_status/<int:status_id>/', update_training_activity_status, name='api_update_training_activity_status'),
    path('api/administrator/get_training_activity_status', admin_get_training_activity_status, name='admin_get_training_activity_status'),
    path('api/training_chart_data', get_training_chart_data, name='get_training_chart_data'),
    path('api/activities_dropdown', get_activities_dropdown, name='get_activities_dropdown'),

]
