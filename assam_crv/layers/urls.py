
from django.urls import path
from .views import getLayers, showMapPage

urlpatterns = [
    path('map/', showMapPage, name='map'),
    path('api/getLayers/', getLayers, name='getLayers')
]
