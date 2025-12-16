# core/urls.py

from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import ( login_view, register_user, list_users, user_profile_get, delete_user, 
                    user_profile_update, create_department, update_department, delete_department, get_departments_list,
                    get_profile, change_password, update_user_profile, get_modules_permission)
# from .views import create_role, update_role, delete_role

urlpatterns = [
    # path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', get_profile, name='profile'),

    path('api/change-password/', change_password, name='change-password'),
    path('api/update-profile/', update_user_profile, name='update-profile'),

    path('api/register_user/', register_user, name='register-user'),
    path('api/users_list/', list_users, name='list-users'),
    path('api/users/<int:user_id>/', user_profile_get, name='user-profile-get'),
    path('api/users/<int:user_id>/update/', user_profile_update, name='user-profile-update'),
    path('api/users/<int:user_id>/delete/', delete_user, name='delete-user'),
    path('api/departments/create/', create_department, name='create-department'),
    path('api/departments/<int:department_id>/update/', update_department, name='update-department'),
    path('api/departments/<int:department_id>/delete/', delete_department, name='delete-department'),
    path('api/departments/', get_departments_list, name='get-departments-list'),
    path('api/get_modules_permission/', get_modules_permission, name='get-modules-permission'),

    # path('api/create_role/', create_role, name='create-role'),
    # path('api/role/<int:role_id>/update/', update_role, name='update-role'),
    # path('api/role/<int:role_id>/delete/', delete_role, name='delete-role'),
    

]

