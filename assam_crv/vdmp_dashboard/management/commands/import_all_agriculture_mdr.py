import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from vdmp_dashboard.models import (
    agricultureLandFloodMDRMapping,
    agricultureLandWindMDRMapping,
    agricultureLandEQMDRMapping
)

class Command(BaseCommand):
    help = 'Import all agriculture MDR data from static/csv_exports directory'

    def handle(self, *args, **options):
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'csv_exports')
        
        # Import flood data
        flood_file = os.path.join(static_dir, 'aggri_flood_mdr.xlsx')
        if os.path.exists(flood_file):
            self.import_flood_mdr(flood_file)
        else:
            self.stdout.write(self.style.WARNING(f'Flood file not found: {flood_file}'))
        
        # Import wind data
        wind_file = os.path.join(static_dir, 'aggei_wind_mdr.xlsx')
        if os.path.exists(wind_file):
            self.import_wind_mdr(wind_file)
        else:
            self.stdout.write(self.style.WARNING(f'Wind file not found: {wind_file}'))
        
        # Import earthquake data
        eq_file = os.path.join(static_dir, 'arrgre_eq_mdr.xlsx')
        if os.path.exists(eq_file):
            self.import_eq_mdr(eq_file)
        else:
            self.stdout.write(self.style.WARNING(f'EQ file not found: {eq_file}'))

    def import_flood_mdr(self, file_path):
        self.stdout.write('Importing flood MDR data...')
        df = pd.read_excel(file_path)
        
        agricultureLandFloodMDRMapping.objects.all().delete()
        
        for _, row in df.iterrows():
            agricultureLandFloodMDRMapping.objects.create(
                flood_depth_m=row['Flood_depth_m'],
                mdr=row['MDR'],
                crop_type=row['House_Type_id']
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} flood MDR records'))

    def import_wind_mdr(self, file_path):
        self.stdout.write('Importing wind MDR data...')
        df = pd.read_excel(file_path)
        
        agricultureLandWindMDRMapping.objects.all().delete()
        
        for _, row in df.iterrows():
            agricultureLandWindMDRMapping.objects.create(
                wind_hazard=row['Wind_speed_kmph'],
                mdr=row['MDR'],
                crop_type=row['House_Type_id']
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} wind MDR records'))

    def import_eq_mdr(self, file_path):
        self.stdout.write('Importing earthquake MDR data...')
        df = pd.read_excel(file_path)
        
        agricultureLandEQMDRMapping.objects.all().delete()
        
        for _, row in df.iterrows():
            agricultureLandEQMDRMapping.objects.create(
                eq_hazard=row['PGA_g'],
                mdr=row['MDR'],
                crop_type=row['House_Type_id']
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} earthquake MDR records'))