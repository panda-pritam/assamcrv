
from django.urls import path

from .views import (administrator_home_view, admin_get_training_activities, get_rescue_equipment, get_users_list, 
                    admin_get_roles_list, get_village_profile, get_department_list, get_vdmp_progres_dashboard, get_vdmp_dashboard, upload_master_data)

from task_force.views import task_force_admin  
from field_images.views import getAdmin 


urlpatterns = [
    path('', administrator_home_view, name='administrator_home_view'),
    path('training_activities', admin_get_training_activities, name='admin_get_training_activities'),
    path('rescue_equipment', get_rescue_equipment, name='rescue_equipment'),
    path('users', get_users_list, name='get_users_list'),
    path('village_profile', get_village_profile, name='get_village_profile'),
    path('departments', get_department_list, name='get_department_list'),
    path('vdmp_dashboard', get_vdmp_dashboard, name='get_vdmp_dashboard'),
    path('vdmp_progress', get_vdmp_progres_dashboard, name='get_vdmp_progres_dashboard'),
    path('roles', admin_get_roles_list, name='admin_get_roles_list'),
    path('task_force_admin/', task_force_admin, name='task_force_admin'),
    #____APIS____
    path('api/upload_master_data/', upload_master_data, name='upload_master_data'),
    path('field_images', getAdmin, name='getAdmin'),

]
