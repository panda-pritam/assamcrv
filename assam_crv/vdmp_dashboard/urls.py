
from django.urls import path
from .views import ( vdmp_dashboard,get_household_summary_data, generate_pdf_view,
                     upload_data_vdmp, delete_vdmp_data, download_report)


from .views import download_excels_format
urlpatterns = [
    path('vdmp_dashboard', vdmp_dashboard, name='vdmp_dashboard'),

    path('api/upload_data_vdmp' , upload_data_vdmp, name='upload_data_vdmp'),
    path('api/delete_vdmp_data', delete_vdmp_data, name='delete_vdmp_data'),
    path('api/get_household_summary_data', get_household_summary_data, name='get_household_summary_data'),
    path('api/download_report', download_report, name='download_report'),
    path('report', generate_pdf_view, name='generate_pdf'),

    path('api/download_excels_format', download_excels_format, name='download_excels_format'),

]


# from django.urls import path
# from . import views

# urlpatterns = [
#     # path('sync-attributes/', views.sync_attributes_view, name='sync_attributes'),
#     path('test-dynamic-sql/', views.test_dynamic_sql, name='test_dynamic_sql'),
#     path('list-mappings/', views.list_mappings, name='list_mappings'),
# ]