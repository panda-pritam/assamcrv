import csv
from django.core.management.base import BaseCommand
from vdmp_progress.models import house_type, house_type_combination_mapping

class Command(BaseCommand):
    help = 'Import house type combination mapping from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                house_type_obj = None
                if row['Mapped']:
                    # Try exact match first
                    try:
                        house_type_obj = house_type.objects.get(house_type=row['Mapped'])
                    except house_type.DoesNotExist:
                        # Try case-insensitive match
                        house_type_obj = house_type.objects.filter(house_type__iexact=row['Mapped']).first()
                        if not house_type_obj:
                            # Try partial match (contains)
                            house_type_obj = house_type.objects.filter(house_type__icontains=row['Mapped'].strip()).first()
                        if not house_type_obj:
                            self.stdout.write(f"House type not found: {row['Mapped']}")
                
                house_type_combination_mapping.objects.create(
                    wall_type=row['Wall_type'],
                    roof_type=row['Roof_type'],
                    floor_type=row['Floor_type'],
                    combo_key=row['combo_key'],
                    house_type=house_type_obj
                )
        
        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))



# python manage.py import_house_mapping "C:\Users\krishna\Downloads\Unique_House_Types2.csv"