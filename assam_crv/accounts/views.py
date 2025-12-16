
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ( RegisterUserSerializer, UserSerializer, UserProfileSerializer, UpdateUserSerializer, DepartmentSerializer,
                          ListDepartmentSerializer, ChangePasswordSerializer, ModuleSerializer ) 
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect
from .models import tblUser, tblModulePermission, tblDepartment
from utils import is_admin_or_superuser, get_filtered_users
from django.contrib.auth.decorators import login_required, user_passes_test


# def home_view(request):
#     """Renders the main dashboard page.
#     This is the default landing page after login."""
#     return redirect('vdmp_dashboard')
#     # return render(request, 'dashboard.html')


@login_required
def get_profile(request):
    """Displays the logged-in user's profile.
    Fetches related location and department hierarchy."""
    user = request.user
    village = getattr(user, 'village', None)
    gram_panchayat = getattr(village, 'gram_panchayat', None) if village else None
    circle = getattr(gram_panchayat, 'circle', None) if gram_panchayat else None
    district = getattr(circle, 'district', None) if circle else None

    context = {
        'department': getattr(user.department, 'name', None),
        'district': getattr(district, 'name', None),
        'circle': getattr(circle, 'name', None),
        'gram_panchayat': getattr(gram_panchayat, 'name', None),
        'village': getattr(village, 'name', None),
    }

    return render(request, 'accounts/profile.html', context)


@api_view(['PATCH'])
@login_required
def update_user_profile(request):
    """Updates the profile data of the logged-in user.
    Accepts partial data for profile update."""
    user = request.user
    serializer = UserProfileSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def login_view(request):
    """Handles user authentication and login.
    Supports session expiry toggle via 'remember me'."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')


@api_view(['POST'])
@login_required
@user_passes_test(is_admin_or_superuser)
def register_user(request):
    """Registers a new user via API.
    Only admin or superuser is allowed to perform this."""
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile_get(request, user_id):
    """Returns profile details for the given user ID.
    Returns 404 if the user does not exist."""
    try:
        user = tblUser.objects.get(id=user_id)
    except tblUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def user_profile_update(request, user_id):
    """Updates a specific user's profile.
    Accepts partial data; returns 404 if user not found."""
    try:
        user = tblUser.objects.get(id=user_id)
    except tblUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UpdateUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User updated successfully", "user": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@login_required
def change_password(request):
    """Allows the authenticated user to change password.
    Password change is validated through serializer."""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@login_required
@user_passes_test(is_admin_or_superuser)
def list_users(request):
    """Returns filtered user list based on query params.
    Admins and superusers only can access this list."""
    district_id = request.query_params.get('district_id')
    circle_id = request.query_params.get('circle_id')
    gram_panchayat_id = request.query_params.get('gram_panchayat_id')
    village_id = request.query_params.get('village_id')
    role_id = request.query_params.get('role_id')
    department_id = request.query_params.get('department_id')
    users = get_filtered_users(
        user=request.user,
        district_id=district_id,
        circle_id=circle_id,
        gram_panchayat_id=gram_panchayat_id,
        village_id=village_id,
        role_id=role_id,
        department_id=department_id
    )
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@login_required
@user_passes_test(is_admin_or_superuser)
def delete_user(request, user_id):
    """Deletes a user by ID from the database.
    Restricted to admin or superuser roles."""
    user = tblUser.objects.get(id=user_id)
    user.delete()
    return redirect('get_users_list')


@api_view(['POST'])
@login_required
@user_passes_test(is_admin_or_superuser)
def create_department(request):
    """Creates a new department and assigns permissions.
    Only accessible to admin or superuser roles."""
    permissions = request.POST.getlist("permissions")
    print(" permissions :", permissions)
    serializer = DepartmentSerializer(data=request.data)
    if serializer.is_valid():
        department = serializer.save()
        return Response({"message": "Department created successfully", "department": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@login_required
@user_passes_test(is_admin_or_superuser)
def update_department(request, department_id):
    """Updates an existing department using PATCH request.
    Only admin or superuser can update departments."""
    try:
        department = tblDepartment.objects.get(id=department_id)
    except tblDepartment.DoesNotExist:
        return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = DepartmentSerializer(department, data=request.data, partial=True)
    if serializer.is_valid():
        department = serializer.save()
        return Response({"message": "Department updated successfully", "department": serializer.data}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@login_required
@user_passes_test(is_admin_or_superuser)
def delete_department(request, department_id):
    """Deletes a department by ID.
    Returns 404 if department is not found."""
    try:
        department = tblDepartment.objects.get(id=department_id)
    except tblDepartment.DoesNotExist:
        return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

    department.delete()
    return Response({"message": "Department deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_departments_list(request):
    """Returns a list of all departments.
    Accessible without authentication or permission checks."""
    departments = tblDepartment.objects.all()
    serializer = ListDepartmentSerializer(departments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_modules_permission(request):
    """Returns permissions for a specific department.
    Accessible without authentication or permission checks."""

    user = request.user
    department = tblDepartment.objects.get(id=user.department.id)

    # Efficient query: join tblModule with tblModulePermission
    module_permissions = tblModulePermission.objects.filter(department=department).select_related('module')

    # Extract modules
    modules = [permission.module for permission in module_permissions]

    # Serialize the actual module data
    serializer = ModuleSerializer(modules, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# @api_view(['POST'])
# def create_role(request):
#     serializer = RoleSerializer(data=request.data)
#     if serializer.is_valid():
#         role = serializer.save()
#         return Response({"message": "Role created successfully", "role": serializer.data}, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# def update_role(request, role_id):
#     try:
#         role = tblRoles.objects.get(id=role_id)
#     except tblRoles.DoesNotExist:
#         return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

#     serializer = RoleSerializer(role, data=request.data, partial=True)
#     if serializer.is_valid():
#         role = serializer.save()
#         return Response({"message": "Role updated successfully", "role": serializer.data}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# def delete_role(request, role_id):
#     role = tblRoles.objects.get(id=role_id)
#     role.delete()
#     return redirect('admin_get_roles_list')

