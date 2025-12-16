
from rest_framework import serializers
from .models import tbl_Rescue_Equipment, tbl_Rescue_Equipment_Status
from django.utils.translation import get_language
from utils import translated  

class Rescue_EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_Rescue_Equipment
        fields = '__all__'
        extra_kwargs = {
            'task_force': {'allow_blank': True, 'required': False},
            'task_force_bn': {'allow_blank': True, 'required': False},
            'task_force_as': {'allow_blank': True, 'required': False},
            'specification': {'allow_blank': True, 'required': False},
            'specification_bn': {'allow_blank': True, 'required': False},
            'specification_as': {'allow_blank': True, 'required': False},
        }
    
    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Equipment name is required")
        
        name = value.strip()
        # Check for duplicate name (exclude current instance for updates)
        queryset = tbl_Rescue_Equipment.objects.filter(name__iexact=name)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Equipment with this name already exists")
        
        return name
    

class DropdownRescue_EquipmentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = tbl_Rescue_Equipment
        fields = ['id', 'name',]
        
    def get_name(self, obj):
        lang = get_language()
        field_name = f'name_{lang}'
        return getattr(obj, field_name, None) or obj.name


class Rescue_Equipment_StatusSerializer(serializers.ModelSerializer):
    equipment_id = serializers.IntegerField(source='equipment.id', read_only=True)
    equipment_name = serializers.SerializerMethodField()
    equipment_specification = serializers.SerializerMethodField()
    equipment_task_force = serializers.SerializerMethodField()

    village_id = serializers.IntegerField(source='village.id', read_only=True)
    village_name = serializers.SerializerMethodField()

    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    district_name = serializers.SerializerMethodField()

    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = tbl_Rescue_Equipment_Status
        fields = [
            'id', 'equipment', 'village',
            'equipment_id', 'equipment_name', 'equipment_specification', 'equipment_task_force',
            'village_id', 'village_name',
            'district_id', 'district_name',
            'count', 'last_update', 'updated_by'
        ]
        extra_kwargs = {
            'equipment': {'write_only': True},
            'village': {'write_only': True}
        }

    def get_equipment_name(self, obj):
        return translated(obj.equipment, 'name')

    def get_equipment_specification(self, obj):
        return translated(obj.equipment, 'specification')

    def get_equipment_task_force(self, obj):
        return translated(obj.equipment, 'task_force')

    def get_village_name(self, obj):
        return translated(obj.village, 'name')

    def get_district_name(self, obj):
        return translated(obj.village.gram_panchayat.circle.district, 'name')

    def validate_count(self, value):
        if value is None:
            raise serializers.ValidationError("Count is required")
        if value < 0:
            raise serializers.ValidationError("Count cannot be negative")
        return value
