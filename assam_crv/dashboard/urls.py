from django.urls import path
from .views import home, dashboard_chart_data, mitigation_intervention, mitigation_intervention_1, mitigation_intervention_3, other_data

urlpatterns = [
    path('', home, name='home'),

    path('api/dashboard_chart_data/', dashboard_chart_data, name='dashboard_chart_data'),
    path('mitigation-intervention/', mitigation_intervention, name='mitigation_intervention'),
    path('mitigation-intervention-1/', mitigation_intervention_1, name='mitigation_intervention_1'),
    path('mitigation-intervention-3/', mitigation_intervention_3, name='mitigation_intervention_3'),
    path('other-data/', other_data, name='other_data'),

]
