from django.urls import path
from .views import ( get_vdmp_activity_status, admin_get_vdmp_activity_status, create_vdmp_activity, 
                    update_vdmp_activity, delete_vdmp_activity, update_vdmp_activity_status, delete_vdmp_activity_status, get_vdmp_activity_status_data,
                    vdmp_progress_page, dropdown_vdmp_activity)


urlpatterns = [
    #____URLS____
    path('vdmp_progress/', vdmp_progress_page, name='vdmp_progress'),

    #____APIS____
    path('api/get_vdmp_activity_status_data', get_vdmp_activity_status_data, name='get_vdmp_activity_status_data'),
    path('api/vdmp_activity_status', get_vdmp_activity_status, name='get_vdmp_activity_status'),
    
    path('api/admin_get_vdmp_activity_status', admin_get_vdmp_activity_status, name='admin_get_vdmp_activity_status'),
    path('api/create_vdmp_activity', create_vdmp_activity, name='create_vdmp_activity'),
    path('api/update_vdmp_activity/<int:activity_id>/', update_vdmp_activity, name='update_vdmp_activity'),
    path('api/delete_vdmp_activity/<int:activity_id>/', delete_vdmp_activity, name='delete_vdmp_activity'),

    path('api/update_vdmp_activity_status/<int:status_id>/', update_vdmp_activity_status, name='update_vdmp_activity_status'),
    path('api/delete_vdmp_activity_status/<int:status_id>/', delete_vdmp_activity_status, name='delete_vdmp_activity_status'),
    path('api/dropdown_vdmp_activity', dropdown_vdmp_activity, name='dropdown_vdmp_activity'),

]