import os
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from mitigation.models import MitigationInterventionMaster
from vdmp_progress.models import BridgeType, ElectricType, RoadType, house_type


DEFAULT_PATH = (
    r"E:\\Siraj\\assam_crv\\file\\For mitigation intervention page typology and cost.xlsx"
)

ASCII_MAP = {
    ord("\u2013"): "-",
    ord("\u2014"): "-",
    ord("\u2018"): "'",
    ord("\u2019"): "'",
    ord("\u201c"): '"',
    ord("\u201d"): '"',
}


def to_ascii(value):
    if value is None:
        return None
    text = str(value).translate(ASCII_MAP)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = " ".join(text.split())
    return text or None


def clean_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return to_ascii(text) if text else None


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


def parse_housing_intervention_types(xl):
    sheet = xl.parse("Housing Interventions", header=None)
    header_row = None
    for idx, row in sheet.iterrows():
        if row.astype(str).str.contains("Housing Intervention type", case=False, na=False).any():
            header_row = idx
            break
    if header_row is None:
        raise CommandError("Housing Interventions header not found.")

    sheet.columns = sheet.iloc[header_row]
    data = sheet.iloc[header_row + 1 :].reset_index(drop=True)
    data = data.rename(columns=lambda x: str(x).strip())

    columns = [c for c in data.columns if "Housing Intervention type" in str(c)]
    types = []
    for col in columns:
        for value in data[col].tolist():
            text = clean_text(value)
            if text and text not in types:
                types.append(text)
    return types


def normalize_housing_typology(value):
    if not value:
        return None
    text = clean_text(value)
    if not text:
        return None
    if text[0].isdigit():
        text = f"R{text}"
    return text


def parse_housing_typologies(xl):
    sheet = xl.parse("Housing_Typology")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    column = next(
        (col for col in sheet.columns if "Housing Typology" in str(col)), None
    )
    if not column:
        return []
    types = []
    for value in sheet[column].tolist():
        text = normalize_housing_typology(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_housing_mitigations(xl):
    sheet = xl.parse("Housing mitigation")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    required = [
        "Housing mitigation Intervention",
        "Description",
        "Unit",
        "Unit Area",
        "Unit Rate (INR)",
    ]
    sheet = sheet[[c for c in required if c in sheet.columns]]

    rows = []
    for _, row in sheet.iterrows():
        name = clean_text(row.get("Housing mitigation Intervention"))
        if not name:
            continue
        rows.append(
            {
                "intervention_name": name,
                "display_note": clean_text(row.get("Description")),
                "unit": clean_text(row.get("Unit")),
                "area": clean_decimal(row.get("Unit Area")),
                "unit_cost_rs": clean_decimal(row.get("Unit Rate (INR)")),
            }
        )
    return rows


def parse_road_typologies(xl):
    sheet = xl.parse("Road Typology", header=None)
    sheet = sheet.dropna(how="all")
    sheet.columns = sheet.iloc[0]
    data = sheet.iloc[1:]
    columns = [c for c in data.columns if "Typology" in str(c)]
    if not columns:
        return []
    raw = []
    for value in data[columns[0]].tolist():
        text = clean_text(value)
        if text:
            raw.append(text)
    types = []
    for item in raw:
        if "(" in item and ")" in item:
            typ = item[item.find("(") + 1 : item.rfind(")")].strip()
        else:
            typ = item
        typ = clean_text(typ)
        if typ and typ not in types:
            types.append(typ)
    return types


def parse_road_intervention_types(xl):
    sheet = xl.parse("Road Intervention")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    types = []
    for value in sheet.get("Intervention type", []).tolist():
        text = clean_text(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_road_mitigations(xl):
    sheet = xl.parse("Road Mitigation")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    required = ["Mitigation intervention", "Description", "Unit cost", "Unit (m)"]
    sheet = sheet[[c for c in required if c in sheet.columns]]

    rows = []
    for _, row in sheet.iterrows():
        name = clean_text(row.get("Mitigation intervention"))
        if not name:
            continue
        rows.append(
            {
                "intervention_name": name,
                "display_note": clean_text(row.get("Description")),
                "unit": clean_text(row.get("Unit (m)")),
                "area": Decimal("1"),
                "unit_cost_rs": clean_decimal(row.get("Unit cost")),
            }
        )
    return rows


def parse_bridge_typologies(xl):
    sheet = xl.parse("Bridge Typolgy")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    types = []
    for value in sheet.get("Bridge Typology", []).tolist():
        text = clean_text(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_bridge_intervention_types(xl):
    sheet = xl.parse("Bridge Intervention")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    types = []
    for value in sheet.get("Intervention type", []).tolist():
        text = clean_text(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_bridge_mitigations(xl):
    sheet = xl.parse("Bridge Mitigation")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    required = [
        "Mitigation intervention",
        "Description",
        "Unit cost (INR)",
        "Unit (m)",
    ]
    sheet = sheet[[c for c in required if c in sheet.columns]]

    rows = []
    for _, row in sheet.iterrows():
        name = clean_text(row.get("Mitigation intervention"))
        if not name:
            continue
        rows.append(
            {
                "intervention_name": name,
                "display_note": clean_text(row.get("Description")),
                "unit": clean_text(row.get("Unit (m)")),
                "area": Decimal("1"),
                "unit_cost_rs": clean_decimal(row.get("Unit cost (INR)")),
            }
        )
    return rows


def parse_power_typologies(xl):
    sheet = xl.parse("P Infra Typology")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    types = []
    for value in sheet.get("Power Infrastructure  Typology", []).tolist():
        text = clean_text(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_power_intervention_types(xl):
    sheet = xl.parse("P Infra Intervention")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    types = []
    for value in sheet.get("Intervention type", []).tolist():
        text = clean_text(value)
        if text and text not in types:
            types.append(text)
    return types


def parse_power_mitigations(xl):
    sheet = xl.parse("P Infra Mitigation")
    sheet = sheet.rename(columns=lambda x: str(x).strip())
    required = ["Mitigation intervention", "Description", "Unit cost (INR)", "Unit"]
    sheet = sheet[[c for c in required if c in sheet.columns]]

    rows = []
    for _, row in sheet.iterrows():
        name = clean_text(row.get("Mitigation intervention"))
        if not name:
            continue
        rows.append(
            {
                "intervention_name": name,
                "display_note": clean_text(row.get("Description")),
                "unit": clean_text(row.get("Unit")),
                "area": Decimal("1"),
                "unit_cost_rs": clean_decimal(row.get("Unit cost (INR)")),
            }
        )
    return rows


def build_rows(file_path):
    xl = pd.ExcelFile(file_path)

    housing_typologies = parse_housing_typologies(xl)
    housing_types = parse_housing_intervention_types(xl)
    housing_mitigations = parse_housing_mitigations(xl)

    road_types = parse_road_typologies(xl)
    road_intervention_types = parse_road_intervention_types(xl)
    road_mitigations = parse_road_mitigations(xl)

    bridge_types = parse_bridge_typologies(xl)
    bridge_intervention_types = parse_bridge_intervention_types(xl)
    bridge_mitigations = parse_bridge_mitigations(xl)

    power_types = parse_power_typologies(xl)
    power_intervention_types = parse_power_intervention_types(xl)
    power_mitigations = parse_power_mitigations(xl)

    rows = []

    for typology in housing_typologies:
        for mitigation in housing_mitigations:
            for intervention_type in housing_types:
                rows.append(
                    {
                        "theme": "Resilient Housing",
                        "subtheme": "Housing",
                        "housing_type_name": typology,
                        "road_type_name": None,
                        "bridge_type_name": None,
                        "electric_type_name": None,
                        "intervention_type": intervention_type,
                        "intervention_name": mitigation["intervention_name"],
                        "display_note": mitigation["display_note"],
                        "unit": mitigation["unit"],
                        "area": mitigation["area"],
                        "unit_cost_rs": mitigation["unit_cost_rs"],
                        "status": "active",
                    }
                )

    for road_type in road_types:
        for intervention_type in road_intervention_types:
            for mitigation in road_mitigations:
                rows.append(
                    {
                        "theme": "Resilient Infrastructure",
                        "subtheme": "Road",
                        "housing_type_name": None,
                        "road_type_name": road_type,
                        "bridge_type_name": None,
                        "electric_type_name": None,
                        "intervention_type": intervention_type,
                        "intervention_name": mitigation["intervention_name"],
                        "display_note": mitigation["display_note"],
                        "unit": mitigation["unit"],
                        "area": mitigation["area"],
                        "unit_cost_rs": mitigation["unit_cost_rs"],
                        "status": "active",
                    }
                )

    for bridge_type in bridge_types:
        for intervention_type in bridge_intervention_types:
            for mitigation in bridge_mitigations:
                rows.append(
                    {
                        "theme": "Resilient Infrastructure",
                        "subtheme": "Bridge",
                        "housing_type_name": None,
                        "road_type_name": None,
                        "bridge_type_name": bridge_type,
                        "electric_type_name": None,
                        "intervention_type": intervention_type,
                        "intervention_name": mitigation["intervention_name"],
                        "display_note": mitigation["display_note"],
                        "unit": mitigation["unit"],
                        "area": mitigation["area"],
                        "unit_cost_rs": mitigation["unit_cost_rs"],
                        "status": "active",
                    }
                )

    for power_type in power_types:
        for intervention_type in power_intervention_types:
            for mitigation in power_mitigations:
                rows.append(
                    {
                        "theme": "Resilient Infrastructure",
                        "subtheme": "Electric infrastructure",
                        "housing_type_name": None,
                        "road_type_name": None,
                        "bridge_type_name": None,
                        "electric_type_name": power_type,
                        "intervention_type": intervention_type,
                        "intervention_name": mitigation["intervention_name"],
                        "display_note": mitigation["display_note"],
                        "unit": mitigation["unit"],
                        "area": mitigation["area"],
                        "unit_cost_rs": mitigation["unit_cost_rs"],
                        "status": "active",
                    }
                )

    unique_rows = []
    seen = set()
    for row in rows:
        vulnerable_asset = (
            row.get("housing_type_name")
            or row.get("road_type_name")
            or row.get("bridge_type_name")
            or row.get("electric_type_name")
            or ""
        )
        key = (
            row["theme"],
            row["subtheme"],
            vulnerable_asset,
            row["intervention_type"] or "",
            row["intervention_name"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)

    return unique_rows


class Command(BaseCommand):
    help = "Sync mitigation intervention master data from the typology/cost XLSX."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=DEFAULT_PATH,
            help="Excel file path (default: mitigation typology and cost file).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show counts without writing to the database.",
        )
        parser.add_argument(
            "--keep-missing-active",
            action="store_true",
            help="Do not inactivate rows missing from the XLSX.",
        )
        parser.add_argument(
            "--report",
            action="store_true",
            help="Print detailed create/update/deactivate lists.",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options["dry_run"]
        keep_missing_active = options["keep_missing_active"]
        report = options["report"]

        if not os.path.exists(file_path):
            raise CommandError(f"Excel file not found: {file_path}")

        try:
            rows = build_rows(file_path)
        except Exception as exc:
            raise CommandError(f"Failed to read Excel: {exc}") from exc

        if not rows:
            self.stdout.write(self.style.WARNING("No rows found in XLSX."))
            return

        existing = MitigationInterventionMaster.objects.filter(
            theme__in=["Resilient Housing", "Resilient Infrastructure"],
            subtheme__in=["Housing", "Road", "Bridge", "Electric infrastructure"],
        ).values(
            "id",
            "theme",
            "subtheme",
            "housing_type_id",
            "road_type_id",
            "bridge_type_id",
            "electric_type_id",
            "housing_type__house_type",
            "road_type__name",
            "bridge_type__name",
            "electric_type__name",
            "intervention_type",
            "intervention_name",
            "display_note",
            "unit",
            "area",
            "unit_cost_rs",
            "status",
        )

        existing_map = {}
        for record in existing:
            vulnerable_asset = (
                record.get("housing_type__house_type")
                or record.get("road_type__name")
                or record.get("bridge_type__name")
                or record.get("electric_type__name")
                or ""
            )
            key = (
                record["theme"],
                record["subtheme"],
                vulnerable_asset,
                record["intervention_type"] or "",
                record["intervention_name"],
            )
            existing_map[key] = record

        housing_type_map = {
            item.house_type: item
            for item in house_type.objects.all()
        }
        road_type_map = {item.name: item for item in RoadType.objects.all()}
        bridge_type_map = {item.name: item for item in BridgeType.objects.all()}
        electric_type_map = {
            item.name: item for item in ElectricType.objects.all()
        }

        def get_or_create_house_type(name):
            obj = housing_type_map.get(name)
            if obj:
                return obj
            obj, _ = house_type.objects.get_or_create(
                house_type=name,
                defaults={"per_unit_cost": Decimal("0.00")},
            )
            housing_type_map[name] = obj
            return obj

        def get_or_create_type(type_map, model, name):
            obj = type_map.get(name)
            if obj:
                return obj
            obj, _ = model.objects.get_or_create(
                name=name, defaults={"status": "active"}
            )
            type_map[name] = obj
            return obj

        to_create = []
        to_update = []
        to_create_keys = []
        to_update_details = []
        incoming_keys = set()

        for row in rows:
            vulnerable_asset = (
                row.get("housing_type_name")
                or row.get("road_type_name")
                or row.get("bridge_type_name")
                or row.get("electric_type_name")
                or ""
            )
            housing_type_obj = (
                get_or_create_house_type(row["housing_type_name"])
                if row.get("housing_type_name")
                else None
            )
            road_type_obj = (
                get_or_create_type(road_type_map, RoadType, row["road_type_name"])
                if row.get("road_type_name")
                else None
            )
            bridge_type_obj = (
                get_or_create_type(
                    bridge_type_map, BridgeType, row["bridge_type_name"]
                )
                if row.get("bridge_type_name")
                else None
            )
            electric_type_obj = (
                get_or_create_type(
                    electric_type_map, ElectricType, row["electric_type_name"]
                )
                if row.get("electric_type_name")
                else None
            )
            row_data = {
                "theme": row["theme"],
                "subtheme": row["subtheme"],
                "housing_type": housing_type_obj,
                "road_type": road_type_obj,
                "bridge_type": bridge_type_obj,
                "electric_type": electric_type_obj,
                "intervention_type": row["intervention_type"],
                "intervention_name": row["intervention_name"],
                "display_note": row["display_note"],
                "unit": row["unit"],
                "area": row["area"],
                "unit_cost_rs": row["unit_cost_rs"],
                "status": row["status"],
            }
            key = (
                row["theme"],
                row["subtheme"],
                vulnerable_asset,
                row["intervention_type"] or "",
                row["intervention_name"],
            )
            incoming_keys.add(key)
            existing_record = existing_map.get(key)
            if not existing_record:
                to_create.append(MitigationInterventionMaster(**row_data))
                to_create_keys.append(key)
                continue

            updates = {}
            if existing_record.get("housing_type_id") != (
                housing_type_obj.house_type_id if housing_type_obj else None
            ):
                updates["housing_type_id"] = (
                    housing_type_obj.house_type_id if housing_type_obj else None
                )
            if existing_record.get("road_type_id") != (
                road_type_obj.id if road_type_obj else None
            ):
                updates["road_type_id"] = road_type_obj.id if road_type_obj else None
            if existing_record.get("bridge_type_id") != (
                bridge_type_obj.id if bridge_type_obj else None
            ):
                updates["bridge_type_id"] = (
                    bridge_type_obj.id if bridge_type_obj else None
                )
            if existing_record.get("electric_type_id") != (
                electric_type_obj.id if electric_type_obj else None
            ):
                updates["electric_type_id"] = (
                    electric_type_obj.id if electric_type_obj else None
                )
            for field in [
                "display_note",
                "unit",
                "area",
                "unit_cost_rs",
                "status",
            ]:
                if existing_record.get(field) != row_data.get(field):
                    updates[field] = row_data.get(field)

            if updates:
                updates["id"] = existing_record["id"]
                to_update.append(updates)
                to_update_details.append(
                    {
                        "key": key,
                        "changes": updates.copy(),
                    }
                )

        to_deactivate = []
        to_deactivate_details = []
        if not keep_missing_active:
            for key, record in existing_map.items():
                if key not in incoming_keys and record.get("status") != "inactive":
                    to_deactivate.append(record["id"])
                    to_deactivate_details.append(
                        {
                            "key": key,
                            "id": record["id"],
                        }
                    )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Dry run: "
                    f"create={len(to_create)} update={len(to_update)} "
                    f"deactivate={len(to_deactivate)}"
                )
            )
            if report:
                self._print_report(
                    to_create_keys, to_update_details, to_deactivate_details
                )
            return

        def reset_sequence():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT setval(
                        pg_get_serial_sequence(
                            'mitigation_mitigationinterventionmaster',
                            'id'
                        ),
                        COALESCE(
                            (SELECT MAX(id) FROM mitigation_mitigationinterventionmaster),
                            1
                        ),
                        true
                    )
                    """
                )

        with transaction.atomic():
            if to_create:
                reset_sequence()
            if to_create:
                MitigationInterventionMaster.objects.bulk_create(to_create)
            for update in to_update:
                record_id = update.pop("id")
                MitigationInterventionMaster.objects.filter(id=record_id).update(
                    **update
                )
            if to_deactivate:
                MitigationInterventionMaster.objects.filter(id__in=to_deactivate).update(
                    status="inactive"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced: created={len(to_create)} updated={len(to_update)} "
                f"deactivated={len(to_deactivate)}"
            )
        )
        if report:
            self._print_report(
                to_create_keys, to_update_details, to_deactivate_details
            )

    def _print_report(self, created, updated, deactivated):
        if created:
            self.stdout.write(self.style.WARNING("Created entries:"))
            for key in created:
                self.stdout.write(self._format_key(key))
        if updated:
            self.stdout.write(self.style.WARNING("Updated entries:"))
            for item in updated:
                key = item.get("key")
                changes = item.get("changes", {})
                changes.pop("id", None)
                self.stdout.write(
                    f"{self._format_key(key)} changes={changes}"
                )
        if deactivated:
            self.stdout.write(self.style.WARNING("Deactivated entries:"))
            for item in deactivated:
                key = item.get("key")
                self.stdout.write(self._format_key(key))

    def _format_key(self, key):
        theme, subtheme, vulnerable_asset, intervention_type, intervention_name = key
        return (
            f"{theme} | {subtheme} | "
            f"{vulnerable_asset or '-'} | {intervention_type or '-'} | "
            f"{intervention_name}"
        )
