from rest_framework import serializers
from .models import GeoserverLayers
from utils import translated  
import uuid

class GeoLayersSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    uuid = serializers.SerializerMethodField()

    class Meta:
        model = GeoserverLayers
        fields = ('id', 'title', 'layer_name', 'workspace', 'uuid')
    
    def get_title(self, obj):
        return translated(obj, 'title')
    
    def get_uuid(self, obj):
        return uuid.uuid4().hex
