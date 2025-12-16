
from django.urls import path
from .views import (get_rescue_equipment_status,admin_get_rescue_equipment_status, get_rescue_equipment, 
                    create_rescue_equipment, get_rescue_equipment_by_id, get_all_rescue_equipments, update_rescue_equipment, 
                    delete_rescue_equipment, create_rescue_equipment_status, update_rescue_equipment_status, delete_rescue_equipment_status,
                    dropdown_rescue_equipment, get_rescue_equipment_chart_data, get_equipments_dropdown)

urlpatterns = [
    path('rescue_equipment', get_rescue_equipment, name='get_rescue_equipment'),
    
    #____APIS____
    path('api/get_rescue_equipment_status', get_rescue_equipment_status, name='api_get_rescue_equipment_status'),
    path('api/admin_get_rescue_equipment_status', admin_get_rescue_equipment_status, name='api_admin_get_rescue_equipment_status'),


    # ____administrator___________
    path('api/create_rescue_equipment/', create_rescue_equipment, name='api_create_rescue_equipment'),
    path('api/get_rescue_equipment/<int:equipment_id>/', get_rescue_equipment_by_id, name='api_get_rescue_equipment_by_id'),
    path('api/get_all_rescue_equipments/', get_all_rescue_equipments, name='api_get_all_rescue_equipments'),
    path('api/update_rescue_equipment/<int:equipment_id>/', update_rescue_equipment, name='api_update_rescue_equipment'),
    path('api/delete_rescue_equipment/<int:equipment_id>/', delete_rescue_equipment, name='api_delete_rescue_equipment'),
    
    # Equipment Status APIs
    # path('api/upload_rescue_equipment_csv', upload_rescue_equipment_csv, name='api_upload_rescue_equipment_csv'),
    path('api/create_rescue_equipment_status/', create_rescue_equipment_status, name='api_create_rescue_equipment_status'),
    path('api/update_rescue_equipment_status/<int:status_id>/', update_rescue_equipment_status, name='api_update_rescue_equipment_status'),
    path('api/delete_rescue_equipment_status/<int:status_id>/', delete_rescue_equipment_status, name='api_delete_rescue_equipment_status'),
    path('api/dropdown_rescue_equipment/', dropdown_rescue_equipment, name='api_dropdown_rescue_equipment'),
    path('api/rescue_equipment_chart_data/', get_rescue_equipment_chart_data, name='get_rescue_equipment_chart_data'),
    path('api/equipments_dropdown/', get_equipments_dropdown, name='get_equipments_dropdown'),

]
