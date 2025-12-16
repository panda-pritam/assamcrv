from django.urls import path
from .views import home, dashboard_chart_data

urlpatterns = [
    path('', home, name='home'),

    path('api/dashboard_chart_data/', dashboard_chart_data, name='dashboard_chart_data'),

]
