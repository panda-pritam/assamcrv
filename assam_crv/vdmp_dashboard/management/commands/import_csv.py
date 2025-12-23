import csv
from django.core.management.base import BaseCommand
from vdmp_dashboard.models import AttributeMapping

class Command(BaseCommand):
    help = 'Import CSV data to AttributeMapping model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def get_tab_info(self, model_name):
        mapping = {
            'HouseholdSurvey': (1, "Household"),
            'Commercial': (5, "Commercial Buildings"),
            'BridgeSurvey': (4, "Bridge"),
            'Critical_Facility': (3, "Critical Facilities")
        }
        return mapping.get(model_name, (None, None))

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        created_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    tab_id, tab_name = self.get_tab_info(row['model_name'])
                    
                    AttributeMapping.objects.create(
                        mobile_db_attribute_id=int(row['mobile_db_attribute_id']) if row['mobile_db_attribute_id'].strip() else None,
                        attribute_text=row['attribute_text'].strip() if row['attribute_text'].strip() else None,
                        alias_name=row['alias_name'].strip() if row['alias_name'].strip() else None,
                        model_name=row['model_name'].strip(),
                        is_calculated=row['is_calculated'].lower() == 'true' if row['is_calculated'].strip() else False,
                        is_active=row['is_active'].lower() == 'true' if row['is_active'].strip() else True,
                        tab_id=tab_id,
                        tab_name=tab_name
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.stdout.write(f"Error processing row {row}: {e}")
        
        self.stdout.write(f"Successfully created {created_count} AttributeMapping records")