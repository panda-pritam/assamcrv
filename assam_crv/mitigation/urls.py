from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MitigationInterventionMasterViewSet,
    MitigationPlanItemViewSet,
    get_critical_risk_list,
    get_housing_risk_summary,
    get_interventions,
    get_road_risk_summary,
    get_subthemes,
    get_themes,
    finalize_plan_items,
    get_vulnerable_assets,
    get_vulnerable_assets_summary,
)

router = DefaultRouter()
router.register(r"master", MitigationInterventionMasterViewSet, basename="mitigation-master")
router.register(r"plan-items", MitigationPlanItemViewSet, basename="mitigation-plan-item")

urlpatterns = [
    path("plan-items/finalize/", finalize_plan_items, name="mitigation-plan-items-finalize"),
    path("themes/", get_themes, name="mitigation-themes"),
    path("subthemes/", get_subthemes, name="mitigation-subthemes"),
    path("vulnerable-assets/", get_vulnerable_assets, name="mitigation-vulnerable-assets"),
    path(
        "vulnerable-assets-summary/",
        get_vulnerable_assets_summary,
        name="mitigation-vulnerable-assets-summary",
    ),
    path("interventions/", get_interventions, name="mitigation-interventions"),
    path(
        "housing-risk-summary/",
        get_housing_risk_summary,
        name="mitigation-housing-risk-summary",
    ),
    path(
        "critical-risk-list/",
        get_critical_risk_list,
        name="mitigation-critical-risk-list",
    ),
    path(
        "road-risk-summary/",
        get_road_risk_summary,
        name="mitigation-road-risk-summary",
    ),
    path("", include(router.urls)),
]
