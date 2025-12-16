
from rest_framework import serializers
from .models import tbl_Training_Activities_Status, tbl_Training_Activities
from utils import translated  


class TrainingActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_Training_Activities
        fields = '__all__'

class CustomTrainingActivityStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = tbl_Training_Activities_Status
        fields = '__all__'
    
    def validate_implemented_date(self, value):
        if value == '':
            return None
        return value
    
    def validate_village(self, value):
        if value is None or value == '':
            raise serializers.ValidationError("Village is required.")
        return value


class TrainingActivityStatusSerializer(serializers.ModelSerializer):
    activity_id = serializers.CharField(source='activity.id', read_only=True)
    activity_name = serializers.SerializerMethodField()

    village_id = serializers.IntegerField(source='village.id', read_only=True)
    village_name = serializers.SerializerMethodField()

    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    district_name = serializers.SerializerMethodField() 
    
    class Meta:
        model = tbl_Training_Activities_Status
        fields = [
            'id', 'activity_id', 'activity_name',
            'village_id', 'village_name',
            'district_id', 'district_name',
            'status', 'implemented_date', 'remarks', 'last_update', 'updated_by'
        ]

    def get_activity_name(self, obj):
        return translated(obj.activity, 'name')

    def get_village_name(self, obj):
        return translated(obj.village, 'name')

    def get_district_name(self, obj):
        return translated(obj.village.gram_panchayat.circle.district, 'name')
