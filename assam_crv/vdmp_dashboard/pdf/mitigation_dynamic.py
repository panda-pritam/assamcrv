from decimal import Decimal, InvalidOperation

from reportlab.platypus import Paragraph

from mitigation.models import MitigationPlanItem
from vdmp_dashboard.models import VillageRoadInfo, VillageRoadInfoErosion
from django.db.models import Sum

from .global_styles import bold_12, bold_center_style_9, normal_style


def _safe_decimal(value):
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _format_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if abs(number - round(number)) < 0.000001:
        return f"{int(round(number)):,}"
    return f"{number:,.2f}"


def _format_money(value):
    formatted = _format_number(value)
    return "-" if formatted == "-" else f"INR {formatted}"


def _normalize_text(value):
    if not value:
        return ""
    return str(value).strip().lower()


def _master_text(master):
    if not master:
        return ""
    parts = [
        master.theme,
        master.subtheme,
        master.intervention_name,
        master.intervention_type,
    ]
    return " ".join(part for part in parts if part)


def _matches_keywords(master, keywords):
    text = _normalize_text(_master_text(master))
    return any(keyword in text for keyword in keywords)


def _estimate_cost(item):
    if item.estimated_cost_rs is not None:
        return _safe_decimal(item.estimated_cost_rs)
    return _safe_decimal(item.unit_cost_rs) * _safe_decimal(item.quantity)


def _get_items(village_id):
    if not village_id:
        return []
    return list(
        MitigationPlanItem.objects.select_related("master").filter(
            village_id=village_id, status="draft"
        )
    )


def _find_typology(item):
    if item.typology:
        return item.typology
    master = item.master
    for attr in ("housing_type", "road_type", "bridge_type", "electric_type"):
        related = getattr(master, attr, None)
        if related:
            return getattr(related, "house_type", None) or getattr(related, "name", None) or "-"
    return "-"


def _intervention_name(item):
    master = item.master
    return master.intervention_name if master and master.intervention_name else "-"


def _remarks_text(item):
    if item.remarks:
        return item.remarks
    master = item.master
    if master and master.display_note:
        return master.display_note
    return "-"


def _unit_cost_value(item):
    if item.unit_cost_rs is not None:
        return item.unit_cost_rs
    master = item.master
    return master.unit_cost_rs if master else None


def _build_placeholder_row(column_count):
    return ["-"] * column_count


def getMitigationIntervention(village_id):
    items = _get_items(village_id)
    if not items:
        return [
            ["Multi hazard mitigation intervention (estimated budget in INR)"],
            ["Resilient housing", "-"],
            ["Resilient road", "-"],
            ["Resilient bridge", "-"],
            ["River bank protection", "-"],
            ["Sluice gate", "-"],
            [Paragraph("Resilient essential service (educational facilities)", bold_12), "-"],
            [
                Paragraph(
                    "Resilient essential service (public WASH facilities and drinking water)",
                    bold_12,
                ),
                "-",
            ],
            [
                Paragraph(
                    "Resilient essential services (electric infrastructure)", bold_12
                ),
                "-",
            ],
            [Paragraph("Resilient livelihood & economic security ", bold_12), "-"],
        ]

    category_order = [
        ("housing", ["housing", "house"]),
        ("road", ["road"]),
        ("bridge", ["bridge"]),
        ("river", ["river", "bank", "embankment", "erosion"]),
        ("sluice", ["sluice"]),
        ("education", ["education", "educational", "school", "anganwadi"]),
        ("wash", ["wash", "sanitation", "drinking water", "water supply"]),
        ("electric", ["electric", "power", "transformer"]),
        ("livelihood", ["livelihood", "economic", "agriculture", "agri", "crop", "livestock"]),
    ]

    totals = {key: Decimal("0") for key, _ in category_order}
    for item in items:
        master = item.master
        for key, keywords in category_order:
            if _matches_keywords(master, keywords):
                totals[key] += _estimate_cost(item)
                break

    def total_or_dash(key):
        amount = totals.get(key, Decimal("0"))
        return "-" if amount <= 0 else _format_money(amount)

    return [
        ["Multi hazard mitigation intervention (estimated budget in INR)"],
        ["Resilient housing", total_or_dash("housing")],
        ["Resilient road", total_or_dash("road")],
        ["Resilient bridge", total_or_dash("bridge")],
        ["River bank protection", total_or_dash("river")],
        ["Sluice gate", total_or_dash("sluice")],
        [Paragraph("Resilient essential service (educational facilities)", bold_12), total_or_dash("education")],
        [
            Paragraph(
                "Resilient essential service (public WASH facilities and drinking water)",
                bold_12,
            ),
            total_or_dash("wash"),
        ],
        [Paragraph("Resilient essential services (electric infrastructure)", bold_12), total_or_dash("electric")],
        [Paragraph("Resilient livelihood & economic security ", bold_12), total_or_dash("livelihood")],
    ]


def getResilientHousingCostTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Housing typology", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Number", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["housing", "house"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
            ]
        )
    return data


def getRoadInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Road type", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Department", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["road"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                "-",
            ]
        )
    return data


def getRoadTypologyTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Road type", bold_center_style_9),
        Paragraph("Total length (km)", bold_center_style_9),
        Paragraph("Severe+high flood vulnerable length (km)", bold_center_style_9),
        Paragraph("Severe+high erosion vulnerable length (km)", bold_center_style_9),
    ]
    data = [headers]
    if not village_id:
        data.append(_build_placeholder_row(len(headers)))
        return data

    flood_qs = VillageRoadInfo.objects.filter(village_id=village_id).exclude(
        road_surface_type__istartswith="WRD"
    )
    erosion_qs = VillageRoadInfoErosion.objects.filter(
        village_id=village_id
    ).exclude(road_surface_type__istartswith="WRD")

    total_map = {
        row["road_surface_type"]: float(row["total_length"] or 0)
        for row in flood_qs.values("road_surface_type").annotate(
            total_length=Sum("road_length_m")
        )
    }
    flood_map = {
        row["road_surface_type"]: float(row["total_length"] or 0)
        for row in flood_qs.filter(flood_depth_m__gte=0.5)
        .values("road_surface_type")
        .annotate(total_length=Sum("road_length_m"))
    }
    erosion_map = {
        row["road_surface_type"]: float(row["total_length"] or 0)
        for row in erosion_qs.filter(
            erosion_class__in=["high", "severe", "High", "Severe"]
        )
        .values("road_surface_type")
        .annotate(total_length=Sum("road_length_m"))
    }

    road_types = sorted(set(total_map) | set(flood_map) | set(erosion_map))
    if not road_types:
        data.append(_build_placeholder_row(len(headers)))
        return data

    def format_km(value):
        if not value:
            return "-"
        return f"{value / 1000:.2f}"

    for index, road_type in enumerate(road_types, 1):
        data.append(
            [
                str(index),
                Paragraph(str(road_type or "-"), normal_style),
                format_km(total_map.get(road_type, 0)),
                format_km(flood_map.get(road_type, 0)),
                format_km(erosion_map.get(road_type, 0)),
            ]
        )
    return data


def getRiverBankInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("River bank", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Department", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["river", "bank", "embankment", "erosion"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                "-",
            ]
        )
    return data


def getEducationalInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Name of asset", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Remarks", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["education", "educational", "school", "anganwadi"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                Paragraph(str(_remarks_text(item)), normal_style),
            ]
        )
    return data


def getWASHInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Name of asset", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Remarks", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["wash", "sanitation", "drinking water", "water supply"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                Paragraph(str(_remarks_text(item)), normal_style),
            ]
        )
    return data


def getElectricInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Name of asset", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Remarks", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["electric", "power", "transformer"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                Paragraph(str(_remarks_text(item)), normal_style),
            ]
        )
    return data


def getLivelihoodInterventionTable(village_id):
    headers = [
        Paragraph("S.No.", bold_center_style_9),
        Paragraph("Name of asset", bold_center_style_9),
        Paragraph("Intervention", bold_center_style_9),
        Paragraph("Quantity", bold_center_style_9),
        Paragraph("Unit cost in INR", bold_center_style_9),
        Paragraph("Total cost in INR", bold_center_style_9),
        Paragraph("Remarks", bold_center_style_9),
    ]
    data = [headers]

    items = [
        item
        for item in _get_items(village_id)
        if _matches_keywords(item.master, ["livelihood", "economic", "agriculture", "agri", "crop", "livestock"])
    ]

    if not items:
        data.append(_build_placeholder_row(len(headers)))
        return data

    for index, item in enumerate(items, 1):
        data.append(
            [
                str(index),
                Paragraph(str(_find_typology(item)), normal_style),
                Paragraph(str(_intervention_name(item)), normal_style),
                _format_number(item.quantity),
                _format_money(_unit_cost_value(item)),
                _format_money(_estimate_cost(item)),
                Paragraph(str(_remarks_text(item)), normal_style),
            ]
        )
    return data
