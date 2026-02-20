import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from vdmp_dashboard.models import roadFloodMDRMapping

class Command(BaseCommand):
    help = 'Import road MDR data from Correct_road_MDR.xlsx'

    def handle(self, *args, **options):
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'csv_exports')
        road_file = os.path.join(static_dir, 'Correct_road_MDR.csv')
        
        if os.path.exists(road_file):
            self.import_road_mdr(road_file)
        else:
            self.stdout.write(self.style.WARNING(f'Road file not found: {road_file}'))

    def import_road_mdr(self, file_path):
        self.stdout.write('Importing road MDR data...')
        df = pd.read_csv(file_path)
        
        roadFloodMDRMapping.objects.all().delete()
        
        for _, row in df.iterrows():
            roadFloodMDRMapping.objects.create(
                flood_depth_m=row['Depth'],
                mdr=row['Damage'],
                road_surface_type=row['Type']
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} road MDR records'))
