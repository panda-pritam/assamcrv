import os
import django
import csv

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assam_crv.settings')
django.setup()

from vdmp_progress.models import house_type, house_type_combination_mapping

def import_csv(csv_file_path):
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Get house_type by matching the text
            house_type_obj = None
            if row['Mapped']:
                try:
                    house_type_obj = house_type.objects.get(house_type=row['Mapped'])
                except house_type.DoesNotExist:
                    print(f"House type not found: {row['Mapped']}")
            
            # Create the mapping record
            house_type_combination_mapping.objects.create(
                wall_type=row['Wall_type'],
                roof_type=row['Roof_type'],
                floor_type=row['Floor_type'],
                combo_key=row['combo_key'],
                house_type=house_type_obj
            )
    
    print("Import completed successfully!")

if __name__ == "__main__":
    csv_file_path = input("Enter CSV file path: ")
    import_csv(csv_file_path)