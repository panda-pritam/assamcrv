from rest_framework import serializers
from .models import tblVDMP_Activity, tblVDMP_Activity_Status
from utils import translated  


class VDMPActivitySerializer(serializers.ModelSerializer):
    custom_name = serializers.SerializerMethodField()
    
    class Meta:
        model = tblVDMP_Activity
        fields = '__all__'
        
    def get_custom_name(self, obj):
        return translated(obj, 'name')


class VDMPActivityStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = tblVDMP_Activity_Status
        fields = '__all__'


class ListVDMPActivityStatusSerializer(serializers.ModelSerializer):
    activity_id = serializers.CharField(source='activity.id', read_only=True)
    activity_name = serializers.SerializerMethodField()

    village_id = serializers.IntegerField(source='village.id', read_only=True)
    village_name = serializers.SerializerMethodField()

    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    district_name = serializers.SerializerMethodField() 
    
    class Meta:
        model = tblVDMP_Activity_Status
        fields = [
            'id', 'activity_id', 'activity_name',
            'village_id', 'village_name',
            'district_id', 'district_name',
            'status', 'last_update', 'updated_by'
        ]

    def get_activity_name(self, obj):
        return translated(obj.activity, 'name')

    def get_village_name(self, obj):
        return translated(obj.village, 'name')

    def get_district_name(self, obj):
        return translated(obj.village.gram_panchayat.circle.district, 'name')


class VDMPActivityStatusSummarySerializer(serializers.Serializer):
    activity = serializers.CharField()
    not_started = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()


class DropdownVDMPActivitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = tblVDMP_Activity
        fields = ['id', 'name']

    def get_name(self, obj):
        return translated(obj, 'name')
