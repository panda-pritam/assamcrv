from django.contrib import admin
from .models import tblDistrict, tblCircle, tblGramPanchayat, tblVillage

@admin.register(tblDistrict)
class tblDistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(tblCircle)
class tblCircleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'district')
    list_filter = ('district',)
    search_fields = ('name',)


@admin.register(tblGramPanchayat)
class tblGramPanchayatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'circle', 'get_district')
    list_filter = ('circle__district', 'circle')
    search_fields = ('name',)

    def get_district(self, obj):
        return obj.circle.district
    get_district.short_description = 'District'


@admin.register(tblVillage)
class tblVillageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'gram_panchayat', 'get_circle', 'get_district')
    list_filter = ('gram_panchayat__circle__district', 'gram_panchayat__circle', 'gram_panchayat')
    search_fields = ('name', 'code')

    def get_circle(self, obj):
        return obj.gram_panchayat.circle
    get_circle.short_description = 'Circle'

    def get_district(self, obj):
        return obj.gram_panchayat.circle.district
    get_district.short_description = 'District'
