from django.contrib.gis.db import models

class ShapefileElectricPole(models.Model):
    gid = models.IntegerField(primary_key=True)
    latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    material = models.CharField(max_length=254, null=True, blank=True)
    remarks = models.CharField(max_length=254, null=True, blank=True)
    photo_id = models.CharField(max_length=254, null=True, blank=True)
    flood = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vill_name = models.CharField(max_length=50, null=True, blank=True)
    vill_id = models.CharField(max_length=20, null=True, blank=True)
    dist_name = models.CharField(max_length=40, null=True, blank=True)
    dist_id = models.CharField(max_length=20, null=True, blank=True)
    geom = models.PointField(srid=4326, null=True, blank=True)  # Adjust SRID if needed

    class Meta:
        managed = False  # Django won’t try to create/delete this table
        db_table = 'electricpoles'  # exact table name in DB
        app_label = 'shapefiles' 


class ShapefileTransformer(models.Model):
    gid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    material = models.CharField(max_length=254, null=True, blank=True)
    vill_name = models.CharField(max_length=50, null=True, blank=True)
    vill_id = models.CharField(max_length=20, null=True, blank=True)
    dist_name = models.CharField(max_length=40, null=True, blank=True)
    dist_id = models.CharField(max_length=20, null=True, blank=True)
    flood = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    geom = models.PointField(srid=4326, null=True, blank=True)  # Adjust SRID if needed

    class Meta:
        managed = False  # Don’t let Django migrations manage this table
        db_table = 'transformer'  # Exact table name in DB
        app_label = 'shapefiles' 



class PraBoundary(models.Model):
    gid = models.IntegerField(primary_key=True)

    village = models.CharField(max_length=80, null=True, blank=True)
    district = models.CharField(max_length=80, null=True, blank=True)
    area_sqkm = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    dist_id = models.FloatField(null=True, blank=True)
    vill_id = models.CharField(max_length=15, null=True, blank=True)
    rev_circ = models.CharField(max_length=50, null=True, blank=True)
    rev_circid = models.CharField(max_length=15, null=True, blank=True)
    area_ha = models.FloatField(null=True, blank=True)
    affarea_ha = models.FloatField(null=True, blank=True)
    shalt_adq = models.FloatField(null=True, blank=True)
    elec_poles = models.IntegerField(null=True, blank=True)
    aff_poles = models.IntegerField(null=True, blank=True)
    transf = models.IntegerField(null=True, blank=True)
    aff_transf = models.IntegerField(null=True, blank=True)
    bridge = models.IntegerField(null=True, blank=True)
    aff_bridge = models.IntegerField(null=True, blank=True)


    class Meta:
        managed = False  # Django will not create/drop the table
        db_table = 'pra_boundary'
        app_label = 'shapefiles' 


class ExposureRiver(models.Model):
    gid = models.AutoField(primary_key=True)  # uses sequence
    objectid_1 = models.FloatField(null=True, blank=True)
    class_name = models.CharField(max_length=254, null=True, blank=True)
    village = models.CharField(max_length=80, null=True, blank=True)
    district = models.CharField(max_length=80, null=True, blank=True)
    vill_id = models.CharField(max_length=15, null=True, blank=True)
    rev_circ = models.CharField(max_length=50, null=True, blank=True)
    dist_id = models.CharField(max_length=15, null=True, blank=True)
    rev_circid = models.CharField(max_length=15, null=True, blank=True)
    shape_leng = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    shape_area = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    length_m = models.FloatField(null=True, blank=True)
    erosion_m = models.FloatField(null=True, blank=True)
    acretion_m = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'exposure_river'
        app_label = 'shapefiles'


class ExposureRoadVillage(models.Model):
    gid = models.AutoField(primary_key=True)  # uses sequence
    village_na = models.CharField(max_length=50, null=True, blank=True)
    length_m = models.FloatField(null=True, blank=True)
    affleng_m = models.FloatField(null=True, blank=True)
    vill_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'exposure_road_village'
        app_label = 'shapefiles'