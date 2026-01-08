from django.urls import path
from .views import home, dashboard_chart_data,mitigation_intervention,other_data

urlpatterns = [
    path('', home, name='home'),

    path('api/dashboard_chart_data/', dashboard_chart_data, name='dashboard_chart_data'),
    path('mitigation-intervention/', mitigation_intervention, name='mitigation_intervention'),
    path('other-data/', other_data, name='other_data'),

]
