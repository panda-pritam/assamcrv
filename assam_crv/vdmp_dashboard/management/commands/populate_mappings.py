from django.core.management.base import BaseCommand
from vdmp_dashboard.models import AttributeMapping


class Command(BaseCommand):
    help = 'Populate AttributeMapping with common household survey fields'

    def handle(self, *args, **options):
        # Common mappings based on the existing SQL
        mappings = [
            {'pattern': 'Name of the head of household', 'alias': 'name_of_hohh'},
            {'pattern': 'Property ownership', 'alias': 'property_owner'},
            {'pattern': 'Name of person', 'alias': 'name_of_person'},
            {'pattern': 'Photo with coordinates', 'alias': 'photo'},
            {'pattern': 'phone number', 'alias': 'mobile_number'},
            {'pattern': 'data access in phone', 'alias': 'data_access'},
            {'pattern': 'Community', 'alias': 'community'},
            {'pattern': 'Social status', 'alias': 'social_status'},
            {'pattern': 'Economic status', 'alias': 'economic_status'},
            {'pattern': 'Wall type', 'alias': 'wall_type'},
            {'pattern': 'Roof type', 'alias': 'roof_type'},
            {'pattern': 'Floor type', 'alias': 'floor_type'},
            {'pattern': 'Number of storeys', 'alias': 'number_of_storeys'},
            {'pattern': 'Number of males', 'alias': 'number_of_males_including_children'},
            {'pattern': 'Number of females', 'alias': 'number_of_females_including_children'},
            {'pattern': 'children age < 6', 'alias': 'children_below_6_years'},
            {'pattern': 'age > 60', 'alias': 'senior_citizens'},
            {'pattern': 'pregnant women', 'alias': 'pregnant_women'},
            {'pattern': 'lactating women', 'alias': 'lactating_women'},
            {'pattern': 'permanently disabled', 'alias': 'persons_with_disability_or_chronic_disease'},
            {'pattern': 'Drinking water source', 'alias': 'drinking_water_source'},
            {'pattern': 'Sanitation facility', 'alias': 'sanitation_facility'},
            {'pattern': 'Digital media owned', 'alias': 'digital_media_owned'},
            {'pattern': 'electric connection', 'alias': 'house_has_electric_connection'},
            {'pattern': 'Own agriculture land', 'alias': 'own_agriculture_land'},
            {'pattern': 'Livelihood primary', 'alias': 'livelihood_primary'},
            {'pattern': 'Big cattle', 'alias': 'do_you_have_big_cattle_cattle_buffalo'},
            {'pattern': 'Small cattle', 'alias': 'do_you_have_small_cattle_goat_sheep_pig'},
            {'pattern': 'Poultry', 'alias': 'do_you_have_poultry_chicken_and_duck'},
            {'pattern': 'Approximate income earned every year', 'alias': 'approximate_income_earned_every_year_inr'},
        ]
        
        created_count = 0
        for mapping_data in mappings:
            # Create mapping without mobile_db_attribute_id for now
            mapping, created = AttributeMapping.objects.get_or_create(
                alias_name=mapping_data['alias'],
                model_name='HouseholdSurvey',
                defaults={
                    'mobile_db_attribute_id': 0,  # Will be updated when we sync
                    'attribute_text': mapping_data['pattern'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created mapping: {mapping_data['alias']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} mappings')
        )
        
        # Special case for ID-based mapping
        special_mapping, created = AttributeMapping.objects.get_or_create(
            mobile_db_attribute_id=123,
            model_name='HouseholdSurvey',
            defaults={
                'alias_name': 'plinth_or_stilt',
                'attribute_text': 'Plinth or Stilt (ID: 123)',
                'is_active': True
            }
        )
        if created:
            self.stdout.write("Created special ID-based mapping for plinth_or_stilt")
        
        self.stdout.write(
            self.style.SUCCESS('Mapping population completed!')
        )