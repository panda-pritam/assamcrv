from django.core.management.base import BaseCommand
from vdmp_dashboard.models import AttributeMapping
from vdmp_progress.dynamic_sql import sync_attribute_texts


class Command(BaseCommand):
    help = 'Sync attribute texts from mobile DB and create sample mappings'

    def handle(self, *args, **options):
        self.stdout.write('Starting attribute sync...')
        
        # First sync attribute texts
        sync_attribute_texts()
        
        # Create sample mappings for HouseholdSurvey
        sample_mappings = [
            {'mobile_db_attribute_id': 1, 'alias_name': 'name_of_hohh', 'model_name': 'HouseholdSurvey'},
            {'mobile_db_attribute_id': 2, 'alias_name': 'property_owner', 'model_name': 'HouseholdSurvey'},
            {'mobile_db_attribute_id': 3, 'alias_name': 'mobile_number', 'model_name': 'HouseholdSurvey'},
            {'mobile_db_attribute_id': 4, 'alias_name': 'community', 'model_name': 'HouseholdSurvey'},
            {'mobile_db_attribute_id': 5, 'alias_name': 'wall_type', 'model_name': 'HouseholdSurvey'},
        ]
        
        created_count = 0
        for mapping_data in sample_mappings:
            mapping, created = AttributeMapping.objects.get_or_create(
                mobile_db_attribute_id=mapping_data['mobile_db_attribute_id'],
                model_name=mapping_data['model_name'],
                defaults={
                    'alias_name': mapping_data['alias_name'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample mappings')
        )
        
        # Now sync the attribute texts for the created mappings
        sync_attribute_texts()
        
        self.stdout.write(
            self.style.SUCCESS('Attribute sync completed successfully!')
        )