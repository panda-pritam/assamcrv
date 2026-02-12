from django.core.management.base import BaseCommand
from village_profile.models import tblVillage
from vdmp_progress.cleaning_utils import run_gis_risk_assessment_pipeline


class Command(BaseCommand):
    help = 'Run GIS risk assessment pipeline for specified villages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--villages',
            nargs='+',
            type=str,
            help='List of village codes (e.g., 280_6 280_13 280_19)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run for all villages',
        )

    def handle(self, *args, **options):
        if options['all']:
            villages = tblVillage.objects.all()
            self.stdout.write(f"Processing all {villages.count()} villages...")
        elif options['villages']:
            village_codes = options['villages']
            villages = tblVillage.objects.filter(code__in=village_codes)
            self.stdout.write(f"Processing {villages.count()} villages: {', '.join(village_codes)}")
        else:
            self.stdout.write(self.style.ERROR('Please provide --villages or --all flag'))
            return

        success_count = 0
        failed_count = 0

        for village in villages:
            try:
                self.stdout.write(f"\n{'='*80}")
                self.stdout.write(self.style.WARNING(f"Processing village: {village.name} ({village.code})"))
                self.stdout.write(f"{'='*80}\n")
                
                run_gis_risk_assessment_pipeline(village, village.code)
                
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Successfully processed {village.name}"))
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"❌ Failed to process {village.name}: {str(e)}"))
                continue

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully processed: {success_count} villages"))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ Failed: {failed_count} villages"))
        self.stdout.write(f"{'='*80}\n")
