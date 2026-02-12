from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import MitigationInterventionMaster, MitigationPlanItem
from .serializers import (
    MitigationInterventionMasterSerializer,
    MitigationPlanItemSerializer,
)


class MitigationInterventionMasterViewSet(viewsets.ModelViewSet):
    queryset = MitigationInterventionMaster.objects.all()
    serializer_class = MitigationInterventionMasterSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        theme = self.request.query_params.get("theme")
        subtheme = self.request.query_params.get("subtheme")
        vulnerable_asset = self.request.query_params.get("vulnerable_asset")
        status = self.request.query_params.get("status")

        if theme:
            queryset = queryset.filter(theme=theme)
        if subtheme:
            queryset = queryset.filter(subtheme=subtheme)
        if vulnerable_asset:
            queryset = queryset.filter(vulnerable_asset=vulnerable_asset)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class MitigationPlanItemViewSet(viewsets.ModelViewSet):
    queryset = MitigationPlanItem.objects.select_related("master", "village")
    serializer_class = MitigationPlanItemSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        village_id = self.request.query_params.get("village_id")
        master_id = self.request.query_params.get("master_id")
        status = self.request.query_params.get("status")

        if village_id:
            queryset = queryset.filter(village_id=village_id)
        if master_id:
            queryset = queryset.filter(master_id=master_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


@api_view(["GET"])
def get_themes(request):
    queryset = MitigationInterventionMaster.objects.all()
    status = request.query_params.get("status")
    if status:
        queryset = queryset.filter(status=status)
    themes = queryset.values_list("theme", flat=True).distinct().order_by("theme")
    return Response(list(themes))


@api_view(["GET"])
def get_subthemes(request):
    queryset = MitigationInterventionMaster.objects.all()
    theme = request.query_params.get("theme")
    status = request.query_params.get("status")
    if theme:
        queryset = queryset.filter(theme=theme)
    if status:
        queryset = queryset.filter(status=status)
    subthemes = (
        queryset.values_list("subtheme", flat=True)
        .distinct()
        .order_by("subtheme")
    )
    return Response(list(subthemes))


@api_view(["GET"])
def get_vulnerable_assets(request):
    queryset = MitigationInterventionMaster.objects.all()
    theme = request.query_params.get("theme")
    subtheme = request.query_params.get("subtheme")
    status = request.query_params.get("status")
    if theme:
        queryset = queryset.filter(theme=theme)
    if subtheme:
        queryset = queryset.filter(subtheme=subtheme)
    if status:
        queryset = queryset.filter(status=status)
    assets = (
        queryset.values_list("vulnerable_asset", flat=True)
        .distinct()
        .order_by("vulnerable_asset")
    )
    return Response([a for a in assets if a])


@api_view(["GET"])
def get_interventions(request):
    queryset = MitigationInterventionMaster.objects.all()
    theme = request.query_params.get("theme")
    subtheme = request.query_params.get("subtheme")
    vulnerable_asset = request.query_params.get("vulnerable_asset")
    status = request.query_params.get("status")

    if theme:
        queryset = queryset.filter(theme=theme)
    if subtheme:
        queryset = queryset.filter(subtheme=subtheme)
    if vulnerable_asset:
        queryset = queryset.filter(vulnerable_asset=vulnerable_asset)
    if status:
        queryset = queryset.filter(status=status)

    serializer = MitigationInterventionMasterSerializer(queryset, many=True)
    return Response(serializer.data)
