from rest_framework import viewsets
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Case, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce, Lower, Trim

from .models import MitigationInterventionMaster, MitigationPlanItem
from vdmp_progress.models import Risk_Assessment_Result, house_type
from vdmp_dashboard.models import Critical_Facility, VillageRoadInfo, VillageRoadInfoErosion
from .serializers import (
    MitigationInterventionMasterSerializer,
    MitigationPlanItemSerializer,
)


class MitigationInterventionMasterViewSet(viewsets.ModelViewSet):
    queryset = MitigationInterventionMaster.objects.all()
    serializer_class = MitigationInterventionMasterSerializer

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
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


@method_decorator(csrf_exempt, name="dispatch")
class MitigationPlanItemViewSet(viewsets.ModelViewSet):
    queryset = MitigationPlanItem.objects.select_related("master", "village")
    serializer_class = MitigationPlanItemSerializer
    authentication_classes = []

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
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

    def create(self, request, *args, **kwargs):
        village_id = request.data.get("village")
        master_id = request.data.get("master")
        typology = request.data.get("typology")
        vulnerability_type = request.data.get("vulnerability_type")
        item_status = request.data.get("status") or "draft"
        if village_id and master_id:
            exists = MitigationPlanItem.objects.filter(
                village_id=village_id,
                master_id=master_id,
                typology=typology or "",
                vulnerability_type=vulnerability_type or "",
                status=item_status,
            ).exists()
            if exists:
                return Response(
                    {
                        "detail": (
                            "This intervention already exists for the selected "
                            "village. Please edit the existing entry."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().create(request, *args, **kwargs)


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


@api_view(["GET"])
def get_vulnerable_assets_summary(request):
    village_id = request.query_params.get("village_id")
    base_queryset = Risk_Assessment_Result.objects.filter(
        asset_type="household"
    )
    if village_id:
        base_queryset = base_queryset.filter(village_id=village_id)

    results = []
    for house in (
        house_type.objects.exclude(building_type__iexact="critical").order_by(
            "house_type"
        )
    ):
        house_qs = base_queryset.filter(house_type_id=house)
        count = house_qs.count()
        flood_gt_zero = house_qs.filter(flood_hazard__gt=0).exists()
        flood_gt_one = house_qs.filter(flood_hazard__gt=1).exists()
        erosion_valid = (
            house_qs.filter(erosion_class__isnull=False)
            .exclude(erosion_class__iexact="")
            .exclude(erosion_class__iexact="low")
            .exclude(erosion_class__iexact="Unknown")
            .exclude(erosion_class__iexact="nan")
            .exclude(erosion_class__iexact="null")
            .exists()
        )

        if flood_gt_one and erosion_valid:
            hazard_type = "Both"
        elif flood_gt_zero:
            hazard_type = "Flood"
        elif erosion_valid:
            hazard_type = "Erosion"
        else:
            hazard_type = "-"

        results.append(
            {
                "house_type": house.house_type,
                "hazard_type": hazard_type,
                "count": count,
            }
        )

    return Response(results)


def _classify_flood_category(flood_hazard):
    flood_value = float(flood_hazard or 0)
    if flood_value >= 1.0:
        return "severe"
    if flood_value >= 0.5:
        return "high"
    if flood_value >= 0.3:
        return "medium"
    return "low"


def _normalize_risk_category(flood_hazard, erosion_class):
    flood_category = _classify_flood_category(flood_hazard)
    flood_high = flood_category in {"high", "severe"}
    erosion_value = str(erosion_class or "").strip().lower()
    erosion_high = erosion_value in {"high", "severe"}
    if erosion_high:
        return "Relocate and reconstruct"
    if flood_high:
        return "Renovate/Reconstruct"
    return "Safe"


@api_view(["GET"])
def get_housing_risk_summary(request):
    village_id = request.query_params.get("village_id")
    base_queryset = Risk_Assessment_Result.objects.filter(
        asset_type="household"
    )
    if village_id:
        base_queryset = base_queryset.filter(village_id=village_id)

    summary = (
        base_queryset.annotate(
            erosion_norm=Lower(Trim(Coalesce("erosion_class", Value(""))))
        )
        .values("house_type_name")
        .annotate(
            flood_vulnerable=Sum(
                Case(
                    When(Q(flood_hazard__gte=0.5), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            erosion_vulnerable=Sum(
                Case(
                    When(
                        Q(erosion_norm__in=["high", "severe"]),
                        then=Value(1),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
            flood_erosion_vulnerable=Sum(
                Case(
                    When(
                        Q(flood_hazard__gte=0.5)
                        & Q(erosion_norm__in=["high", "severe"]),
                        then=Value(1),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
        )
        .order_by("house_type_name")
    )

    results = []
    for row in summary:
        results.append(
            {
                "house_type": row["house_type_name"] or "-",
                "flood_vulnerable": int(row["flood_vulnerable"] or 0),
                "erosion_vulnerable": int(row["erosion_vulnerable"] or 0),
                "flood_erosion_vulnerable": int(
                    row["flood_erosion_vulnerable"] or 0
                ),
            }
        )

    return Response(results)


@api_view(["GET"])
def get_critical_risk_list(request):
    village_id = request.query_params.get("village_id")
    base_queryset = Risk_Assessment_Result.objects.filter(
        asset_type="critical_facility"
    )
    if village_id:
        base_queryset = base_queryset.filter(village_id=village_id)

    records = list(
        base_queryset.values(
            "reference_id",
            "building_area_sqft",
            "flood_hazard",
            "erosion_class",
        )
    )

    reference_ids = [
        int(ref_id)
        for ref_id in (row.get("reference_id") for row in records)
        if str(ref_id or "").isdigit()
    ]
    facility_map = {
        str(facility.id): facility
        for facility in Critical_Facility.objects.filter(id__in=reference_ids)
    }

    results = []
    for row in records:
        reference_id = str(row.get("reference_id") or "")
        facility = facility_map.get(reference_id)
        name = "-"
        occupancy_type = "-"
        if facility:
            name = facility.name_of_building or "-"
            occupancy_type = facility.occupancy_type or "-"

        results.append(
            {
                "reference_id": reference_id or "-",
                "facility_name": name,
                "occupancy_type": occupancy_type,
                "area_sqft": row.get("building_area_sqft") or 0,
                "risk_category": _normalize_risk_category(
                    row.get("flood_hazard"), row.get("erosion_class")
                ),
            }
        )

    return Response(results)


@api_view(["GET"])
def get_road_risk_summary(request):
    village_id = request.query_params.get("village_id")
    flood_qs = VillageRoadInfo.objects.all()
    erosion_qs = VillageRoadInfoErosion.objects.all()
    if village_id:
        flood_qs = flood_qs.filter(village_id=village_id)
        erosion_qs = erosion_qs.filter(village_id=village_id)

    flood_qs = flood_qs.exclude(road_surface_type__istartswith="WRD")
    erosion_qs = erosion_qs.exclude(road_surface_type__istartswith="WRD")

    flood_summary = {
        row["road_surface_type"]: float(row["total_length"] or 0)
        for row in flood_qs.values("road_surface_type").annotate(
            total_length=Sum("road_length_m")
        )
    }
    erosion_summary = {
        row["road_surface_type"]: float(row["total_length"] or 0)
        for row in erosion_qs.values("road_surface_type").annotate(
            total_length=Sum("road_length_m")
        )
    }

    road_types = sorted(set(flood_summary) | set(erosion_summary))
    results = []
    for road_type in road_types:
        results.append(
            {
                "road_type": road_type or "-",
                "flood_length_m": flood_summary.get(road_type, 0),
                "erosion_length_m": erosion_summary.get(road_type, 0),
            }
        )

    return Response(results)
