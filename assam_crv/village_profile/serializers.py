from rest_framework import serializers
from .models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage
from utils import translated  


class DistrictSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = tblDistrict
        fields = ['id', 'name', 'code','latitude', 'longitude']

    def get_name(self, obj):
        return translated(obj, 'name')


class CircleSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = tblCircle
        fields = ['id', 'name', 'district']

    def get_name(self, obj):
        return translated(obj, 'name')


class GramPanchayatSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = tblGramPanchayat
        fields = ['id', 'name', 'circle']

    def get_name(self, obj):
        return translated(obj, 'name')


class VillageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = tblVillage
        fields = ['id', 'name', 'code', 'gram_panchayat','latitude', 'longitude']

    def get_name(self, obj):
        return translated(obj, 'name')


class ListCircleSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()

    class Meta:
        model = tblCircle
        fields = ['id', 'name', 'name_bn', 'name_as', 'district', 'district_name']

    def get_district_name(self, obj):
        return translated(obj.district, 'name')

class ListGramPanchayatSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()
    circle_name = serializers.SerializerMethodField()

    class Meta:
        model = tblGramPanchayat
        fields = ['id', 'name', 'name_bn', 'name_as', 'circle_name','circle', 'district_name']

    def get_district_name(self, obj):
        return translated(obj.circle.district, 'name')
    
    def get_circle_name(self, obj):
        return translated(obj.circle, 'name')

class ListVillageSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()
    circle_name = serializers.SerializerMethodField()
    gram_panchayat_name = serializers.SerializerMethodField()

    class Meta:
        model = tblVillage
        fields = ['id','code', 'name', 'name_bn', 'name_as', 'district_name', 'circle_name', 'gram_panchayat_name','gram_panchayat','latitude', 'longitude', 'geojson_file']

    def get_district_name(self, obj):
        return translated(obj.gram_panchayat.circle.district, 'name')

    def get_circle_name(self, obj):
        return translated(obj.gram_panchayat.circle, 'name')
    
    def get_gram_panchayat_name(self, obj):
        return translated(obj.gram_panchayat, 'name')

class ListDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = tblDistrict
        fields = '__all__'