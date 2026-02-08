from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from village_profile.models import tblVillage
from datetime import datetime

from vdmp_dashboard.models import HouseholdSurvey, Critical_Facility, Risk_Assesment,VillageRoadInfo,VillageRoadInfoErosion, VillageRoadInfoEQ, VillageRoadInfoWind, villageAgricultureLandWindInfo,villageAgricultureLandEQInfo,villageAgricultureLandFloodInfo
from vdmp_progress.models import Risk_Assessment_Result
from collections import Counter
from administrator.models import PRA_main

from .village_profile import getVillageArea, getLULCData
from django.db.models import Count,Sum,  IntegerField, FloatField

from django.db.models.functions import Cast, Coalesce
from administrator.models import LineDepartment
from django.db.models import Q, Sum, FloatField, IntegerField
from django.db.models.functions import Cast, Coalesce, Trim, NullIf, Lower
from django.core.exceptions import FieldDoesNotExist




from .dummy_data import  getMitigationIntervention

from .global_styles import blue_heading, underline_heading, notes_style, bold_center_style,normal_style,bold_12,bold_12,blue_sub_heading

from .utils.table import create_styled_table

# Global dictionary for village summary data
VILLAGE_SUMMARY_DATA = {
    'total_population': 0,
    'total_households': 0,
    'dominant_house_type': 'N/A',
    'major_land_use': 'N/A',
    'occupational_category': 'N/A',
    'sanitation_facilities': 'N/A'
}


def safe_int_sum(field_name):
    """
    Safely converts:
    '1'   → 1
    '1.0' → 1
    '0.0' → 0
    ''    → 0
    NULL  → 0
    """
    return Coalesce(
        Sum(
            Cast(
                Cast(
                    NullIf(Trim(field_name), ''),
                    FloatField()
                ),
                IntegerField()
            )
        ),
        0
    )




def mode_value(field):
    # 🚫 empty / invalid field protection
    if not field or not isinstance(field, str) or not field.strip():
        return "N/A"

    # 🚫 ensure field exists in model
    try:
        HouseholdSurvey._meta.get_field(field)
    except FieldDoesNotExist:
        print(f"⚠️ Invalid field passed to mode_value: '{field}'")
        return "N/A"

    row = (
        qs.exclude(**{f"{field}__isnull": True})
          .exclude(**{f"{field}__exact": ""})
          .values(field)
          .annotate(cnt=Count(field))
          .order_by("-cnt")
          .first()
    )
    return row[field] if row else "N/A"


def getEmergencyTollFreeContactData(village_id):
    try:
        emergency_officials = LineDepartment.objects.filter(
            village_id=village_id,
            official_number__iexact='no'
        ).select_related('section_master')
        
        data = [["S. No.", "Important Contact", "Contact Number"]]

        if not emergency_officials.exists():
            # ✅ one blank row
            data.append(["-", "-", "-"])
            return data
        
        for i, official in enumerate(emergency_officials, 1):
            data.append([
                str(i),
                official.section_master.section or "-",
                official.phone_number or "-"
            ])
        
    
            
        return data
        
    except Exception as e:
        return [
            ["S. No.", "Important Contact", "Contact Number"],
            ["1", "Police Station", "100"],
            ["2", "Fire Station", "102"],
            ["3", "Ambulance", "108"],
            ["4", Paragraph("District Commissioner (Emergency Toll-Free)"), Paragraph("<para align=center>1077 (District), 1079 (State)</para>")],
            ["5", Paragraph("District Emergency Operation Centre, Barpeta"), "9864643089"]
        ]

def getHazardAssessment(village_id):
    from administrator.models import PRA_main
    
    try:
        pra_data = PRA_main.objects.filter(village_id=village_id).first()
        
        if pra_data:
            return [
                ['Hazard Assessment'],
                ["", Paragraph("Frequency", bold_center_style), Paragraph("Severity", bold_center_style)],
                ['Flood hazard', f"{pra_data.flood_frequency or '-'}", f"{pra_data.flood_severity or '-'}"],
                ['Erosion hazard', f"{pra_data.erosion_hazard_frequency or '-'} ", f"{pra_data.erosion_hazard_severity or '-'}"],
                ['Strong Wind hazard', f"{pra_data.strong_wind_hazard_frequency or '-'} ", f"{pra_data.strong_wind_hazard_severity or '-'}"],
                ['Earthquake hazard', f"{pra_data.earthquake_hazard_frequency or '-'}", f"{pra_data.earthquake_hazard_severity or '-'}"]
            ]
        else:
            return [
                ['Hazard Assessment'],
                 ["", Paragraph("Frequency", bold_center_style), Paragraph("Severity", bold_center_style)],
                ['Flood hazard', '-','-'],
                ['Erosion hazard', '-','-'],
                ['Strong Wind hazard', '-','-'],
                ['Earthquake hazard', '-','-']
            ]
    except Exception:
        return [
            ['Hazard Assessment'],
            ['Flood hazard', '-'],
            ['Erosion hazard', '-'],
            ['Strong Wind hazard', '-'],
            ['Earthquake hazard', '-']
        ]

def getDistrictLevelOfficialsData(village_id):
    try:
        officials = LineDepartment.objects.filter(
            village_id=village_id,
            official_number__iexact='yes'
        ).select_related('section_master')
        
        data = [["S. No.", "Name", "Phone Number", "Position/Responsibility"]]

        if not officials.exists():
            # ✅ one blank row
            data.append(["-", "-", "-", "-"])
            return data
        
        for i, official in enumerate(officials, 1):
            data.append([
                str(i),
                official.contact_name or "-",
                official.phone_number or "-",
                official.section_master.section if official.section_master else "-"
            ])
            
        return data
        
    except Exception:
        return [
            ["S. No.", "Name", "Phone Number", "Position/Responsibility"],
            ["-", "-", "-", "-"]
        ]



def get_village_area(village_id):
    """Get village area from village_boundary table"""
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return 0
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT area_sqkm
                FROM public.village_boundary
                WHERE Vill_ID = %s
            """, [village_code])
            
            row = cursor.fetchone()
            if row and row[0]:
                return float(row[0])
            else:
                return 0
    except Exception:
        return 0

# Get village related data from the database
def generate_general_summary_table(village_id=None):
   
    if village_id:
        # Optimized query with select_related to avoid N+1 queries
        village = tblVillage.objects.select_related(
            'gram_panchayat',
            'gram_panchayat__circle', 
            'gram_panchayat__circle__district'
        ).get(id=village_id)
        
        # Get village area from database
        village_area = get_village_area(village_id)
        area_text = f"{village_area:.2f} sq km" if village_area > 0 else "N/A"
        
        # Get major land use
        lulc_data = getLULCData(village_id, 'assam', 'lulc', True)
        major_land_use = lulc_data if lulc_data else "N/A"
        print(major_land_use)
        VILLAGE_SUMMARY_DATA['major_land_use'] = major_land_use
        
        return [
            ['General Summary'],
            ['Date of baseline data collection', datetime.now().strftime('%B %Y')],
            ['Village', village.name],
            ['Geographic area', area_text],
            ['Block', village.gram_panchayat.name],
            ['Revenue circle', village.gram_panchayat.circle.name],
            ['District', village.gram_panchayat.circle.district.name]
            
        ]
    else:
        return [
            ['General Summary'],
            ['Date of baseline data collection', datetime.now().strftime('%B %Y')],
            ['Village', 'N/A'],
            ['Geographic area', 'N/A'],
            ['Block', 'N/A'],
            ['Revenue circle', 'N/A'],
            ['District', 'N/A'],
            # ['Major Land Use', 'N/A']
        ] 
        
    
    
from django.db.models.functions import Lower, Trim

def to_int(val):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def get_major_land_use(village_id):
    """Get major land use from lulc table"""
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return "Information not available"
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "Class_name", SUM("Area_SqM") as total_area
                FROM public.lulc
                WHERE "Vill_ID" = %s
                GROUP BY "Class_name"
                ORDER BY total_area DESC
                LIMIT 1
            """, [village_code])
            
            row = cursor.fetchone()
            if row:
                class_name = row[0]
                max_area = row[1]
                
                # Get total area for percentage calculation
                cursor.execute("""
                    SELECT SUM("Area_SqM") as total
                    FROM public.lulc
                    WHERE "Vill_ID" = %s
                """, [village_code])
                
                total_area = cursor.fetchone()[0]
                if total_area and total_area > 0:
                    percentage = round((max_area / total_area) * 100, 2)
                    return f"{class_name} {percentage}% of the total area"
                else:
                    return class_name
            else:
                return "Information not available"
    except Exception:
        return "Information not available"

def generate_socio_economic_summary_table(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        # =========================
        # TOTAL POPULATION
        # =========================
        total_population = sum(
            to_int(h.number_of_males_including_children) +
            to_int(h.number_of_females_including_children)
            for h in households
        )

        total_households_count = households.count()
        
        # Get major land use from database
        major_land_use = get_major_land_use(village_id)

        # =========================
        # NORMALIZE TEXT FIELDS
        # =========================
        households_n = households.annotate(
            house_type_n=Lower(Trim('house_type')),
            toilet_class_n=Lower(Trim('toilet_class')),
            sanitation_type_n=Lower(Trim('sanitation_facility')),
            livelihood_n=Lower(Trim('livelihood_primary')),
        )

        # =========================
        # SANITATION (OWN TOILETS)
        # =========================
        own_households = households_n.filter(sanitation_type_n='own')
        own_total = own_households.count()

        if own_total > 0:
            pucca_toilet = own_households.filter(toilet_class_n='pucca').count()
            semi_pucca_toilet = own_households.filter(toilet_class_n='semi pucca').count()
            kachcha_toilet = own_households.filter(toilet_class_n='kachcha').count()

            toilet_counts = {
                'Pucca': pucca_toilet,
                'Semi Pucca': semi_pucca_toilet,
                'Kachcha': kachcha_toilet
            }

            max_toilet_type = max(toilet_counts, key=toilet_counts.get)
            max_percentage = round((toilet_counts[max_toilet_type] / own_total) * 100)

            sanitation_text = (
                f"Predominantly {max_toilet_type.lower()} toilets "
                f"({max_percentage}% of households with own sanitation facilities)"
            )
        else:
            sanitation_text = (
                "Households reported limited access to individual sanitation facilities"
            )

        # =========================
        # HOUSE TYPE
        # =========================
        kachcha = households_n.filter(house_type_n='kachcha').count()
        semi_pucca = households_n.filter(house_type_n='semi pucca').count()
        pucca = households_n.filter(house_type_n='pucca').count()

        house_counts = {
            'Kachcha': kachcha,
            'Semi Pucca': semi_pucca,
            'Pucca': pucca
        }

        if total_households_count > 0:
            max_house_type = max(house_counts, key=house_counts.get)
            max_percentage = round(
                (house_counts[max_house_type] / total_households_count) * 100, 1
            )

            dominant_house_type = (
                f"Majority of households reside in {max_house_type.lower()} houses "
                f"({max_percentage}%)"
            )
        else:
            dominant_house_type = "Housing information not available"

        # =========================
        # OCCUPATION
        # =========================
        livelihood_qs = (
            households_n
            .exclude(livelihood_n__isnull=True)
            .exclude(livelihood_n='')
            .values('livelihood_n')
            .annotate(count=Count('livelihood_n'))
            .order_by('-count')
        )

        if livelihood_qs.exists() and total_households_count > 0:
            top_livelihood = livelihood_qs[0]['livelihood_n'].title()
            top_count = livelihood_qs[0]['count']
            percentage = round((top_count / total_households_count) * 100)

            occupational_category = (
                f"{percentage}% of households primarily depend on {top_livelihood.lower()}"
            )
        else:
            occupational_category = (
                "Occupational details were not sufficiently reported"
            )

        # =========================
        # UPDATE GLOBAL SUMMARY
        # =========================
        VILLAGE_SUMMARY_DATA['total_population'] = total_population
        VILLAGE_SUMMARY_DATA['total_households'] = total_households_count
        VILLAGE_SUMMARY_DATA['dominant_house_type'] = dominant_house_type
        VILLAGE_SUMMARY_DATA['sanitation_facilities'] = sanitation_text
        VILLAGE_SUMMARY_DATA['occupational_category'] = occupational_category
        VILLAGE_SUMMARY_DATA['major_land_use'] = major_land_use

        # =========================
        # FINAL TABLE (REPORTLAB SAFE)
        # =========================
        return [
            ['Socio-Economic Summary'],
            ['Total population', f"{total_population} persons (as reported)"],
            ['Total households', f"{total_households_count} households surveyed"],
            ['Dominant house type', dominant_house_type],
            ['Major landuse', major_land_use],
            ['Occupational category', occupational_category],
            ['Sanitation facilities', Paragraph(sanitation_text, normal_style)],
        ]

    except Exception as e:
        print("❌ Socio-economic summary error:", e)

        # SAFE FALLBACK TABLE (never breaks PDF)
        return [
            ['Socio-Economic Summary'],
            ['Total population', 'N/A'],
            ['Total households', 'N/A'],
            ['Dominant house type', 'N/A'],
            ['Major landuse', 'N/A'],
            ['Occupational category', 'N/A'],
            ['Sanitation facilities', Paragraph("N/A", normal_style)],
        ]





def getRiskAssessment(village_id):
    
    # Get risk assessment data for the village
    risk_data = Risk_Assessment_Result.objects.filter(village_id=village_id)
    
    if not risk_data.exists():
        return [
            ['Risk Assessment (excluding content loss)'],
            ['Sector', Paragraph('Flood'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
            [Paragraph('Potential average loss (residential)', bold_12), 'No data', 'No data', 'No data'],
            [Paragraph('Potential average loss (commercial)', bold_12), 'No data', 'No data', 'No data'],
            [Paragraph('Potential average loss (critical facilities – Health facilities, educational facilities, flood shelter)', bold_12), 'No data', 'No data', 'No data'],
            [Paragraph('Potential average loss (road)',bold_12 ), '-', '-', '-'],
            [Paragraph('Potential average loss (agriculture) '  ,bold_12), '-', '-', '-'],
            
        ]
    
    # Calculate losses by asset type (convert to crores)
    household_flood = (risk_data.filter(asset_type='household').aggregate(Sum('flood_loss'))['flood_loss__sum'] or 0) / 10000000
    household_eq = (risk_data.filter(asset_type='household').aggregate(Sum('eq_loss'))['eq_loss__sum'] or 0) / 10000000
    household_wind = (risk_data.filter(asset_type='household').aggregate(Sum('wind_loss'))['wind_loss__sum'] or 0) / 10000000
    
    commercial_flood = (risk_data.filter(asset_type='commercial').aggregate(Sum('flood_loss'))['flood_loss__sum'] or 0) / 10000000
    commercial_eq = (risk_data.filter(asset_type='commercial').aggregate(Sum('eq_loss'))['eq_loss__sum'] or 0) / 10000000
    commercial_wind = (risk_data.filter(asset_type='commercial').aggregate(Sum('wind_loss'))['wind_loss__sum'] or 0) / 10000000
    
    critical_flood = (risk_data.filter(asset_type='critical_facility').aggregate(Sum('flood_loss'))['flood_loss__sum'] or 0) / 10000000
    critical_eq = (risk_data.filter(asset_type='critical_facility').aggregate(Sum('eq_loss'))['eq_loss__sum'] or 0) / 10000000
    critical_wind = (risk_data.filter(asset_type='critical_facility').aggregate(Sum('wind_loss'))['wind_loss__sum'] or 0) / 10000000

    # ---------- ROADS ----------
    road_risk_flood = (
        VillageRoadInfo.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('flood_loss'))['total'] or 0
    ) / 10000000

    road_risk_eq = (
        VillageRoadInfoEQ.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('eq_loss'))['total'] or 0
    ) / 10000000

    road_risk_wind = (
        VillageRoadInfoWind.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('wind_loss'))['total'] or 0
    ) / 10000000


    # ---------- AGRICULTURE ----------
    agriculture_flood = (
        villageAgricultureLandFloodInfo.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('flood_loss'))['total'] or 0
    ) / 10000000

    agriculture_eq = (
        villageAgricultureLandEQInfo.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('eq_loss'))['total'] or 0
    ) / 10000000

    agriculture_wind = (
        villageAgricultureLandWindInfo.objects
        .filter(village_id=village_id)
        .aggregate(total=Sum('wind_loss'))['total'] or 0
    ) / 10000000

    
    return [
        ['Risk Assessment (excluding content loss)'],
        ['Sector', Paragraph('Flood'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
        [Paragraph('Potential average loss (residential)', bold_12), f'INR {household_flood:.2f} Crore', f'INR {household_eq:.2f} Crore', f'INR {household_wind:.2f} Crore'],
        [Paragraph('Potential average loss (commercial)',bold_12), f'INR {commercial_flood:.2f} Crore', f'INR {commercial_eq:.2f} Crore', f'INR {commercial_wind:.2f} Crore'],
        [Paragraph('Potential average loss (critical facilities – Health facilities, educational facilities, flood shelter)', bold_12), f'INR {critical_flood:.2f} Crore', f'INR {critical_eq:.2f} Crore', f'INR {critical_wind:.2f} Crore'],
        [Paragraph('Potential average loss (road)', bold_12), f'INR {road_risk_flood:.2f} Crore', '-', '-'],
        [Paragraph('Potential average loss (agriculture)',bold_12), f'INR {agriculture_flood:.2f} Crore', '-', '-'],
      
    ]


import requests
from django.db import connection

def get_eroding_river_bank(village_id):
    """
    Fetch eroding river bank length AND total river bank length (km)
    """
    print(f"\n🟡 [EROSION] Start get_eroding_river_bank | village_id={village_id}")

    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
        print(f"🟢 Village code found: {village_code}")
    except tblVillage.DoesNotExist:
        print("❌ Village not found")
        return "No data"

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "Length_km", "Class"
                FROM public.erosion_accretion
                WHERE "Vill_ID" = %s
            """, [village_code])

            rows = cursor.fetchall()
            print(f"🟢 Rows fetched from erosion_accretion: {len(rows)}")

            if not rows:
                print("⚠️ No erosion rows found")
                return "No river bank data"

            total_km = 0.0
            erosion_km = 0.0

            for idx, row in enumerate(rows, 1):
                raw_length = row[0]
                raw_class = row[1]

                print(f"   ▶ Row {idx}: Length={raw_length}, Class={raw_class}")

                try:
                    length_km = float(raw_length or 0)
                except (TypeError, ValueError):
                    print(f"     ❌ Invalid length value: {raw_length}")
                    continue

                cls = (raw_class or "").lower()
                total_km += length_km

                if cls in ("erosion", "errosion"):
                    erosion_km += length_km

            total_km = round(total_km, 2)
            erosion_km = round(erosion_km, 2)

            print(f"🟢 Total river bank: {total_km} km")
            print(f"🟢 Eroding river bank: {erosion_km} km")

            if total_km == 0:
                return "No river bank data"

            return f"{erosion_km} km out of {total_km} km"

    except Exception as e:
        # print("❌ Erosion query error:", e)
        return "No data"

            
from django.db.models import Sum, FloatField, IntegerField, F, Value
from django.db.models.functions import Cast, Coalesce, Trim, NullIf

def safe_sum_single(qs, field_name):
    # print(f"   🔹 Aggregating field: {field_name}")   

    try:
        result = qs.aggregate(
            total=Coalesce(
                Sum(
                    Cast(
                        Cast(
                            NullIf(
                                Trim(F(field_name)),   # ✅ field reference
                                Value('')              # ✅ EMPTY STRING AS VALUE
                            ),
                            FloatField()
                        ),
                        IntegerField()
                    )
                ),
                0
            )
        )['total']

        # print(f"      ✅ {field_name} = {result}")
        return result

    except Exception as e:
        print(f"      ❌ ERROR in {field_name}: {e}")
        return 0




def getVulnerabilityAssessment(village_id):
    print(f"\n🟡 [VULNERABILITY] Start | village_id={village_id}")

    try:
        from django.db.models import Q, Sum, FloatField, IntegerField
        from django.db.models.functions import Cast, Coalesce, Trim, NullIf

        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        print(f"🟢 Total households: {total_households}")

        if total_households == 0:
            print("⚠️ No household data")
            return [
                ["Vulnerability Assessment"],
                ['Economic status', 'No data'],
                ['Vulnerable population', 'No data'],
                ['Eroding river bank', 'No data'],
                ['Flood vulnerable Houses', 'No data'],
                ['Erosion vulnerable Houses', 'No data'],
                ['Flood vulnerable Road', 'No data'],
                ['Erosion vulnerable Road', 'No data'],
                ['School', 'No data'],
                ['Livelihood vulnerability Index', 'No data'],
            ]

        # -----------------------------
        # ECONOMIC STATUS
        # -----------------------------
        bpl_count = 0
        phh_count = 0

        for h in households:
            economic = (h.economic_status or "").lower()
            if economic == 'bpl' or 'below poverty line' in economic:
                bpl_count += 1
            elif economic == 'phh' or 'priority household' in economic:
                phh_count += 1

        # print(f"🟢 BPL count: {bpl_count}, PHH count: {phh_count}")

        economic_status = (
            f"BPL - {round((bpl_count / total_households) * 100)}%, "
            f"Priority Household - {round((phh_count / total_households) * 100)}%"
        )

        # -----------------------------
        # TOTAL POPULATION
        # -----------------------------
        total_population = sum(
            to_int(h.number_of_males_including_children) +
            to_int(h.number_of_females_including_children)
            for h in households
        )

        # print(f"🟢 Total population: {total_population}")

       
        disabled = safe_sum_single(
            households, 'persons_with_disability_or_chronic_disease'
        )

        lactating = safe_sum_single(
            households, 'lactating_women'
        )

        pregnant = safe_sum_single(
            households, 'pregnant_women'
        )

        seniors = safe_sum_single(
            households, 'senior_citizens'
        )

        children = safe_sum_single(
            households, 'children_below_6_years'
        )

        # print(f"🟢 ---------------- Vulnerable counts - Disabled: {disabled}, Lactating: {lactating}, Pregnant: {pregnant}, Seniors: {seniors}, Children: {children}")

        vulnerable_totals = {
            'disabled': disabled,
            'lactating': lactating,
            'pregnant': pregnant,
            'seniors': seniors,
            'children': children,
        }

        # print(f"🟢 Vulnerable raw totals: {vulnerable_totals}")

        vulnerable_count = sum(vulnerable_totals.values())

        if total_population > 0:
            vulnerable_percent = round((vulnerable_count / total_population) * 100)
            vulnerable_population = f"{vulnerable_count} ({vulnerable_percent}%)"
        else:
            vulnerable_population = "No data"

        print(f"🟢 Vulnerable population: {vulnerable_population}")


        # -----------------------------
        # HOUSE VULNERABILITY
        # -----------------------------
        total_households = households.count()
        print(f"🟢 Total households: {total_households}")

        # Flood vulnerable houses
        flood_vulnerable_houses = households.filter(
            flood_depth_m__gte=0.5
        ).count()

        flood_house_percent = (
            round((flood_vulnerable_houses / total_households) * 100, 1)
            if total_households > 0 else 0
        )

        # Erosion vulnerable houses
        erosion_vulnerable_houses = households.filter(
            house_vulnerable_to_erosion__iexact='yes'
        ).count()

        erosion_house_percent = (
            round((erosion_vulnerable_houses / total_households) * 100, 1)
            if total_households > 0 else 0
        )

        print(
            f"🟢 Flood vulnerable houses: "
            f"{flood_vulnerable_houses} ({flood_house_percent}%)"
        )
        print(
            f"🟢 Erosion vulnerable houses: "
            f"{erosion_vulnerable_houses} ({erosion_house_percent}%)"
        )


        # -----------------------------
        # ROAD VULNERABILITY
        # -----------------------------
        flood_road_length_m = VillageRoadInfo.objects.filter(
            village_id=village_id,
            flood_depth_m__gt=0.5
        ).aggregate(total=Sum('road_length_m'))['total'] or 0

        erosion_road_length_m = VillageRoadInfoErosion.objects.filter(
            village_id=village_id
        ).filter(
            Q(erosion_class__iexact='Severe') |
            Q(erosion_class__iexact='High')
        ).aggregate(total=Sum('road_length_m'))['total'] or 0

        print(f"🟢 Flood road length (m): {flood_road_length_m}")
        print(f"🟢 Erosion road length (m): {erosion_road_length_m}")

        flood_road_text = (
            f"{round(flood_road_length_m / 1000, 2)} km under severe/high flood zone"
            if flood_road_length_m > 0 else "No data"
        )

        erosion_road_text = (
            f"{round(erosion_road_length_m / 1000, 2)} km under severe/high erosion zone"
            if erosion_road_length_m > 0 else "No data"
        )

        # -----------------------------
        # SCHOOLS
        # -----------------------------
        schools_qs = Critical_Facility.objects.filter(
            village_id=village_id,
            occupancy_type__icontains='school'
        )

        total_schools = schools_qs.count()
        vulnerable_schools = schools_qs.filter(
            flood_depth_m__gt=0.5
        ).count()

        schools_text = (
            f"{vulnerable_schools} out of {total_schools} schools under high flood risk"
            if total_schools > 0 else "No educational facilities available"
        )

        print(f"🟢 Schools vulnerable: {schools_text}")

        # -----------------------------
        # ERODING RIVER BANK
        # -----------------------------
        erosion_text = get_eroding_river_bank(village_id)
        print(f"🟢 Eroding river bank: {erosion_text}")

        # -----------------------------
        # FINAL TABLE
        # -----------------------------
        return [
            ["Vulnerability Assessment"],
            ['Economic status', economic_status],
            ['Vulnerable population', vulnerable_population],
            ['Eroding river bank', erosion_text],
            ['Flood vulnerable Houses', flood_vulnerable_houses],
            ['Erosion vulnerable Houses', erosion_vulnerable_houses],
            ['Flood vulnerable Road', flood_road_text],
            ['Erosion vulnerable Road', erosion_road_text],
            ['School', schools_text],
            ['Livelihood vulnerability Index', '-'],
        ]

    except Exception as e:
        print("❌ Vulnerability Assessment fatal error:", e)
        return [
            ["Vulnerability Assessment"],
            ['Economic status', 'N/A'],
            ['Vulnerable population', 'N/A'],
            ['Eroding river bank', 'N/A'],
            ['Flood vulnerable Houses', 'N/A'],
            ['Erosion vulnerable Houses', 'N/A'],
            ['Flood vulnerable Road', 'N/A'],
            ['Erosion vulnerable Road', 'N/A'],
            ['School', 'N/A'],
            ['Livelihood vulnerability Index', 'N/A'],
        ]

def village_summary(elements,village_id):
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>2  Summary Village Details </b>", blue_heading)
    
    elements.append(heading)
    elements.append(Spacer(1, 12))
    

    table_sections = [
        {"heading": "General Summary",
          "getter_function": generate_general_summary_table,
          "col_width":[200, 300]
         },
        {"heading": "Socio-Economic Summary", 
         "getter_function": generate_socio_economic_summary_table,
          "col_width":[200, 300]
         },
       {
            "heading": "Hazard Assessment",
            "getter_function": getHazardAssessment,
             "col_width":[200, 150,150]
       },
       {
           'heading': "Vulnerability Assessment",
            "getter_function": getVulnerabilityAssessment,
             "col_width":[200, 300]
       },
       {
           'heading':"Risk Assessment (excluding content loss in INR Crore)",
           "getter_function": getRiskAssessment,
            "col_width":[200, 100,100,100],
            
       },
       {
           'heading':"Mitigation intervention",
           "getter_function": getMitigationIntervention,
            "col_width":[200, 300]
       }
    ]


    draw_Village_summery_tables(elements,table_sections,village_id)
    # elements.append(table)
    elements.append(PageBreak())


# def create_styled_table(table_data, col_width,merg=False):
#     styles = getSampleStyleSheet()
#     wrap_style = ParagraphStyle(
#         name="wrap_style",
#         fontName="Helvetica",
#         fontSize=9,
#         leading=11,
#         wordWrap='CJK',  # Enables wrapping at word boundaries
#     )

#     # Wrap cell content with Paragraphs
#     wrapped_data = []
#     for row in table_data:
#         wrapped_row = []
#         for cell in row:
#             if isinstance(cell, str):
#                 wrapped_row.append(Paragraph(cell, wrap_style))
#             else:
#                 wrapped_row.append(cell)
#         wrapped_data.append(wrapped_row)

#     # Create table
#     table = Table(wrapped_data, colWidths=col_width)
#     table_styles = [
#         ("BACKGROUND", (0, 0), (-1, 0), tb_header_bg),
#         ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
#         ("ALIGN", (0, 0), (-1, -1), "LEFT"),
#         ("VALIGN", (0, 0), (-1, -1), "TOP"),
#         ("GRID", (0, 0), (-1, -1), tb_border_width, tb_border_color),
#         ("FONTSIZE", (0, 0), (-1, -1), 9),
#         ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
#         ("TOPPADDING", (0, 0), (-1, -1), 4),
#     ]
#     if merg:
#         table_styles.insert(0, ('SPAN', (0, 0), (1, 0)))
#     table.setStyle(TableStyle(table_styles))
#     return table

def draw_Village_summery_tables(elements,table_sections,village_id):
    styles = getSampleStyleSheet()
    custom_style=[ ('SPAN', (0, 0), (-1, 0)),  ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),]
   
    for section in table_sections:
        # heading = Paragraph(f"<b>{section['heading']}</b>", styles["Heading2"])
        # elements.append(heading)
        # elements.append(Spacer(1, 6))

        table_data = section["getter_function"](village_id)
        
        table = create_styled_table(table_data, section['col_width'], False, True, custom_style, section['heading'])
        elements.append(table)
        if(section["heading"] == 'Vulnerability Assessment'):
            elements.append(PageBreak())
        # elements.append(Spacer(1, 12))
    
    # Notes section  
    # elements.append(Spacer(1, 12))
    # para=Paragraph("Note: While the investment amount mentioned above for mitigation represents the maximum, the Chapter 6 also presents various cost-effective alternatives. There are other possible cost effective solutions as well which can be explored while developing Detailed Project Report.", notes_style)
    # elements.append(para)

    # Village contacts 
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>2.1 Important contact details</b>", blue_sub_heading))
    elements.append(Spacer(1, 6))
    imp_contact_details=getDistrictLevelOfficialsData(village_id)
    table=create_styled_table(imp_contact_details, [40,150,160,150], False, True, [('ALIGN', (0, 1), (0, -1), 'RIGHT'),('ALIGN', (3, 1), (3, -1), 'RIGHT'),('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')], "Village Contacts")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Emergency toll free contact information
    
    elements.append(Paragraph('<b>2.2 Emergency Toll Free Contact Information</b>', blue_sub_heading))

    custom_style=[   ('ALIGN', (0, 1), (0, -1), 'RIGHT'),('ALIGN', (2, 1), (2, -1), 'RIGHT'),('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')]
    
    elements.append(Spacer(1, 6))
    emergency_contact_details=getEmergencyTollFreeContactData(village_id)
    table=create_styled_table(emergency_contact_details, [40, 250,210], False, True, custom_style, "Emergency Toll Free Contact")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # # Important Emergency contact information
    # elements.append(Paragraph("<u><b>Important Emergency Contact Information</b></u>", underline_heading))
    # elements.append(Spacer(1, 6))
    # imp_contact_details=getImportantEmergencyContactData(village_id)
    # table=create_styled_table(imp_contact_details, [40, 250, 210], False, True, custom_style, "Important Emergency Contact")
    # elements.append(table)
    # elements.append(Spacer(1, 12))
    
   
    
    
# from vdmp_dashboard.models import Risk_Assesment
# from village_profile.models import tblVillage

# def getRiskAssessment(village_id):
#     try:
#         # Validate and fetch village safely
#         village = tblVillage.objects.filter(id=village_id).first()
#         if not village:
#             return [
#                 ['Risk Assessment (excluding content loss in INR Crore)'],
#                 ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
#                 ['Residential', '-'],
#                 ['Commercial', '-'],
#                 ['Critical Facilities', '-'],
#                 ['Roads', '-'],
#                 ['Agriculture', '-'],
#                 ['Note', '-']
#             ]
        
#         risk_data = Risk_Assesment.objects.filter(village=village)
#         if risk_data.exists():
#             # Helper function to safely fetch value
#             def get_value(qs, hazard, exposure_filter):
#                 record = qs.filter(hazard__iexact=hazard, **exposure_filter).first()
#                 return record.total_exposure_value_inr_crore if record else '-'

#             # Residential
#             residential_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Residential"})
#             residential_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Residential"})
#             residential_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Residential"})

#             # Commercial
#             commercial_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Commercial"})
#             commercial_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Commercial"})
#             commercial_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Commercial"})

#             # Critical Facilities
#             critical_facilities_flood = get_value(risk_data, "Flood", {"exposure_type__icontains": "Critical"})
#             critical_facilities_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__icontains": "Critical"})
#             critical_facilities_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__icontains": "Essential"})

#             # Roads
#             roads_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Roads"})
#             roads_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Roads"})
#             roads_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Roads"})

#             # Agriculture
#             agriculture_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Agriculture"})
#             agriculture_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Agriculture"})
#             agriculture_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Agriculture"})

#             return [
#                 ['Risk Assessment (excluding content loss in INR Crore)'],
#                 ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
#                 ['Residential', str(residential_flood), str(residential_earthquake), str(residential_cyclone)],
#                 ['Commercial', str(commercial_flood), str(commercial_earthquake), str(commercial_cyclone)],
#                 ['Critical Facilities', str(critical_facilities_flood), str(critical_facilities_earthquake), str(critical_facilities_cyclone)],
#                 ['Roads', str(roads_flood), str(roads_earthquake), str(roads_cyclone)],
#                 ['Agriculture', str(agriculture_flood), str(agriculture_earthquake), str(agriculture_cyclone)],
#                 ['Note', '-', '-', '-']
#             ]
#         else:
#             return [
#                 ['Risk Assessment (excluding content loss in INR Crore)'],
#                 ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
#                 ['Residential', '-'],
#                 ['Commercial', '-'],
#                 ['Critical Facilities', '-'],
#                 ['Roads', '-'],
#                 ['Agriculture', '-'],
#                 ['Note', '-']
#             ]
#     except Exception as e:
#         # In case of invalid village_id or unexpected error
#         return [
#                 ['Risk Assessment (excluding content loss in INR Crore)'],
#                 ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
#                 ['Residential', '-'],
#                 ['Commercial', '-'],
#                 ['Critical Facilities', '-'],
#                 ['Roads', '-'],
#                 ['Agriculture', '-'],
#                 ['Note', '-']
#         ]

