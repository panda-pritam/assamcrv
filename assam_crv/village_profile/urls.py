
from django.urls import path
from .views import ( get_districts, get_circles, get_gram_panchayats, get_villages, villages_by_district, 
                    add_district_crlcle_gp_vill_by_csv,get_all_districts, get_all_villages, get_all_circles, get_all_gram_panchayats,
                    create_circle, create_district, create_gram_panchayat, create_village, update_circle, update_district
                     ,update_gram_panchayat, update_village, delete_circle, delete_district, delete_gram_panchayat, delete_village,update_locations, get_village_count, get_location_counts, sync_mobile_db_villages )

from .views import count_of_villages_with_survey

urlpatterns = [
    path('api/get_districts', get_districts, name='get_districts'),
    path('api/get_circles', get_circles, name='get_circles'),
    path('api/get_gram_panchayats', get_gram_panchayats, name='get_gram_panchayats'),
    path('api/get_villages', get_villages, name='get_villages'),
    path('api/villages_by_district', villages_by_district, name='villages_by_district'),

    path('api/get_all_districts', get_all_districts, name='get_all_districts'),
    path('api/get_all_villages', get_all_villages, name='get_all_villages'),
    path('api/get_all_circles', get_all_circles, name='get_all_circles'),
    path('api/get_all_gram_panchayats', get_all_gram_panchayats, name='get_all_gram_panchayats'),

    #create
    path('api/create_circle', create_circle, name='create_circle'),
    path('api/create_district', create_district, name='create_district'),
    path('api/create_gram_panchayat', create_gram_panchayat, name='create_gram_panchayat'),
    path('api/create_village', create_village, name='create_village'),

    #update
    path('api/<int:circle_id>/update_circle', update_circle, name='update_circle'),
    path('api/<int:district_id>/update_district', update_district, name='update_district'),
    path('api/<int:gram_panchayat_id>/update_gram_panchayat', update_gram_panchayat, name='update_gram_panchayat'),
    path('api/<int:village_id>/update_village', update_village, name='update_village'),

    #delete
    path('api/<int:circle_id>/delete_circle', delete_circle, name='delete_circle'),
    path('api/<int:district_id>/delete_district', delete_district, name='delete_district'),
    path('api/<int:gram_panchayat_id>/delete_gram_panchayat', delete_gram_panchayat, name='delete_gram_panchayat'),
    path('api/<int:village_id>/delete_village', delete_village, name='delete_village'),

    path('api/update_locations', update_locations, name='update_locations'),
    path('api/get_village_count', get_village_count, name='get_village_count'),
    path('api/get_location_counts', get_location_counts, name='get_location_counts'),
    #add via csv
    path('api/add_district_crlcle_gp_vill_by_csv', add_district_crlcle_gp_vill_by_csv, name='add_district_crlcle_gp_vill_by_csv'),
    
    # Sync mobile DB
    path('api/sync_mobile_db_villages', sync_mobile_db_villages, name='sync_mobile_db_villages'),


    path('api/count_of_villages_with_survey', count_of_villages_with_survey, name='count_of_villages_with_survey'),
]
