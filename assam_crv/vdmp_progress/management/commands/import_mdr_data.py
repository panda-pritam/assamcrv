import pandas as pd
from django.core.management.base import BaseCommand
from vdmp_progress.models import flood_MDR_table, EQ_MDR_table, wind_MDR_table, house_type


class Command(BaseCommand):
    help = 'Import MDR data from Excel files'

    def handle(self, *args, **options):
        # File paths
        flood_file = r"C:\Users\krishna\Downloads\Assam_CRV_Automation (2)\Assam_CRV_Automation\Task3_Risk_Assessment\Flood_MDR.xlsx"
        wind_file = r"C:\Users\krishna\Downloads\Assam_CRV_Automation (2)\Assam_CRV_Automation\Task3_Risk_Assessment\Wind_MDR.xlsx"
        eq_file = r"C:\Users\krishna\Downloads\Assam_CRV_Automation (2)\Assam_CRV_Automation\Task3_Risk_Assessment\EQ_MDR.xlsx"

        # Import Flood MDR data
        self.stdout.write('Importing Flood MDR data...')
        df_flood = pd.read_excel(flood_file)
        for _, row in df_flood.iterrows():
            house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
            flood_MDR_table.objects.create(
                flood_depth_m=row['Flood_depth_m'],
                MDR_value=row['MDR'],
                house_type=house_type_obj
            )
        self.stdout.write(f'Imported {len(df_flood)} flood MDR records')

        # Import Wind MDR data
        self.stdout.write('Importing Wind MDR data...')
        df_wind = pd.read_excel(wind_file)
        for _, row in df_wind.iterrows():
            house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
            wind_MDR_table.objects.create(
                wind_speed_kmph=row['Wind_speed_kmph'],
                MDR_value=row['MDR'],
                house_type=house_type_obj
            )
        self.stdout.write(f'Imported {len(df_wind)} wind MDR records')

        # Import EQ MDR data
        self.stdout.write('Importing EQ MDR data...')
        df_eq = pd.read_excel(eq_file)
        for _, row in df_eq.iterrows():
            house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
            EQ_MDR_table.objects.create(
                PGA_g=row['PGA_g'],
                MDR_value=row['MDR'],
                house_type=house_type_obj
            )
        self.stdout.write(f'Imported {len(df_eq)} EQ MDR records')

        self.stdout.write(self.style.SUCCESS('Successfully imported all MDR data'))