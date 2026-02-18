from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MitigationInterventionMasterViewSet,
    MitigationPlanItemViewSet,
    get_interventions,
    get_subthemes,
    get_themes,
    get_vulnerable_assets,
)

router = DefaultRouter()
router.register(r"master", MitigationInterventionMasterViewSet, basename="mitigation-master")
router.register(r"plan-items", MitigationPlanItemViewSet, basename="mitigation-plan-item")

urlpatterns = [
    path("", include(router.urls)),
    path("themes/", get_themes, name="mitigation-themes"),
    path("subthemes/", get_subthemes, name="mitigation-subthemes"),
    path("vulnerable-assets/", get_vulnerable_assets, name="mitigation-vulnerable-assets"),
    path("interventions/", get_interventions, name="mitigation-interventions"),
]
