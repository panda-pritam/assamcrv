from django.core.management.base import BaseCommand
from village_profile.models import tblVillage
from vdmp_progress.cleaning_utils import run_gis_risk_assessment_pipeline
import traceback


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

        # ===== SELECT VILLAGES =====
        if options['all']:
            villages = tblVillage.objects.all()
            self.stdout.write(f"Processing all {villages.count()} villages...")
        elif options['villages']:
            village_codes = options['villages']
            villages = tblVillage.objects.filter(code__in=village_codes)
            self.stdout.write(
                f"Processing {villages.count()} villages: {', '.join(village_codes)}"
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please provide --villages or --all flag')
            )
            return

        # ===== TRACKERS =====
        success_count = 0
        failed_count = 0
        success_villages = []
        failed_villages = []

        # ===== PROCESS LOOP =====
        for village in villages:
            try:
                self.stdout.write(f"\n{'='*80}")
                self.stdout.write(
                    self.style.WARNING(
                        f"Processing village: {village.name} ({village.code})"
                    )
                )
                self.stdout.write(f"{'='*80}\n")

                # Run pipeline
                run_gis_risk_assessment_pipeline(village, village.code)

                # Success tracking
                success_count += 1
                success_villages.append(village.code)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully processed {village.name} ({village.code}) | Success count: {success_count}"
                    )
                )

            except Exception as e:
                # Failure tracking
                failed_count += 1
                failed_villages.append(village.code)

                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Failed to process {village.name} ({village.code}): {str(e)}"
                    )
                )

                # Print traceback for debugging
                traceback.print_exc()
                continue

        # ===== FINAL SUMMARY =====
        self.stdout.write(f"\n{'='*80}")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully processed: {success_count} villages"
            )
        )
        if success_villages:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Success villages -> {', '.join(success_villages)}"
                )
            )

        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Failed: {failed_count} villages"
                )
            )
            self.stdout.write(
                self.style.ERROR(
                    f"Failed villages -> {', '.join(failed_villages)}"
                )
            )

        self.stdout.write(f"{'='*80}\n")