from django.shortcuts import render
from .serializers import GeoLayersSerializer
from .models import GeoserverLayers
from rest_framework.response import Response
from rest_framework.decorators import api_view

def showMapPage(request):
    return render(request, 'layers/map.html')

@api_view(['GET'])
def getLayers(request):
    layers = GeoserverLayers.objects.all()
    serializer = GeoLayersSerializer(layers, many=True)
    return Response(serializer.data)