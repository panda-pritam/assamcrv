from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FieldImageViewSet

router = DefaultRouter()
router.register(r'field-images', FieldImageViewSet, basename='fieldimage')

urlpatterns = [
    path('', include(router.urls)),
]