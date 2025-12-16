from rest_framework import serializers
from .models import TaskForce


class TaskForceSerializer(serializers.ModelSerializer):
    village_name = serializers.CharField(source='village.name', read_only=True)
    district_name = serializers.CharField(source='village.gram_panchayat.circle.district.name', read_only=True)
    circle_name = serializers.CharField(source='village.gram_panchayat.circle.name', read_only=True)
    gram_panchayat_name = serializers.CharField(source='village.gram_panchayat.name', read_only=True)
    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    circle_id = serializers.IntegerField(source='village.gram_panchayat.circle.id', read_only=True)
    gram_panchayat_id = serializers.IntegerField(source='village.gram_panchayat.id', read_only=True)
    
    class Meta:
        model = TaskForce
        fields = '__all__'
