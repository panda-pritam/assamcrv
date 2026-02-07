import pandas as pd
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from vdmp_progress.models import flood_MDR_table, EQ_MDR_table, wind_MDR_table, house_type


class Command(BaseCommand):
    help = 'Import MDR data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flood-file',
            type=str,
            help='Path to Flood_MDR.xlsx file'
        )
        parser.add_argument(
            '--wind-file',
            type=str,
            help='Path to Wind_MDR.xlsx file'
        )
        parser.add_argument(
            '--eq-file',
            type=str,
            help='Path to EQ_MDR.xlsx file'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Directory containing all MDR Excel files (flood, wind, eq)'
        )

    def get_file_path(self, explicit_path=None, env_var=None, default_name=None):
        """
        Resolve file path from multiple sources (priority order):
        1. Explicit command-line argument
        2. Environment variable
        3. Default location in project media directory
        """
        if explicit_path:
            path = Path(explicit_path)
            if path.exists():
                return str(path.resolve())
            else:
                raise FileNotFoundError(f"File not found: {path}")

        if env_var and os.getenv(env_var):
            path = Path(os.getenv(env_var))
            if path.exists():
                return str(path.resolve())
            else:
                raise FileNotFoundError(f"File not found (env var {env_var}): {path}")

        if default_name:
            # Try in project media directory
            media_path = Path(settings.MEDIA_ROOT) / "mdr_data" / default_name
            if media_path.exists():
                return str(media_path.resolve())
            
            # Try in current directory
            local_path = Path(default_name)
            if local_path.exists():
                return str(local_path.resolve())

        return None

    def handle(self, *args, **options):
        # Get directory path if provided
        data_dir = options.get('data_dir')
        
        # Resolve file paths with fallback chain
        flood_file = self.get_file_path(
            explicit_path=options.get('flood_file') or (os.path.join(data_dir, 'Flood_MDR.xlsx') if data_dir else None),
            env_var='MDR_FLOOD_FILE',
            default_name='Flood_MDR.xlsx'
        )
        
        wind_file = self.get_file_path(
            explicit_path=options.get('wind_file') or (os.path.join(data_dir, 'Wind_MDR.xlsx') if data_dir else None),
            env_var='MDR_WIND_FILE',
            default_name='Wind_MDR.xlsx'
        )
        
        eq_file = self.get_file_path(
            explicit_path=options.get('eq_file') or (os.path.join(data_dir, 'EQ_MDR.xlsx') if data_dir else None),
            env_var='MDR_EQ_FILE',
            default_name='EQ_MDR.xlsx'
        )

        # Check that all files exist
        missing_files = []
        for name, path in [('Flood', flood_file), ('Wind', wind_file), ('EQ', eq_file)]:
            if not path:
                missing_files.append(f"{name}: {name}_MDR.xlsx")

        if missing_files:
            self.stdout.write(self.style.ERROR(
                'Missing MDR files:\n' + '\n'.join(missing_files) + 
                '\n\nUsage:\n'
                'python manage.py import_mdr_data --data-dir /path/to/mdr/files\n'
                'OR\n'
                'python manage.py import_mdr_data --flood-file path/to/flood.xlsx --wind-file path/to/wind.xlsx --eq-file path/to/eq.xlsx\n'
                'OR set environment variables: MDR_FLOOD_FILE, MDR_WIND_FILE, MDR_EQ_FILE'
            ))
            return


        # Import Flood MDR data
        try:
            self.stdout.write('Importing Flood MDR data...')
            df_flood = pd.read_excel(flood_file)
            for _, row in df_flood.iterrows():
                house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
                flood_MDR_table.objects.create(
                    flood_depth_m=row['Flood_depth_m'],
                    MDR_value=row['MDR'],
                    house_type=house_type_obj
                )
            self.stdout.write(f'✓ Imported {len(df_flood)} flood MDR records')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'× Error importing flood MDR: {str(e)}'))

        # Import Wind MDR data
        try:
            self.stdout.write('Importing Wind MDR data...')
            df_wind = pd.read_excel(wind_file)
            for _, row in df_wind.iterrows():
                house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
                wind_MDR_table.objects.create(
                    wind_speed_kmph=row['Wind_speed_kmph'],
                    MDR_value=row['MDR'],
                    house_type=house_type_obj
                )
            self.stdout.write(f'✓ Imported {len(df_wind)} wind MDR records')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'× Error importing wind MDR: {str(e)}'))

        # Import EQ MDR data
        try:
            self.stdout.write('Importing EQ MDR data...')
            df_eq = pd.read_excel(eq_file)
            for _, row in df_eq.iterrows():
                house_type_obj = house_type.objects.get(house_type_id=int(row['House_Type_id']))
                EQ_MDR_table.objects.create(
                    PGA_g=row['PGA_g'],
                    MDR_value=row['MDR'],
                    house_type=house_type_obj
                )
            self.stdout.write(f'✓ Imported {len(df_eq)} EQ MDR records')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'× Error importing EQ MDR: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully imported all MDR data'))