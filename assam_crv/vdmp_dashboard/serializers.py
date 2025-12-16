
from rest_framework import serializers
from .models import HouseholdSurvey
from utils import translated  


class HouseholdSurveySerializer(serializers.ModelSerializer):
    village_id = serializers.IntegerField(source='village.id', read_only=True)
    village_name = serializers.SerializerMethodField()

    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    district_name = serializers.SerializerMethodField()

    circle_id = serializers.IntegerField(source='village.gram_panchayat.circle.id', read_only=True)
    circle_name = serializers.SerializerMethodField()

    gram_panchayat_id = serializers.IntegerField(source='village.gram_panchayat.id', read_only=True)
    gram_panchayat_name = serializers.SerializerMethodField()

    class Meta:
        model = HouseholdSurvey
        fields = ['property_owner','name_of_hohh','number_of_males_including_children','number_of_females_including_children','children_below_6_years','senior_citizens',
                'id', 'last_updated',
                'village_id', 'village_name',
                'district_id', 'district_name',
                'circle_id', 'circle_name',
                'gram_panchayat_id', 'gram_panchayat_name' ]
        read_only_fields = [
            'id', 'last_updated',
            'village_id', 'village_name',
            'district_id', 'district_name',
            'circle_id', 'circle_name',
            'gram_panchayat_id', 'gram_panchayat_name'
        ]

    def update(self, instance, validated_data):
        # Preserve the original village
        validated_data['village'] = instance.village

        # Update fields except read-only
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def get_village_name(self, obj):
        return translated(obj.village, 'name')

    def get_district_name(self, obj):
        return translated(obj.village.gram_panchayat.circle.district, 'name')

    def get_circle_name(self, obj):
        return translated(obj.village.gram_panchayat.circle, 'name')

    def get_gram_panchayat_name(self, obj):
        return translated(obj.village.gram_panchayat, 'name')
