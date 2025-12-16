from django.contrib import admin
from accounts.models import tblRoles, tblUser, tblDepartment, tblModule, tblModulePermission

@admin.register(tblUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('role', 'is_active', 'district')
    ordering = ('username',)

@admin.register(tblRoles)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'details')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(tblDepartment)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'details')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(tblModule)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'div_id', 'class_name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(tblModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ('department', 'module')
    search_fields = ('department__name', 'module__name')
    ordering = ('department', 'module')