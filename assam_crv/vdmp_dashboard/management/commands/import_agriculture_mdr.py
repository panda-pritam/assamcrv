import pandas as pd
from django.core.management.base import BaseCommand
from vdmp_dashboard.models import (
    agricultureLandFloodMDRMapping,
    agricultureLandWindMDRMapping,
    agricultureLandEQMDRMapping
)

class Command(BaseCommand):
    help = 'Import agriculture MDR data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument('--flood', type=str, help='Path to flood MDR Excel file')
        parser.add_argument('--wind', type=str, help='Path to wind MDR Excel file')
        parser.add_argument('--eq', type=str, help='Path to earthquake MDR Excel file')

    def handle(self, *args, **options):
        if options['flood']:
            self.import_flood_mdr(options['flood'])
        
        if options['wind']:
            self.import_wind_mdr(options['wind'])
            
        if options['eq']:
            self.import_eq_mdr(options['eq'])

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