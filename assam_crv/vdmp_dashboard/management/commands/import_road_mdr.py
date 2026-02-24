import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from vdmp_dashboard.models import roadFloodMDRMapping

class Command(BaseCommand):
    help = 'Import road MDR data from Correct_road_MDR.(csv|xlsx)'

    def handle(self, *args, **options):
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'csv_exports')
        csv_file = os.path.join(static_dir, 'Correct_road_MDR.csv')
        xlsx_file = os.path.join(static_dir, 'Correct_road_MDR.xlsx')

        if os.path.exists(xlsx_file):
            self.import_road_mdr(xlsx_file)
            return

        if os.path.exists(csv_file):
            self.import_road_mdr(csv_file)
            return

        self.stdout.write(
            self.style.WARNING(
                f'Road file not found: {xlsx_file} or {csv_file}'
            )
        )

    def import_road_mdr(self, file_path):
        self.stdout.write('Importing road MDR data...')
        if file_path.lower().endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        self.stdout.write('File imported')
        
        roadFloodMDRMapping.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully Deleted road MDR records'))
        
        for _, row in df.iterrows():
            roadFloodMDRMapping.objects.create(
                flood_depth_m=row['Depth'],
                mdr=row['Damage'],
                road_surface_type=row['Type']
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} road MDR records'))
