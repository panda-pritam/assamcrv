import os
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from mitigation.models import MitigationInterventionMaster


DEFAULT_SHEET = "all themes intervention"
DEFAULT_PATH = (
    r"E:\Siraj\assam_crv\file\Mitigation intervention master table for sw team v1.xlsx"
)


def clean_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def clean_decimal(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


class Command(BaseCommand):
    help = "Import mitigation intervention master data from an Excel sheet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=DEFAULT_PATH,
            help="Excel file path (default: mitigation master file).",
        )
        parser.add_argument(
            "--sheet",
            default=DEFAULT_SHEET,
            help="Sheet name to import (default: all themes intervention).",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip rows that already exist based on key fields.",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        sheet_name = options["sheet"]
        skip_existing = options["skip_existing"]

        if not os.path.exists(file_path):
            raise CommandError(f"Excel file not found: {file_path}")

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as exc:
            raise CommandError(f"Failed to read Excel: {exc}") from exc

        df.columns = [str(col).strip() for col in df.columns]

        column_map = {
            "Theme": "theme",
            "Sub theme": "subtheme",
            "Vulnerable asset": "vulnerable_asset",
            "Vulnerable asset ": "vulnerable_asset",
            "Intervention type": "intervention_type",
            "Mitigation intervention": "intervention_name",
            "Display as Note: Explanation of mitigation intervention/Guiding points for repair": "display_note",
            "Unit": "unit",
            "Quantity": "default_quantity",
            "Unit cost (Rs)": "unit_cost_rs",
        }

        missing = [col for col in ["Theme", "Sub theme", "Mitigation intervention"] if col not in df.columns]
        if missing:
            raise CommandError(f"Missing required columns: {', '.join(missing)}")

        existing_keys = set()
        if skip_existing:
            existing_keys = set(
                MitigationInterventionMaster.objects.values_list(
                    "theme",
                    "subtheme",
                    "vulnerable_asset",
                    "intervention_type",
                    "intervention_name",
                )
            )

        records = []
        skipped = 0

        for _, row in df.iterrows():
            raw = {col: row.get(col) for col in df.columns}
            data = {}

            for excel_col, model_field in column_map.items():
                if excel_col in raw:
                    data[model_field] = raw.get(excel_col)

            theme = clean_text(data.get("theme"))
            subtheme = clean_text(data.get("subtheme"))
            vulnerable_asset = clean_text(data.get("vulnerable_asset"))
            intervention_type = clean_text(data.get("intervention_type"))
            intervention_name = clean_text(data.get("intervention_name"))

            if not theme or not subtheme or not intervention_name:
                continue

            key = (theme, subtheme, vulnerable_asset, intervention_type, intervention_name)
            if skip_existing and key in existing_keys:
                skipped += 1
                continue

            record = MitigationInterventionMaster(
                theme=theme,
                subtheme=subtheme,
                vulnerable_asset=vulnerable_asset,
                intervention_type=intervention_type,
                intervention_name=intervention_name,
                display_note=clean_text(data.get("display_note")),
                unit=clean_text(data.get("unit")),
                default_quantity=clean_decimal(data.get("default_quantity")),
                unit_cost_rs=clean_decimal(data.get("unit_cost_rs")),
                status="active",
            )
            records.append(record)

        if not records:
            self.stdout.write(self.style.WARNING("No records to import."))
            return

        with transaction.atomic():
            MitigationInterventionMaster.objects.bulk_create(records)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(records)} records. Skipped {skipped} existing."
            )
        )
