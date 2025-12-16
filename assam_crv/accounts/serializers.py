# core/serializers.py

from rest_framework import serializers
from .models import tblUser, tblRoles, tblDepartment, tblModule, tblModulePermission
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.utils.translation import get_language

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = tblUser
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'mobile', 'district', 'gram_panchayat', 'circle', 'village', 'role', 'department']

    def validate_username(self, value):
        if tblUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if tblUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)

        user = tblUser.objects.create(**validated_data)

        return user

class UpdateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = tblUser
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'mobile', 'district', 'gram_panchayat', 'circle', 'village', 'role', 'department']
    
    def update(self, instance, validated_data):
        # Only update password if it's provided
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.password = make_password(password)

        instance.save()
        return instance
    

class UserSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()
    circle_name = serializers.SerializerMethodField()
    gram_panchayat_name = serializers.SerializerMethodField()
    village_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = tblUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'mobile',
            'district', 'gram_panchayat', 'circle', 'village', 'role', 'role_name',
            'is_active', 'district_name', 'circle_name', 'gram_panchayat_name',
            'village_name', 'department', 'department_name'
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def get_localized_name(self, obj):
        lang = get_language()
        if not obj:
            return None
        return getattr(obj, f'name_{lang}', None) or getattr(obj, 'name', None)

    def get_district_name(self, obj):
        return self.get_localized_name(obj.district)

    def get_circle_name(self, obj):
        return self.get_localized_name(obj.circle)

    def get_gram_panchayat_name(self, obj):
        return self.get_localized_name(obj.gram_panchayat)

    def get_village_name(self, obj):
        return self.get_localized_name(obj.village)

    def get_role_name(self, obj):
        return self.get_localized_name(obj.role)

    def get_department_name(self, obj):
        return self.get_localized_name(obj.department)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = tblRoles
        fields = '__all__'


class ListDepartmentSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = tblDepartment
        fields = '__all__' 
        extra_fields = ['permissions']  

    def get_permissions(self, obj):
        return tblModulePermission.objects.select_related('module') \
            .filter(department=obj) \
            .values_list('module_id', flat=True)

 

class DepartmentSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=tblModule.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = tblDepartment
        fields = ['id', 'name', 'name_bn', 'name_as', 'details', 'permissions']

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        department = tblDepartment.objects.create(**validated_data)
        for module in permissions:
            tblModulePermission.objects.create(department=department, module=module)
        return department

    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if permissions is not None:
            # Clear existing and add new module permissions
            tblModulePermission.objects.filter(department=instance).delete()
            for module in permissions:
                tblModulePermission.objects.create(department=instance, module=module)

        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = tblUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'mobile'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not user.check_password(old_password):
            raise serializers.ValidationError("Old password is incorrect")

        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match")

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.password = make_password(self.validated_data['new_password'])
        user.save()
        return user



class ModuleSerializer(serializers.ModelSerializer):
    module_name = serializers.SerializerMethodField()

    class Meta:
        model = tblModule
        fields = ['module_name', 'class_name', 'div_id']

    def get_module_name(self, obj):
        lang = get_language()
        localized_field = f'name_{lang}'
        return getattr(obj, localized_field, None) or obj.name