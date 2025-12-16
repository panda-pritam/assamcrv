from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import FieldImage
from .serializers import FieldImageSerializer, BulkFieldImageSerializer
from village_profile.models import tblVillage
from django.shortcuts import get_object_or_404

from django.shortcuts import render

class FieldImageViewSet(viewsets.ModelViewSet):
    serializer_class = FieldImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = FieldImage.objects.all()
        params = self.request.query_params

        district_id = params.get('district_id')
        circle_id = params.get('circle_id')
        gp_id = params.get('gram_panchayat_id')
        village_id = params.get('village_id')
        category = params.get('category')

        if district_id:
            queryset = queryset.filter(village__gram_panchayat__circle__district_id=district_id)
        if circle_id:
            queryset = queryset.filter(village__gram_panchayat__circle_id=circle_id)
        if gp_id:
            queryset = queryset.filter(village__gram_panchayat_id=gp_id)
        if village_id:
            queryset = queryset.filter(village_id=village_id)
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by("-upload_datetime")

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='by-village/(?P<village_id>[^/.]+)')
    def by_village(self, request, village_id=None):
        village = get_object_or_404(tblVillage, pk=village_id)
        images = FieldImage.objects.filter(village=village)
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        serializer = BulkFieldImageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            created_images = serializer.save()
            response_serializer = FieldImageSerializer(created_images, many=True, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        return Response(FieldImage.CATEGORY_CHOICES)


def getAdmin(request):
    return render(request, 'administrator/field_images/index.html')



