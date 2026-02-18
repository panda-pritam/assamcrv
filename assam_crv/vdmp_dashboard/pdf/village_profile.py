from reportlab.platypus import Paragraph, Spacer,  ListFlowable, ListItem, Image,Table,TableStyle

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image as RLImage, Table as ReportLabTable, TableStyle
import os
from reportlab.platypus import Image as ReportLabImage, Table as ReportLabTable, TableStyle
from reportlab.lib import colors
import locale
locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')

def format_indian_number(num):
    try:
        return locale.format_string('%d', int(num), grouping=True)
    except:
        return str(num)
from .global_styles import blue_level3_heading, blue_heading,table_sub_title,blue_sub_heading,image_title,notes_style,tb_header_bg,Legend_heading,indented_style,bold_style,normal_style, bold_center_style_9,srNoStyle, heading_box_color,bold_center_style,right_align_text
from .utils.table import create_styled_table
from .utils.geoserverLayerImage import  get_geoserver_legend_path,get_geoserver_image_as_rl_image

from ..models import VillageListOfAllTheDistricts,HouseholdSurvey,Commercial,Critical_Facility,VillageRoadInfo
from village_profile.models import tblVillage
from administrator.models import FGD_livelihood_summary, PRA_main

from vdmp_dashboard.models import HouseholdSurvey,Critical_Facility,ElectricPole,Transformer

from django.db.models import Sum, Count
from django.db.models import Q

import requests
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus import Table as ReportLabTable
# from .village_summary import VILLAGE_SUMMARY_DATA
from django.db.models.functions import Lower, Trim  
from vdmp_dashboard.models import VdmpVillageMapData, VdmDistrictMapData

from django.db.models import Sum, IntegerField, FloatField
from django.db.models.functions import Cast, Coalesce, Replace
from assam_crv.settings import MEDIA_ROOT
from django.conf import settings

GEOSERVER_BASE_URL = settings.GEOSERVER_URL.rstrip('/')

styles = getSampleStyleSheet()
page_width, page_height = A4


# ------------------ data query -------------------------------


def getFacilityAccessData(village_id):
    try:
        pra_data = PRA_main.objects.filter(village_id=village_id).first()

        # -----------------------------
        # Helper function
        # -----------------------------
        def format_distance(distance):
            if distance is None:
                return "N/A"
            return f"{distance:.0f} km" if float(distance).is_integer() else f"{distance:.1f} km"

        # -----------------------------
        # If no PRA data
        # -----------------------------
        if not pra_data:
            return [
                ["S. No.", "Asset Type", "Distance from Village"],
                ["1", "Higher Secondary School", "N/A"],
                ["2", "College", "N/A"],
                ["3", "Post Office", "N/A"],
                ["4", "Police Station", "N/A"],
                ["5", "Banks", "N/A"],
                ["6", "PHC", "N/A"],
                ["7", "CHC", "N/A"],
                ["8", "Private clinic/ hospital", "N/A"],
                ["9", "Ambulance", "N/A"],
                ["10", "Bus service", "N/A"],
                ["11", "Main markets", "N/A"],
                ["12", "Veterinary Hospitals", "N/A"]
            ]

        # -----------------------------
        # Return actual data
        # -----------------------------
        return [
            [Paragraph("S. No.",bold_center_style_9), Paragraph("Asset Type",bold_center_style_9), Paragraph("Distance from Village",bold_center_style_9)],

            ["1", "Higher secondary school",
             format_distance(pra_data.nearest_higher_secondary_km)],

            ["2", "College",
             format_distance(pra_data.nearest_college_km)],

            ["3", "Post office",
             format_distance(pra_data.nearest_post_office_km)],

            ["4", "Police station",
             format_distance(pra_data.nearest_police_station_km)],

            ["5", "Banks",
             format_distance(pra_data.nearest_bank_atm_km)],

            ["6", "PHC",
             format_distance(pra_data.nearest_phc_km)],

            ["7", "CHC",
             format_distance(pra_data.nearest_chc_km)],

            ["8", "Private clinic/ hospital",
             format_distance(pra_data.nearest_hospital_km)],

            ["9", "Ambulance",
             format_distance(pra_data.nearest_ambulance_km)],

            ["10", "Bus service",
             format_distance(pra_data.nearest_bus_service_km)],

            ["11", "Main markets",
             format_distance(pra_data.main_market_km)],

            ["12", "Veterinary hospitals",
             format_distance(pra_data.nearest_veterinary_clinic_km)],
        ]

    except Exception as e:
        print("Facility access error:", e)

        return [
            ["S. No.", "Asset Type", "Distance from Village"],
            ["1", "Higher secondary school", "N/A"],
            ["2", "College", "N/A"],
            ["3", "Post office", "N/A"],
            ["4", "Police station", "N/A"],
            ["5", "Banks", "N/A"],
            ["6", "PHC", "N/A"],
            ["7", "CHC", "N/A"],
            ["8", "Private clinic/ hospital", "N/A"],
            ["9", "Ambulance", "N/A"],
            ["10", "Bus service", "N/A"],
            ["11", "Main markets", "N/A"],
            ["12", "Veterinary hospitals", "N/A"]
        ]


from django.db import connection

def getPowerInfrastructureData_Total(village_id):
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return [
            [Paragraph("S. No.", bold_center_style_9),
             Paragraph("Type", bold_center_style_9),
             Paragraph("Number", bold_center_style_9)],
            ["1", Paragraph("Electric post and network", normal_style), "N/A"],
            ["2", Paragraph("Transformer", normal_style), "N/A"],
        ]

    electric_data_total = 0
    transformer_data_total = 0

    # =========================
    # ELECTRIC POLES
    # =========================
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public'
                    AND table_name='electricpoles'
                )
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM public.electricpoles
                    WHERE "Vill_Id" = %s
                """, [village_code])
                electric_data_total = cursor.fetchone()[0] or 0
    except Exception as e:
        print("Electric poles error:", e)
        electric_data_total = 0

    # =========================
    # TRANSFORMER
    # =========================
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema='public'
                    AND table_name='transformer'
                )
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM public.transformer
                    WHERE "Vill_ID" = %s
                """, [village_code])
                transformer_data_total = cursor.fetchone()[0] or 0
    except Exception as e:
        print("Transformer error:", e)
        transformer_data_total = 0

    # =========================
    # RETURN TABLE
    # =========================
    return [
        [Paragraph("S. No.", bold_center_style_9),
         Paragraph("Type", bold_center_style_9),
         Paragraph("Number", bold_center_style_9)],
        ["1", Paragraph("Electric post and network", normal_style),
         Paragraph(str(electric_data_total),right_align_text)],
        ["2", Paragraph("Transformer", normal_style),
         Paragraph(str(transformer_data_total),right_align_text)],
    ]





def getVillageLocationDetails(village_id):
    from django.db import connection
    from administrator.models import PRA_main
    
    try:
        # Get basic village data from tblVillage
        village = tblVillage.objects.select_related(
            'gram_panchayat__circle__district'
        ).get(id=village_id)
        
        village_name = village.name or "N/A"
        block_name = village.gram_panchayat.name if village.gram_panchayat else "N/A"
        circle_name = village.gram_panchayat.circle.name if village.gram_panchayat and village.gram_panchayat.circle else "N/A"
        district_name = village.gram_panchayat.circle.district.name if village.gram_panchayat and village.gram_panchayat.circle and village.gram_panchayat.circle.district else "N/A"
        village_code = village.code
        
        # Initialize with defaults
        distance_hq = "N/A"
        total_area = "N/A"
        avg_elevation = "N/A"
        topography = "Flood plain"
        
        # Try to get data from village_polygon table (geometry-based area calculation)
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'village_boundary'
                    )
                """)
                
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        SELECT 
                            ST_Area(ST_Transform(geom, 32646)) / 1000000.0 as area_sqkm
                        FROM public.village_boundary
                        WHERE "Vill_ID" = %s
                    """, [village_code])
                    
                    row = cursor.fetchone()
                    if row and row[0]:
                        total_area = f"{row[0]:.2f}"
        except Exception as e:
            print("Village area query error:", e)
            pass
        
        # Try to get additional data from village_boundary table
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'village_boundary'
                    )
                """)
                
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        SELECT hq_distckm, avg_elev_m, topography
                        FROM public.village_boundary
                        WHERE "Vill_ID" = %s
                    """, [village_code])
                    
                    row = cursor.fetchone()
                    if row:
                        distance_hq = str(row[0]) if row[0] else "N/A"
                        avg_elevation = str(row[1]) if row[1] else "N/A"
                        topography = row[2] or "N/A"
        except Exception:
            pass
        
        # Fallback to PRA_main if data not found
        if avg_elevation == "N/A" or topography == "N/A" or distance_hq == "N/A":
            try:
                pra_data = PRA_main.objects.filter(village_id=village_id).first()
                if pra_data:
                    if avg_elevation == "N/A" and pra_data.average_elevation_msl:
                        avg_elevation = str(pra_data.average_elevation_msl)
                    if topography == "N/A" and pra_data.topography:
                        topography = pra_data.topography
                    if distance_hq == "N/A" and pra_data.distance_from_district_headquarter_km:
                        distance_hq = str(pra_data.distance_from_district_headquarter_km)
            except Exception:
                pass
        
        return [
            [Paragraph("Revenue Village", bold_style), Paragraph(village_name, normal_style)],
            [Paragraph("Block", bold_style), Paragraph(block_name, normal_style)],
            [Paragraph("Revenue Circle", bold_style), Paragraph(circle_name, normal_style)],
            [Paragraph("District", bold_style), Paragraph(district_name, normal_style)],
            [Paragraph("Distance from district headquarter (km)", bold_style), Paragraph(distance_hq, normal_style)],
            [Paragraph("Total area (sq km)", bold_style), Paragraph(total_area, normal_style)],
            [Paragraph("Average elevation (above MSL)", bold_style), Paragraph(avg_elevation, normal_style)],
            # [Paragraph("Topography", bold_style), Paragraph(topography, normal_style)],
        ]
        
    except tblVillage.DoesNotExist:
        return [
            [Paragraph("Revenue Village", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Block", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Revenue Circle", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("District", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Distance from district headquarter (km)", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Total area (sq km)", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Average elevation (above MSL)", bold_style), Paragraph("N/A", normal_style)],
            # [Paragraph("Topography", bold_style), Paragraph("N/A", normal_style)],
        ]


def getVillageDemographic(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        def safe_int(value):
            try:
                return int(value) if value and value.strip() else 0
            except (ValueError, AttributeError):
                return 0

        totals = households.aggregate(
            total_males=Coalesce(
                Sum(
                    Cast(
                        Cast('number_of_males_including_children', FloatField()),
                        IntegerField()
                    )
                ),
                0
            ),
            total_females=Coalesce(
                Sum(
                    Cast(
                        Cast('number_of_females_including_children', FloatField()),
                        IntegerField()
                    )
                ),
                0
            ),
        )


        total_males = totals['total_males'] or 0
        total_females = totals['total_females'] or 0
        
        # total_males = sum(safe_int(h.number_of_males_including_children) for h in households)
        # total_females = sum(safe_int(h.number_of_females_including_children) for h in households)
        total_population = total_males + total_females
        total_households = households.count()
        
        avg_family_size = int(round(total_population / total_households)) if total_households > 0 else 0
        

        male_female_ratio = round((total_females / total_males) * 1000) if total_females > 0 else 0
        
        # VILLAGE_SUMMARY_DATA['total_population']=total_population
        # VILLAGE_SUMMARY_DATA['total_households']=total_households
        
        return [
            [Paragraph('S. No.',bold_center_style_9),Paragraph("Household Characteristic",bold_center_style_9), Paragraph("Total", bold_center_style_9)],
            ['1',"No of Males", format_indian_number(total_males)],
            ['2',"No of Females", format_indian_number(total_females)],
            ['3',"Total Population", format_indian_number(total_population)],
            ["4","Number of Households", format_indian_number(total_households)],
            ['5',"Absentee House", "None"],
            ['6',"Average Family Size", str(avg_family_size)],
            ['7',Paragraph("Number of females per 1,000 males"), str(male_female_ratio)]
        ]
    except Exception:
        return [
            [Paragraph('S. No.',bold_center_style_9),Paragraph("Household Characteristic",bold_center_style_9), Paragraph("Total", bold_center_style_9)],
            ["1","No of Males", "N/A"],
            ["2","No of Females", "N/A"],
            ["3","Total Population", "N/A"],
            ["4","Number of Households", "N/A"],
            ["5","Absentee House", "N/A"],
            ["6","Average Family Size", "N/A"],
            ["7","Male-Female Ratio", "N/A"]
        ]
    
def map_economic_status(economic):
    if not economic:
        return None

    eco = str(economic).strip().lower()

    ECONOMIC_MAP = {
        'aay': ['aay', 'antyodaya'],
        'apl': ['apl', 'above poverty'],
        'ay':  ['ay', 'annapurna'],
        'bpl': ['bpl', 'below poverty'],
        'phh': ['phh', 'priority'],
    }

    for key, keywords in ECONOMIC_MAP.items():
        if any(word in eco for word in keywords):
            return key.upper()

    return None


def normalize_social_status(value):
    if not value:
        return "Others"

    v = value.lower()

    if 'differently' in v or 'disabled' in v:
        return 'Differently Abled'

    if 'widow' in v:
        return 'Widow'

    if 'single' in v and ('woman' in v or 'female' in v):
        return 'Single Woman'

    if 'single' in v and ('man' in v or 'male' in v):
        return 'Single Man'

    if 'married' in v and ('male' in v or 'man' in v):
        return 'Married Male'

   

    return 'Others'


def getSocialEconomicStatusData(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        # Social × Economic matrix
        data = {
            'Differently Abled': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Married Male': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Single Man': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Single Woman': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Widow': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
        }

        # -----------------------------
        # POPULATE MATRIX
        # -----------------------------
        for hh in households:
            social_key = normalize_social_status(hh.social_status)
            economic_key = map_economic_status(hh.economic_status)

            if social_key == 'Others' or not economic_key:
                continue

            data[social_key][economic_key] += 1

        # -----------------------------
        # BUILD TABLE
        # -----------------------------
        result = [[
            Paragraph("S. No.", bold_center_style_9),
            Paragraph("Social/Economic Status Household", bold_center_style_9),
            Paragraph("AAY",bold_center_style_9), Paragraph("APL", bold_center_style_9,), Paragraph("AY", bold_center_style_9,), Paragraph("BPL", bold_center_style_9,), Paragraph("PHH", bold_center_style_9),
            Paragraph("Total", bold_center_style_9),
            Paragraph("%", bold_center_style_9)
        ]]

        col_totals = {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0}
        sr_no = 1

        for social, counts in data.items():
            row_total = sum(counts.values())
            row_percent = (
                f"{round((row_total / total_households) * 100)}%"
                if total_households else "0%"
            )

            result.append([
                sr_no,
                social,
                counts['AAY'],
                counts['APL'],
                counts['AY'],
                counts['BPL'],
                counts['PHH'],
                row_total,
                row_percent
            ])

            for k in col_totals:
                col_totals[k] += counts[k]

            sr_no += 1

        # -----------------------------
        # COLUMN-WISE PERCENTAGES
        # -----------------------------
        col_percents = {}
        total_percent = 0
        for k, v in col_totals.items():
            pct = round((v / total_households) * 100) if total_households else 0
            col_percents[k] = f"{pct}%"
            total_percent += pct

        # -----------------------------
        # TOTAL ROW
        # -----------------------------
        result.append([
            sr_no,
            "Total",
            col_totals['AAY'],
            col_totals['APL'],
            col_totals['AY'],
            col_totals['BPL'],
            col_totals['PHH'],
            total_households,
            "100%"
        ])
        
        # -----------------------------
        # PERCENTAGE ROW
        # -----------------------------
        result.append([
            "",
            "%",
            col_percents['AAY'],
            col_percents['APL'],
            col_percents['AY'],
            col_percents['BPL'],
            col_percents['PHH'],
            "",
            f"{total_percent}%"
        ])

        # -----------------------------
        # SUMMARY (for narrative text)
        # -----------------------------
        summary = {
            'bpl_percent': round(col_totals['BPL'] / total_households * 100) if total_households else 0,
            'phh_percent': round(col_totals['PHH'] / total_households * 100) if total_households else 0,
            'aay_percent': round(col_totals['AAY'] / total_households * 100) if total_households else 0,
            'widow_percent': round(sum(data['Widow'].values()) / total_households * 100) if total_households else 0,
            'married_male_percent': round(sum(data['Married Male'].values()) / total_households * 100) if total_households else 0,
        }

        return result, summary

    except Exception as e:
        print("Social-economic table error:", e)

        empty_result = [[
            "S. No.",
            "Social/Economic Status Household",
            "AAY", "APL", "AY", "BPL", "PHH",
            "Total",
            "%"
        ]]

        empty_summary = {
            'bpl_percent': 0,
            'phh_percent': 0,
            'aay_percent': 0,
            'widow_percent': 0,
            'married_male_percent': 0,
        }

        return empty_result, empty_summary



from django.db.models import Case, When, IntegerField, Value, Q
from django.db.models.functions import Replace, Cast

def getIncomeGroupData(village_id):
    households = HouseholdSurvey.objects.filter(village_id=village_id)

    households = households.annotate(
        income_clean=Replace(
            Replace('approximate_income_earned_every_year_inr', Value(','), Value('')),
            Value(' '), Value('')
        )
    ).annotate(
        income_amt=Case(
            When(income_clean__regex=r'^\d+$',
                 then=Cast('income_clean', IntegerField())),
            default=None,
            output_field=IntegerField()
        )
    )

    upto_50k = households.filter(income_amt__lte=50000).count()
    upto_150k = households.filter(income_amt__gt=50000, income_amt__lte=150000).count()
    upto_250k = households.filter(income_amt__gt=150000, income_amt__lte=250000).count()
    above_250k = households.filter(income_amt__gt=250000).count()

    unknown = households.filter(income_amt__isnull=True).count()

    total = households.count()   # ✅ correct total

    def pct(val):
        return f"{(val / total * 100):.1f}%" if total else "0%"
    
    reported_total = (
        upto_50k +
        upto_150k +
        upto_250k +
        above_250k +
        unknown
    )

    total_pct = (reported_total / total * 100) if total else 0


    table_data = [
        [Paragraph("S. No.", bold_center_style_9), Paragraph("Income Group (INR)", bold_center_style_9), Paragraph("No. of Household",bold_center_style_9), Paragraph("%", bold_center_style_9)],
        ["1", "INR 50,000", upto_50k, pct(upto_50k)],
        ["2", Paragraph("INR 50,000 to 1,50,000"), upto_150k, pct(upto_150k)],
        ["3", Paragraph( "INR 150,000 to 2,50,000"), upto_250k, pct(upto_250k)],
        ["4", "> 2,50,000", above_250k, pct(above_250k)],
        ["5", "Income Not Reported", unknown, pct(unknown)],
        ["6", "Total", total, f"{total_pct}%"]
    ]

    low_income_percent = round(
        ((upto_50k + upto_150k) / total * 100), 1
    ) if total else 0

    return table_data, {"low_income_percent": low_income_percent}



def getAgricultureLandHoldingData(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        # Buckets
        leased = {'u05': 0, '0515': 0, '1525': 0, 'a25': 0}
        owned  = {'u05': 0, '0515': 0, '1525': 0, 'a25': 0}
        no_land = 0

        # ---------------------------
        # Helper: classify area (matching Excel formula)
        # ---------------------------
        def get_bucket(area):
            """
            Classify land area into buckets
            Returns: 'u05', '0515', '1525', 'a25', or None
            """
            try:
                # Convert to float (don't use int - it truncates!)
                area_float = float(area)
                
                if area_float <= 0:
                    return None  # No land
                elif area_float < 0.5:  # Changed from <= to <
                    return 'u05'
                elif area_float < 1.5:  # Changed from <= to <
                    return '0515'
                elif area_float <= 2.5:  # Keep <= for upper bound
                    return '1525'
                else:  # > 2.5
                    return 'a25'
            except (TypeError, ValueError):
                return None

        # ---------------------------
        # Main loop
        # ---------------------------
        for hh in households:
            ownership = (hh.own_agriculture_land or '').strip().lower()
            area_raw = hh.area_of_agriculture_land_owned_bigha

            # NO LAND / UNKNOWN
            if ownership in ('no', 'unknown', ''):
                no_land += 1
                continue

            bucket = get_bucket(area_raw)
            if not bucket:
                no_land += 1
                continue

            if ownership == 'leased':
                leased[bucket] += 1
            elif ownership in ('own', 'yes'):
                owned[bucket] += 1
            else:
                # If ownership is something else unexpected
                no_land += 1

        # ---------------------------
        # Totals
        # ---------------------------
        total_leased = sum(leased.values())
        total_owned = sum(owned.values())
        total_all = total_leased + total_owned + no_land

        # Column totals for each land size category
        col_u05 = leased['u05'] + owned['u05']
        col_0515 = leased['0515'] + owned['0515']
        col_1525 = leased['1525'] + owned['1525']
        col_a25 = leased['a25'] + owned['a25']

        # Percentage helper with 2 decimal places for individual, rounded for totals
        def pct(x, y, is_total=False):
            if y == 0:
                return "0.00%" if not is_total else "0%"
            percentage = (x / y * 100)
            if is_total:
                return f"{min(round(percentage), 100)}%"
            else:
                return f"{percentage:.2f}%"

        # ---------------------------
        # Table
        # ---------------------------
        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Agricultural land ownership (in bigha)", bold_center_style_9),
             Paragraph("< 0.5", bold_center_style_9), Paragraph("0.5-1.5", bold_center_style_9), Paragraph("1.5-2.5",bold_center_style_9), Paragraph(">2.5", bold_center_style_9), Paragraph("Total", bold_center_style_9)],

            ["1", "Leased",
             leased['u05'], leased['0515'],
             leased['1525'], leased['a25'],
             total_leased],

            ["2", "% leased to total leased",
             pct(leased['u05'], total_leased),
             pct(leased['0515'], total_leased),
             pct(leased['1525'], total_leased),
             pct(leased['a25'], total_leased),
             pct(total_leased, total_leased, is_total=True)],

            ["3", "Owned",
             owned['u05'], owned['0515'],
             owned['1525'], owned['a25'],
             total_owned],

            ["4", "% owned to total HH with own agriculture land",
             pct(owned['u05'], total_owned),
             pct(owned['0515'], total_owned),
             pct(owned['1525'], total_owned),
             pct(owned['a25'], total_owned),
             pct(total_owned, total_owned, is_total=True)],

            ["5", "No land (basically manual labour)", "", "", "", "", no_land],
            ["6", "Total", col_u05, col_0515, col_1525, col_a25, total_all]
        ]

        stats = {
            'owned_land_percent': round(total_owned / total_all * 100) if total_all > 0 else 0
        }

        return table_data, stats

    except Exception as e:
        print(f"Error in getAgricultureLandHoldingData: {e}")
        return [
           [Paragraph("S. No.", bold_center_style_9), Paragraph("Agricultural land ownership (in bigha)", bold_center_style_9),
             Paragraph("< 0.5", bold_center_style_9), Paragraph("0.5-1.5", bold_center_style_9), Paragraph("1.5-2.5",bold_center_style_9), Paragraph(">2.5", bold_center_style_9), Paragraph("Total", bold_center_style_9)],
            ["1", "Leased", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["2", "% leased to total leased", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["3", "Owned", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["4", "% owned to total HH with own agriculture land", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["5", "No land (basically manual labour)", "", "", "", "", "N/A"],
            ["6", "Total", "", "", "", "", "N/A"]
        ], {'owned_land_percent': 0}



def getAverageExpenditureBreakdownData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        if not households.exists():
            return [
                 [Paragraph("S. No.", bold_center_style_9), Paragraph("Expenditure Category", bold_center_style_9), Paragraph("%", bold_center_style_9)],
                ["1", "Agriculture", "-"],
                ["2", "Festival and marriage", "-"],
                ["3", "House repair", "-"],
                ["4", "Tobacco and liquor", "-"],
                ["5", "Education", "-"],
                ["6", "Health", "-"],
                ["7", "Food", "-"],
                ["8", "Total", "-"]
            ]
        
        def safe_decimal(value):
            try:
                if not value or str(value).strip() == '' or str(value).strip().lower() == 'none':
                    return Decimal('0')
                # Clean the value - remove any non-numeric characters except decimal point
                clean_value = ''.join(c for c in str(value) if c.isdigit() or c == '.')
                return Decimal(clean_value) if clean_value else Decimal('0')
            except (ValueError, TypeError, AttributeError, decimal.InvalidOperation):
                return Decimal('0')
        
        # Sum each field manually since they are CharField
        agri_sum = sum(safe_decimal(h.amount_spent_for_agriculture_livestock) for h in households)
        festival_sum = sum(safe_decimal(h.expense_on_festival_marriage_and_other_social_occassions) for h in households)
        repair_sum = sum(safe_decimal(h.expense_on_house_repair) for h in households)
        tobacco_sum = sum(safe_decimal(h.expense_on_tobacco_liquor) for h in households)
        education_sum = sum(safe_decimal(h.expense_on_education) for h in households)
        health_sum = sum(safe_decimal(h.expense_on_health) for h in households)
        food_sum = sum(safe_decimal(h.expense_on_food) for h in households)

        grand_total = agri_sum + festival_sum + repair_sum + tobacco_sum + education_sum + health_sum + food_sum

        def percentage(x):
            if grand_total == 0:
                return "0"
            pct = (Decimal(x) / grand_total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return f"{pct}%"

        agri_pct = percentage(agri_sum)
        festival_pct = percentage(festival_sum)
        repair_pct = percentage(repair_sum)
        tobacco_pct = percentage(tobacco_sum)
        education_pct = percentage(education_sum)
        health_pct = percentage(health_sum)
        food_pct = percentage(food_sum)
        
        total_pct = sum([
            Decimal(agri_pct.rstrip('%')) if agri_pct != '0' else Decimal('0'),
            Decimal(festival_pct.rstrip('%')) if festival_pct != '0' else Decimal('0'),
            Decimal(repair_pct.rstrip('%')) if repair_pct != '0' else Decimal('0'),
            Decimal(tobacco_pct.rstrip('%')) if tobacco_pct != '0' else Decimal('0'),
            Decimal(education_pct.rstrip('%')) if education_pct != '0' else Decimal('0'),
            Decimal(health_pct.rstrip('%')) if health_pct != '0' else Decimal('0'),
            Decimal(food_pct.rstrip('%')) if food_pct != '0' else Decimal('0')
        ])

        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Expenditure Category", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Agriculture", agri_pct],
            ["2", "Festival and marriage", festival_pct],
            ["3", "House repair", repair_pct],
            ["4", "Tobacco and liquor", tobacco_pct],
            ["5", "Education", education_pct],
            ["6", "Health", health_pct],
            ["7", "Food", food_pct],
            ["8", "Total", f"{total_pct}%" if grand_total > 0 else "0"]
        ]

    except Exception as e:
        print(f"Error in getAverageExpenditureBreakdownData: {e}")
        return [
             [Paragraph("S. No.", bold_center_style_9), Paragraph("Expenditure Category", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Agriculture", "N/A"],
            ["2", "Festival and marriage", "N/A"],
            ["3", "House repair", "N/A"],
            ["4", "Tobacco and liquor", "N/A"],
            ["5", "Education", "N/A"],
            ["6", "Health", "N/A"],
            ["7", "Food", "N/A"],
            ["8", "Total", "N/A"]
        ]
        
def getHouseholdDebtLiabilityData(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        if total_households == 0:
            return [
                [Paragraph("S. No.", bold_center_style_9), Paragraph("Loan Amount (INR)",bold_center_style_9), Paragraph("Number of households",bold_center_style_9), Paragraph("%", bold_center_style_9)],
                ["1", "No Loan", "0", "0.00%"],
                ["2", "Upto 10K", "0", "0.00%"],
                ["3", "Upto 50K", "0", "0.00%"],
                ["4", "Upto 100K", "0", "0.00%"],
                ["5", "More than 100K", "0", "0.00%"],
                ["6", "Total", "0", "0.00%"]
            ]

        households = households.annotate(
            loan_amt=Cast(Cast('loan_amount', FloatField()), IntegerField())
        )

        # ✅ SINGLE SOURCE OF TRUTH: loan_amt
        no_loan = households.filter(
            Q(loan_amt__isnull=True) | Q(loan_amt__lte=0)
        ).count()

        upto_10k = households.filter(loan_amt__gt=0, loan_amt__lte=10000).count()
        upto_50k = households.filter(loan_amt__gt=10000, loan_amt__lte=50000).count()
        upto_100k = households.filter(loan_amt__gt=50000, loan_amt__lte=100000).count()
        more_than_100k = households.filter(loan_amt__gt=100000).count()

        total_count = (
            no_loan +
            upto_10k +
            upto_50k +
            upto_100k +
            more_than_100k
        )

        def pct(val):
            return round((val / total_households) * 100, 2)

        total_pct = round((total_count / total_households) * 100)

        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Loan Amount (INR)",bold_center_style_9), Paragraph("Number of households",bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "No Loan", str(no_loan), f"{pct(no_loan)}%"],
            ["2", "Upto 10K", str(upto_10k), f"{pct(upto_10k)}%"],
            ["3", "Upto 50K", str(upto_50k), f"{pct(upto_50k)}%"],
            ["4", "Upto 100K", str(upto_100k), f"{pct(upto_100k)}%"],
            ["5", "More than 100K", str(more_than_100k), f"{pct(more_than_100k)}%"],
            ["6", "Total", str(total_count), f"{total_pct}%"]
        ]

    except Exception as e:
        print("Debt Liability Error:", e)
        return [
             [Paragraph("S. No.", bold_center_style_9), Paragraph("Loan Amount (INR)",bold_center_style_9), Paragraph("Number of households",bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "No Loan", "N/A", "N/A"],
            ["2", "Upto 10K", "N/A", "N/A"],
            ["3", "Upto 50K", "N/A", "N/A"],
            ["4", "Upto 100K", "N/A", "N/A"],
            ["5", "More than 100K", "N/A", "N/A"],
            ["6", "Total", "N/A", "N/A"]
        ]


from django.db.models import Q

def getPrimaryLivelihoodDistributionData(village_id, type='primary'):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        field_name = 'livelihood_primary' if type == 'primary' else 'livelihood_secondary'
        activity_type = 'Primary economic activity' if type == 'primary' else 'Secondary economic activity'

        if total_households == 0:
            return [
                [Paragraph("S. No.", bold_center_style_9), Paragraph('Livelihood',bold_center_style_9), Paragraph(f"{activity_type}",bold_center_style_9)],
                ["", "", "No. of Household", "%"],
                ["1", "Agriculture", "0", "0.00%"],
                ["2", "Fishing", "0", "0.00%"],
                ["3", "Livestock", "0", "0.00%"],
                ["4", "Manual labour", "0", "0.00%"],
                ["5", "Weaving", "0", "0.00%"],
                ["6", "No job", "0", "0.00%"],
                ["7", "Service", "0", "0.00%"],
                ["8", "Shop", "0", "0.00%"],
                ["9", "Not Specified", "0", "0.00%"],
                ["10", "Total", "0", "0%"]
            ]

        agriculture = households.filter(**{f"{field_name}__iexact": "Agriculture"}).count()
        fishing = households.filter(**{f"{field_name}__iexact": "Fishing"}).count()
        livestock = households.filter(**{f"{field_name}__iexact": "Livestock"}).count()
        manual_labour = households.filter(**{f"{field_name}__iexact": "Manual Labour"}).count()
        weaving = households.filter(**{f"{field_name}__iexact": "Weaving"}).count()
        service = households.filter(**{f"{field_name}__iexact": "Service"}).count()
        shop = households.filter(**{f"{field_name}__iexact": "Shop"}).count()

        no_job = households.filter(
            Q(**{f"{field_name}__icontains": "no job"}) |
            Q(**{f"{field_name}__icontains": "none"})
        ).count()

        not_specified = households.filter(
            Q(**{f"{field_name}__isnull": True}) |
            Q(**{f"{field_name}__exact": ""})
        ).count()

        def pct(val):
            if total_households == 0:
                return "N/A"
            return f"{(val / total_households * 100):.2f}%"

        total_count = (
            agriculture + fishing + livestock + manual_labour +
            weaving + no_job + service + shop + not_specified
        )

        total_pct = f"{(total_count / total_households * 100):.0f}%"

        return [
           [Paragraph("S. No.", bold_center_style_9), Paragraph('Livelihood',bold_center_style_9), Paragraph(f"{activity_type}",bold_center_style_9)],
            ["", "", Paragraph("No. of Household", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Agriculture", str(agriculture), pct(agriculture)],
            ["2", "Fishing", str(fishing), pct(fishing)],
            ["3", "Livestock", str(livestock), pct(livestock)],
            ["4", "Manual labour", str(manual_labour), pct(manual_labour)],
            ["5", "Weaving", str(weaving), pct(weaving)],
            ["6", "No job", str(no_job), pct(no_job)],
            ["7", "Service", str(service), pct(service)],
            ["8", "Shop", str(shop), pct(shop)],
            ["9", "Not Specified", str(not_specified), pct(not_specified)],
            ["10", "Total", str(total_count), total_pct]
        ]

    except Exception as e:
        print(f"Error in getPrimaryLivelihoodDistributionData: {e}")
        activity_type = 'Primary economic activity' if type == 'primary' else 'Secondary economic activity'
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph('Livelihood',bold_center_style_9), Paragraph(f"{activity_type}",bold_center_style_9)],
            ["", "", "No. of Household", "%"],
            ["1", "Agriculture", "N/A", "N/A"],
            ["2", "Fishing", "N/A", "N/A"],
            ["3", "Livestock", "N/A", "N/A"],
            ["4", "Manual labour", "N/A", "N/A"],
            ["5", "Weaving", "N/A", "N/A"],
            ["6", "No job", "N/A", "N/A"],
            ["7", "Service", "N/A", "N/A"],
            ["8", "Shop", "N/A", "N/A"],
            ["9", "Not Specified", "N/A", "N/A"],
            ["10", "Total", "N/A", "N/A"]
        ]




def getCropCultivationData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [[Paragraph('S. No.',bold_center_style_9),Paragraph("Number of crops", bold_center_style_9), Paragraph("No. of Household", bold_center_style_9), Paragraph("%", bold_center_style_9)], ["1", "One crop", "0", "0%"], ["2", "Two crops", "0", "0%"], ["3", "More than 2 crops", "0", "0%"], ["4", "No agriculture", "0", "0%"], ["5", "Total", "0", "0%"]]
        
        one_crop = 0
        two_crops = 0
        more_than_two = 0
        no_agriculture = 0
        
        for hh in households:
            crops = (hh.crops_cultivated or '').strip().lower()
            
            # Check for empty, none, or null
            if not crops or crops in ('none', 'null', 'n/a'):
                no_agriculture += 1
                continue
            
            # Split by comma and count non-empty crops
            crop_list = [c.strip() for c in crops.split(',') if c.strip() and c.strip() not in ('none', 'null', 'n/a')]
            crop_count = len(crop_list)
            
            if crop_count == 0:
                no_agriculture += 1
            elif crop_count == 1:
                one_crop += 1
            elif crop_count == 2:
                two_crops += 1
            else:
                more_than_two += 1
        
        # Calculate percentages
        one_crop_pct = f"{(one_crop/total_households*100):.2f}%"
        two_crops_pct = f"{(two_crops/total_households*100):.2f}%"
        more_than_two_pct = f"{(more_than_two/total_households*100):.2f}%"
        no_agriculture_pct = f"{(no_agriculture/total_households*100):.2f}%"
        
        total_count = one_crop + two_crops + more_than_two + no_agriculture
        if total_households > 0:
            raw_pct = (total_count / total_households) * 100

            if raw_pct >= 99.5:   # handle floating-point precision
                total_pct = 100
            else:
                total_pct = round(raw_pct)
        else:
            total_pct = 0

        
        return [
            [Paragraph('S. No.',bold_center_style_9),Paragraph("Number of crops", bold_center_style_9), Paragraph("No. of Household", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "One crop", str(one_crop), one_crop_pct],
            ["2", "Two crops", str(two_crops), two_crops_pct],
            ["3", "More than 2 crops", str(more_than_two), more_than_two_pct],
            ["4", "No agriculture", str(no_agriculture), no_agriculture_pct],
            ["5", "Total", str(total_count), f"{total_pct}%"]
        ]
    except Exception:
        return [
            [Paragraph('S. No.',bold_center_style_9),Paragraph("Number of crops", bold_center_style_9), Paragraph("No. of Household", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "One crop", "N/A", "N/A"],
            ["2", "Two crops", "N/A", "N/A"],
            ["3", "More than 2 crops", "N/A", "N/A"],
            ["4", "No agriculture", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A"]
        ]


def normalize_percentages(counts, total, decimals=0):
    """
    Normalize percentages so that they sum EXACTLY to 100.
    Adjusts the last non-zero bucket.
    """
    if total == 0:
        return ["-"] * len(counts)

    raw = [(c / total) * 100 for c in counts]
    rounded = [round(p, decimals) for p in raw]

    diff = round(100 - sum(rounded), decimals)

    for i in reversed(range(len(rounded))):
        if counts[i] > 0:
            rounded[i] = round(rounded[i] + diff, decimals)
            break

    return [f"{p:.{decimals}f}%" for p in rounded]


from django.db.models import Q

def getLivestockOwnershipData(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        # ================= ZERO DATA =================
        if total_households == 0:
            return [
                [Paragraph('S. No.',bold_center_style_9), Paragraph("Count",bold_center_style_9), Paragraph("Livestock",bold_center_style_9),"",Paragraph("Small cattle",bold_center_style_9)],
                ["", "", Paragraph("Household with big Cattle",bold_center_style_9), Paragraph("%",bold_center_style_9), Paragraph("HH with small cattle",bold_center_style_9), Paragraph("%",bold_center_style_9)],

                ["1", "0", "0", "-", "0", "-"],
                ["2", "< 3", "0", "-", "0", "-"],
                ["3", "3–6", "0", "-", "0", "-"],
                ["4", ">6", "0", "-", "0", "-"],

                ["5", "Total", "0", "-", "0", "-"]
            ]

        # ================= BIG CATTLE =================
        big_counts = [
            households.filter(big_cattle__iexact='no big cattle').count(),
            households.filter(big_cattle__iexact='upto 3 big cattle').count(),
            households.filter(big_cattle__iexact='3 to 6 big cattle').count(),
            households.filter(
                Q(big_cattle__iexact='>6 big cattle') |
                Q(big_cattle__iexact='more than 6 big cattle')
            ).count()
        ]

        # ================= SMALL CATTLE =================
        small_counts = [
            households.filter(small_cattle__iexact='no small cattle').count(),
            households.filter(small_cattle__iexact='upto 3 small cattle').count(),
            households.filter(small_cattle__iexact='3 to 6 small cattle').count(),
            households.filter(
                Q(small_cattle__iexact='>6 small cattle') |
                Q(small_cattle__iexact='more than 6 small cattle')
            ).count()
        ]

        # ================= PERCENTAGES =================
        big_pcts = normalize_percentages(big_counts, total_households, decimals=0)
        small_pcts = normalize_percentages(small_counts, total_households, decimals=2)

        total_big = sum(big_counts)
        total_small = sum(small_counts)

        # Calculate actual total percentages
        total_big_pct = f"{round(100 * total_big / total_households)}%" if total_households > 0 else "-"
        total_small_pct = f"{(100 * total_small / total_households):.2f}%" if total_households > 0 else "-"

        return [
            [Paragraph('S. No.',bold_center_style_9), Paragraph("Count",bold_center_style_9), Paragraph("Livestock",bold_center_style_9),"",Paragraph("Small cattle",bold_center_style_9)],
                ["", "", Paragraph("Household with big Cattle",bold_center_style_9), Paragraph("%",bold_center_style_9), Paragraph("HH with small cattle",bold_center_style_9), Paragraph("%",bold_center_style_9)],

            ["1", "0", str(big_counts[0]), big_pcts[0], str(small_counts[0]), small_pcts[0]],
            ["2", "< 3", str(big_counts[1]), big_pcts[1], str(small_counts[1]), small_pcts[1]],
            ["3", "3–6", str(big_counts[2]), big_pcts[2], str(small_counts[2]), small_pcts[2]],
            ["4", ">6", str(big_counts[3]), big_pcts[3], str(small_counts[3]), small_pcts[3]],

            ["5", "Total", str(total_big), total_big_pct, str(total_small), total_small_pct]
        ]

    except Exception as e:
        print("Livestock Ownership Error:", e)
        return [
           [Paragraph('S. No.',bold_center_style_9), Paragraph("Count",bold_center_style_9), Paragraph("Livestock",bold_center_style_9),"",Paragraph("Small cattle",bold_center_style_9)],
                ["", "", Paragraph("Household with big Cattle",bold_center_style_9), Paragraph("%",bold_center_style_9), Paragraph("HH with small cattle",bold_center_style_9), Paragraph("%",bold_center_style_9)],

            ["1", "0", "N/A", "N/A", "N/A", "N/A"],
            ["2", "< 3", "N/A", "N/A", "N/A", "N/A"],
            ["3", "3–6", "N/A", "N/A", "N/A", "N/A"],
            ["4", ">6", "N/A", "N/A", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A", "N/A", "N/A"]
        ]

def getHousingTypologyData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"], ["No. of Household", "-", "-", "-", "-"], ["%", "-", "-", "-", ""]]
        
        # Count households by house type
        kachcha = households.filter(house_type='Kachcha').count()
        semi_pucca = households.filter(house_type='Semi Pucca').count()
        pucca = households.filter(house_type='Pucca').count()
        
        # Find dominant house type and update global dictionary
        counts = {'Kachcha': kachcha, 'Semi Pucca': semi_pucca, 'Pucca': pucca}
        max_house_type = max(counts, key=counts.get)
        max_percentage = round((counts[max_house_type] / total_households) * 100, 1)
        # VILLAGE_SUMMARY_DATA['dominant_house_type'] = f"{max_house_type} - {max_percentage}%"
        
        # Calculate percentages as numbers first
        kachcha_pct_val = round(kachcha / total_households * 100, 1)
        semi_pucca_pct_val = round(semi_pucca / total_households * 100, 1)
        pucca_pct_val = round(pucca / total_households * 100, 1)

        # Total percentage (fix rounding by ensuring max 100%)
        total_pct_val = min(100, round(kachcha_pct_val + semi_pucca_pct_val + pucca_pct_val, 1))

        # Convert to strings with %
        kachcha_pct = f"{kachcha_pct_val}%"
        semi_pucca_pct = f"{semi_pucca_pct_val}%"
        pucca_pct = f"{pucca_pct_val}%"
        total_pct = f"{total_pct_val}%"

        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Typology", bold_center_style_9), Paragraph("Kachcha", bold_center_style_9), Paragraph("Semi Pucca",bold_center_style_9), Paragraph("Pucca", bold_center_style_9), Paragraph("Total", bold_center_style_9)],
            ["1", "No. of Household", str(kachcha), str(semi_pucca), str(pucca), str(total_households)],
            ["2", "Percentage %", kachcha_pct, semi_pucca_pct, pucca_pct, total_pct]
        ]

    except Exception:
        return [
             [Paragraph("S. No.", bold_center_style_9), Paragraph("Typology", bold_center_style_9), Paragraph("Kachcha", bold_center_style_9), Paragraph("Semi Pucca",bold_center_style_9), Paragraph("Pucca", bold_center_style_9), Paragraph("Total", bold_center_style_9)],
            ["1", "No. of Household", "N/A", "N/A", "N/A", "N/A"],
            ["2", "Percentage %", "N/A", "N/A", "N/A", ""]
        ]
        
def getDigitalAccessData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [ [Paragraph("S. No.", bold_center_style_9), Paragraph("Digital Media Owned", bold_center_style_9), Paragraph("No of households", bold_center_style_9), Paragraph("%", bold_center_style_9)], ["1", "Mobile Phone", "-", "-"], ["2", "TV", "-", "-"], ["3", "Radio", "-", "-"], ["4", "Radio and Mobile Phone", "-", "-"], ["5", "TV and Mobile Phone", "-", "-"], ["6", "None", "-", "-"], ["7", "Total", "-", "-"]]
        
        mobile_only = 0
        tv_only = 0
        radio_only = 0
        radio_mobile = 0
        tv_mobile = 0
        none_count = 0
        
        for hh in households:
            media = hh.digital_media_owned or ''
            media_items = [item.strip() for item in media.split(',') if item.strip()]
            
            has_mobile = any('Mobile Phone' in item for item in media_items)
            has_tv = any('Tv' in item or 'TV' in item for item in media_items)
            has_radio = any('Radio' in item for item in media_items)
            
            if has_radio and has_mobile and not has_tv:
                radio_mobile += 1
            elif has_mobile and has_tv and not has_radio:
                tv_mobile += 1
            elif has_mobile and not has_tv and not has_radio:
                mobile_only += 1
            # elif has_tv and not has_mobile and not has_radio:
            #     tv_only += 1

            elif has_tv:
                tv_only += 1
            elif has_radio and not has_mobile and not has_tv:
                radio_only += 1
            else:
                none_count += 1
            
            # elif not media_items or media.strip().lower() == 'none':
            #     none_count += 1
        
        mobile_pct = f"{round(mobile_only/total_households*100)}%"
        tv_pct = f"{round(tv_only/total_households*100)}%"
        radio_pct = f"{round(radio_only/total_households*100)}%"
        radio_mobile_pct = f"{round(radio_mobile/total_households*100)}%"
        tv_mobile_pct = f"{round(tv_mobile/total_households*100)}%"
        none_pct = f"{round(none_count/total_households*100)}%"
        
        total_count = mobile_only + tv_only + radio_only + radio_mobile + tv_mobile + none_count
        total_pct = round(mobile_only/total_households*100) + round(tv_only/total_households*100) + round(radio_only/total_households*100) + round(radio_mobile/total_households*100) + round(tv_mobile/total_households*100) + round(none_count/total_households*100)
        
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Digital Media Owned", bold_center_style_9), Paragraph("No of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Mobile Phone", str(mobile_only), mobile_pct],
            ["2", "TV", str(tv_only), tv_pct],
            ["3", "Radio", str(radio_only), radio_pct],
            ["4", "Radio and Mobile Phone", str(radio_mobile), radio_mobile_pct],
            ["5", "TV and Mobile Phone", str(tv_mobile), tv_mobile_pct],
            ["6", "None", str(none_count), none_pct],
            ["7", "Total", str(total_count), f"{total_pct}%"]
        ]
    except Exception:
        return [
             [Paragraph("S. No.", bold_center_style_9), Paragraph("Digital Media Owned", bold_center_style_9), Paragraph("No of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Mobile Phone", "N/A", "N/A"],
            ["2", "TV", "N/A", "N/A"],
            ["3", "Radio", "N/A", "N/A"],
            ["4", "Radio and Mobile Phone", "N/A", "N/A"],
            ["5", "TV and Mobile Phone", "N/A", "N/A"],
            ["6", "None", "N/A", "N/A"],
            ["7", "Total", "N/A", "N/A"]
        ]

from django.db.models import Q
from django.db.models.functions import Lower, Trim

def getPublicAssetsData(village_id):
    try:
        facilities = Critical_Facility.objects.filter(
            village_id=village_id
        ).annotate(
            clean_type=Lower(Trim('occupancy_type'))
        )

        if not facilities.exists():
            return [
                ["Presence of facilities"],
                ["S. No.", "Type", "Number", "Electricity", "Drinking water", "Sanitation", "Good road access", "Building condition (Good)"],
                ["1", "Anganwadi", "-", "-", "-", "-", "-", "-"],
                ["2", "School", "-", "-", "-", "-", "-", "-"],
                ["3", "Govt Office", "-", "-", "-", "-", "-", "-"],
                ["4", "Religious Place", "-", "-", "-", "-", "-", "-"],
                ["5", "Total", "-", "-", "-", "-", "-", "-"]
            ]

        # Define clean matching keywords
        facility_map = {
            "Anganwadi": ["anganwadi"],
            "School": ["school"],
            "Govt Office": ["govt office", "government office"],
            "Religious Place": ["religious place", "temple", "mosque", "church"]
        }

        result = [
            [Paragraph("Presence of facilities", bold_center_style_9)],
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Type", bold_center_style_9), Paragraph("Number", bold_center_style_9), Paragraph("Electricity", bold_center_style_9), Paragraph("Drinking Water", bold_center_style_9), Paragraph("Sanitation", bold_center_style_9), Paragraph("Good Road Access", bold_center_style_9), Paragraph("Building Condition (Good)", bold_center_style_9)]
        ]

        total_facilities = 0
        total_electricity = 0
        total_drinking_water = 0
        total_sanitation = 0
        total_good_road = 0
        total_good_building = 0

        for i, (label, keywords) in enumerate(facility_map.items(), 1):

            # Match using icontains on cleaned field
            type_facilities = facilities.filter(
                Q(clean_type__icontains=keywords[0])
            )

            total_count = type_facilities.count()

            electricity_count = type_facilities.filter(
                house_has_electric_connection__iexact='yes'
            ).count()

            drinking_water_count = type_facilities.exclude(
                drinking_water_source__isnull=True
            ).exclude(
                drinking_water_source__exact=''
            ).count()

            sanitation_count = type_facilities.exclude(
                toilet_facility__isnull=True
            ).exclude(
                toilet_facility__exact=''
            ).count()

            good_road_count = type_facilities.filter(
                access_road_during_flood__iexact='good road'
            ).count()

            good_building_count = type_facilities.filter(
                building_quality__icontains='good'
            ).count()

            # Add to totals
            total_facilities += total_count
            total_electricity += electricity_count
            total_drinking_water += drinking_water_count
            total_sanitation += sanitation_count
            total_good_road += good_road_count
            total_good_building += good_building_count

            result.append([
                str(i),
                label,
                str(total_count),
                str(electricity_count),
                str(drinking_water_count),
                str(sanitation_count),
                str(good_road_count),
                str(good_building_count)
            ])

        # Total row
        result.append([
            str(len(facility_map) + 1),
            "Total",
            str(total_facilities),
            str(total_electricity),
            str(total_drinking_water),
            str(total_sanitation),
            str(total_good_road),
            str(total_good_building)
        ])

        return result

    except Exception as e:
        print(f"Error in getPublicAssetsData: {e}")
        return [
         [Paragraph("Presence of facilities", bold_center_style_9)],
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Type", bold_center_style_9), Paragraph("Number", bold_center_style_9), Paragraph("Electricity", bold_center_style_9), Paragraph("Drinking Water", bold_center_style_9), Paragraph("Sanitation", bold_center_style_9), Paragraph("Good Road Access", bold_center_style_9), Paragraph("Building Condition (Good)", bold_center_style_9)],
            ["1", "Anganwadi", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["2", "School", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["3", "Govt Office", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["4", "Religious Place", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
        ]



from collections import defaultdict
from django.db import connection
import requests

def percent(val, total, is_total=False):
    if not total:
        return "0%"
    if is_total:
        return "100%"
    return f"{round((val / total) * 100, 2)}%"

def getRoadLengthByTypologyData(village_id, workspace, layer):
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return [
            ["S. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
            ["", "Village not found", "0", "0%"]
        ]

    # =========================
    # 1️⃣ TRY DATABASE FIRST
    # =========================
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'road_network'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if table_exists:
                # Try uppercase first
                try:
                    cursor.execute("""
                        SELECT "RSur_Type", SUM("Length") AS total_length
                        FROM public.road_network
                        WHERE "Vill_ID" = %s
                        GROUP BY "RSur_Type"
                        ORDER BY total_length DESC
                    """, [village_code])
                    rows = cursor.fetchall()
                except Exception:
                    # Fallback to lowercase
                    cursor.execute("""
                        SELECT rsur_type, SUM(length) AS total_length
                        FROM public.road_network
                        WHERE vill_id = %s
                        GROUP BY rsur_type
                        ORDER BY total_length DESC
                    """, [village_code])
                    rows = cursor.fetchall()

                if rows:
                    total_length_m = sum(r[1] for r in rows if r[1])
                    total_length_km = total_length_m / 1000 if total_length_m else 0

                    result = [
                        [Paragraph("S. No.", bold_center_style_9), Paragraph("Surface type", bold_center_style_9), Paragraph("Length (km)", bold_center_style_9), Paragraph("% to Total road length", bold_center_style_9 )]
                    ]

                    for idx, (surface, length_m) in enumerate(rows, 1):
                        length_km = (length_m or 0) / 1000
                        result.append([
                            str(idx),
                            surface or "Unknown",
                            f"{length_km:.2f}",
                            percent(length_km, total_length_km)
                        ])

                    # ✅ TOTAL ROW (NO HARDCODE)
                    result.append([
                        str(len(rows) + 1),
                        "Total",
                        f"{total_length_km:.2f}",
                        percent(total_length_km, total_length_km, is_total=True)
                    ])

                    return result
    except Exception:
        pass  # fallback to GeoServer

    # =========================
    # 2️⃣ FALLBACK TO GEOSERVER
    # =========================
    try:
        # Build WFS request
        wfs_url = f"{GEOSERVER_BASE_URL}/{workspace}/ows"
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": f"{workspace}:{layer}",
            "outputFormat": "application/json",
            "CQL_FILTER": f"vill_id='{village_code}'"
        }

        response = requests.get(wfs_url, params=params, timeout=10)
        response.raise_for_status()

        geojson = response.json()
        features = geojson.get("features", [])

        surface_lengths = defaultdict(float)

        for f in features:
            props = f.get("properties", {})
            surface = (props.get("rsur_type") or "Unknown").strip()
            length_m = props.get("length") or 0
            surface_lengths[surface] += float(length_m)

        total_length_km = sum(surface_lengths.values()) / 1000

        result = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Surface type", bold_center_style_9), Paragraph("Length (km)", bold_center_style_9), Paragraph("% to Total road length", bold_center_style_9 )]
        ]

        for idx, (surface, length_m) in enumerate(surface_lengths.items(), 1):
            length_km = length_m / 1000
            result.append([
                str(idx),
                surface,
                f"{length_km:.2f}",
                percent(length_km, total_length_km)
            ])

        # ✅ TOTAL ROW (NO HARDCODE)
        result.append([
            str(len(surface_lengths) + 1),
            "Total",
            f"{total_length_km:.2f}",
            percent(total_length_km, total_length_km, is_total=True)
        ])

        return result

    except Exception:
        return [
            ["S. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
            ["", "Data unavailable", "N/A", "N/A"]
        ]



def getFGDLivelihoodData(village_id):
    try:
        fgd_data = FGD_livelihood_summary.objects.filter(village_id=village_id).first()
        if not fgd_data:
            return {
                'cropping_pattern': [],
                'cropping_calendar': [],
                'challenges_in_agriculture': [],
                'livestock_and_allied_activities': [],
                'challenges_in_livestock': [],
                'departmental_support': []
            }
        
        def split_to_points(text):
            if not text:
                return []
            return [point.strip() for point in text.split(';') if point.strip()]
        
        return {
            'cropping_pattern': split_to_points(fgd_data.cropping_pattern),
            'cropping_calendar': split_to_points(fgd_data.cropping_calendar),
            'challenges_in_agriculture': split_to_points(fgd_data.challenges_in_agriculture),
            'livestock_and_allied_activities': split_to_points(fgd_data.livestock_and_allied_activities),
            'challenges_in_livestock': split_to_points(fgd_data.challenges_in_livestock),
            'departmental_support': split_to_points(fgd_data.departmental_support)
        }
    except Exception:
        return {
            'cropping_pattern': [],
            'cropping_calendar': [],
            'challenges_in_agriculture': [],
            'livestock_and_allied_activities': [],
            'challenges_in_livestock': [],
            'departmental_support': []
        }

def getVillageArea(village_id):
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return 0

    wfs_url = f"{GEOSERVER_BASE_URL}/assam/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": "assam:village_boundary",
        "outputFormat": "application/json",
        "CQL_FILTER": f"vill_id='{village_code}'"
    }

    try:
        response = requests.get(wfs_url, params=params, timeout=10)
        if response.status_code != 200:
            return 0

        geojson = response.json()
        features = geojson.get("features", [])
        
        if features:
            props = features[0].get("properties", {})
            area_sqkm = props.get("area_sqkm", 0) or 0
            return float(area_sqkm)
        
        return 0
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException):
        return 0
    except Exception:
        return 0


def getLULCData(village_id, workspace, layer, onlymax=False):
    from django.db import connection
    from collections import defaultdict
    from decimal import Decimal, ROUND_HALF_UP
    import requests

    # ---------------------------------------
    # Helper: Normalize Landuse Name
    # ---------------------------------------
    def normalize_landuse_name(name):
        if not name:
            return "Unknown"

        name = str(name).strip().lower()

        # Merge fallow into agriculture
        if name in ["fallow land", "agriculture land"]:
            return "Agriculture land"

        # Sentence case (first letter capital)
        return name.capitalize()

    # ---------------------------------------
    # Get village
    # ---------------------------------------
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        if onlymax:
            return "N/A"
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Landuse", bold_center_style_9), Paragraph("Area (sqm)", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "Village not found", "0", "0%"]
        ]

    # =======================================
    # 1️⃣ TRY DATABASE FIRST
    # =======================================
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'lulc'
                )
            """)

            if cursor.fetchone()[0]:

                cursor.execute("""
                    SELECT "Class_name", SUM("Area_SqM") as total_area
                    FROM public.lulc
                    WHERE "Vill_ID" = %s
                    GROUP BY "Class_name"
                """, [village_code])

                rows = cursor.fetchall()

                if rows:
                    class_area = defaultdict(float)

                    for class_name, area_sqm in rows:
                        if class_name and area_sqm:
                            clean_name = normalize_landuse_name(class_name)
                            class_area[clean_name] += float(area_sqm)

                    total_area = sum(class_area.values())

                    if total_area == 0:
                        if onlymax:
                            return "N/A"
                        return [
                           [Paragraph("S. No.", bold_center_style_9), Paragraph("Landuse", bold_center_style_9), Paragraph("Area (sqm)", bold_center_style_9), Paragraph("%", bold_center_style_9)],
                        ]

                    # ----------------------------------
                    # ONLY MAX MODE
                    # ----------------------------------
                    if onlymax:
                        max_land_use = max(class_area, key=class_area.get)
                        max_area = class_area[max_land_use]
                        percentage = round((max_area / total_area) * 100)
                        return f"{max_land_use} - {percentage}%"

                    # ----------------------------------
                    # NORMAL TABLE MODE
                    # ----------------------------------
                    result = [[Paragraph("S. No.", bold_center_style_9), Paragraph("Landuse", bold_center_style_9), Paragraph("Area (sqm)", bold_center_style_9), Paragraph("%", bold_center_style_9)]]

                    # Sort by descending area
                    sorted_classes = sorted(
                        class_area.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )

                    total_percent = Decimal("0")

                    for idx, (class_name, area) in enumerate(sorted_classes, start=1):
                        percent = (
                            Decimal(area) / Decimal(total_area) * 100
                        ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

                        total_percent += percent

                        result.append([
                            str(idx),
                            class_name,
                            f"{int(area):,}",
                            f"{percent}%"
                        ])

                    total_percent = min(Decimal("100"), total_percent)

                    result.append([
                        "",
                        "Total area",
                        f"{int(total_area):,}",
                        f"{total_percent}%"
                    ])

                    return result

    except Exception:
        pass  # Fall back to GeoServer

    # =======================================
    # 2️⃣ FALLBACK TO GEOSERVER (WFS)
    # =======================================
    wfs_url = f"{GEOSERVER_BASE_URL}/{workspace}/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": f"{workspace}:{layer}",
        "outputFormat": "application/json",
        "CQL_FILTER": f"vill_id='{village_code}'"
    }

    try:
        response = requests.get(wfs_url, params=params, timeout=10)

        if response.status_code != 200:
            if onlymax:
                return "N/A"
            return [
                ["S. No.", "Landuse", "Area (sqm)", "%"],
                ["", "Geoserver unavailable", "N/A", "N/A"]
            ]

        geojson = response.json()
        features = geojson.get("features", [])

        if not features:
            if onlymax:
                return "N/A"
            return [
                ["S. No.", "Landuse", "Area (sqm)", "%"],
                ["", "No data available", "0", "0%"]
            ]

        class_area = defaultdict(float)

        for feature in features:
            props = feature.get("properties", {})
            class_name = props.get("class_name")
            area_sqm = props.get("shape_area", 0.0) or 0.0

            clean_name = normalize_landuse_name(class_name)
            class_area[clean_name] += float(area_sqm)

        total_area = sum(class_area.values())

        if total_area == 0:
            if onlymax:
                return "N/A"
            return [
                ["S. No.", "Landuse", "Area (sqm)", "%"],
                ["", "No data available", "0", "0%"]
            ]

        if onlymax:
            max_land_use = max(class_area, key=class_area.get)
            max_area = class_area[max_land_use]
            percentage = round((max_area / total_area) * 100)
            return f"{max_land_use} - {percentage}%"

        result = [[Paragraph("S. No.", bold_center_style_9), Paragraph("Landuse", bold_center_style_9), Paragraph("Area (sqm)", bold_center_style_9), Paragraph("%", bold_center_style_9)]]

        sorted_classes = sorted(
            class_area.items(),
            key=lambda x: x[1],
            reverse=True
        )

        total_percent = Decimal("0")

        for idx, (class_name, area) in enumerate(sorted_classes, start=1):
            percent = (
                Decimal(area) / Decimal(total_area) * 100
            ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

            total_percent += percent

            result.append([
                str(idx),
                class_name,
                f"{int(area):,}",
                f"{percent}%"
            ])

        total_percent = min(Decimal("100"), total_percent)

        result.append([
            "",
            "Total area",
            f"{int(total_area):,}",
            f"{total_percent}%"
        ])

        return result

    except Exception:
        if onlymax:
            return "N/A"
        return [
            ["S. No.", "Landuse", "Area (sqm)", "%"],
            ["", "Data unavailable", "N/A", "N/A"]
        ]



def getDrinkingWaterSourceData(village_id):
    """
    Table 3.13: Source of drinking water for HHs
    """

    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        # Header (added S. No.)
        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Drinking Water Source", bold_center_style_9), Paragraph("No. of households",bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        water_sources = (
            households
            .exclude(drinking_water_source__isnull=True)
            .exclude(drinking_water_source__exact="")
            .annotate(source_n=Lower(Trim("drinking_water_source")))
            .values("source_n")
            .annotate(count=Count("source_n"))
            .order_by("-count")
        )

        valid_households = sum(row["count"] for row in water_sources)

        if valid_households == 0:
            table_data.append(["1", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        sr_no = 1

        for row in water_sources:
            source_name = row["source_n"].title()
            count = row["count"]
            percentage = round((count / valid_households) * 100)

            table_data.append([
                str(sr_no),
                source_name,
                str(count),
                f"{percentage}%"
            ])
            sr_no += 1

        total_pct = f"{round(sum(round((row['count'] / valid_households) * 100) for row in water_sources))}%"

        # Total row (no S. No.)
        table_data.append([
            "",
            "Total",
            str(valid_households),
            total_pct
        ])

        return table_data

    except Exception:
        return [
             [Paragraph("S. No.", bold_center_style_9), Paragraph("Drinking Water Source", bold_center_style_9), Paragraph("No. of households",bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]

    

def getJJMHouseConnect(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        table_data = [[Paragraph("S. No.", bold_center_style_9), Paragraph("JJM house connection", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]]

        yes_count = 0
        no_count = 0
        valid_households = 0

        for hh in households:
            if not hh.JJM_or_other_taped_water_connection:
                continue

            v = str(hh.JJM_or_other_taped_water_connection).strip().lower()

            if v in ["yes", "y", "true", "1"]:
                yes_count += 1
                valid_households += 1
            elif v in ["no", "n", "false", "0"]:
                no_count += 1
                valid_households += 1

        if valid_households == 0:
            table_data.append(["", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        yes_percentage = round((yes_count / valid_households) * 100)
        no_percentage = round((no_count / valid_households) * 100)
        total_pct = f"{yes_percentage + no_percentage}%"

        table_data.append(["1", "Yes", str(yes_count), f"{yes_percentage}%"])
        table_data.append(["2", "No", str(no_count), f"{no_percentage}%"])

        table_data.append([
            "",
            "Total",
            str(valid_households),
            total_pct
        ])

        return table_data

    except Exception as e:
        print("JJM error:", e)
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("JJM house connection", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]



from django.db.models.functions import Lower, Trim
from django.db.models import Count

def getAdequacyOfDrinkingWaterData(village_id):

    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Adequacy of drinking water", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        total_households = households.count()

        if total_households == 0:
            table_data.append(["1", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        yes_count = 0
        no_count = 0
        unknown_count = 0

        for hh in households:
            value = hh.adequate_water_supply

            if value is None:
                unknown_count += 1
                continue

            v = str(value).strip().lower()

            if not v:
                unknown_count += 1
            elif v in ["yes", "y", "adequate"]:
                yes_count += 1
            elif v in ["no", "n", "inadequate"]:
                no_count += 1
            else:
                unknown_count += 1

        # Percentages
        yes_pct = round((yes_count / total_households) * 100, 2)
        no_pct = round((no_count / total_households) * 100, 2)
        unknown_pct = round((unknown_count / total_households) * 100, 2)

        table_data.append(["1", "Yes", str(yes_count), f"{yes_pct}%"])
        table_data.append(["2", "No", str(no_count), f"{no_pct}%"])
        table_data.append(["3", "Unknown", str(unknown_count), f"{unknown_pct}%"])

        table_data.append([
            "",
            "Total",
            str(total_households),
            "100%"
        ])

        return table_data

    except Exception:
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Adequacy of drinking water", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]



def getSanitationFacilities(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Sanitation Facility", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        own_count = 0
        no_toilet_count = 0
        valid_households = 0

        for hh in households:
            if not hh.sanitation_facility:
                continue

            v = str(hh.sanitation_facility).strip().lower()

            if v == "own":
                own_count += 1
                valid_households += 1
            else:
                # Community Toilet, Open, or any other value
                no_toilet_count += 1
                valid_households += 1

        if valid_households == 0:
            table_data.append(["", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        own_pct = round((own_count / valid_households) * 100)
        no_toilet_pct = round((no_toilet_count / valid_households) * 100)
        total_pct = f"{own_pct + no_toilet_pct}%"

        table_data.append(["1", "Yes", own_count, f"{own_pct}%"])
        table_data.append(["2", "No", no_toilet_count, f"{no_toilet_pct}%"])

        table_data.append([
            "",
            "Total",
            valid_households,
            total_pct
        ])

        return table_data

    except Exception as e:
        print("❌ Sanitation error:", e)
        return [
            ["S. No.", "Sanitation Facility", "No of households", "%"],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]




def normalize_toilet_type(value):
    """
    Normalize toilet type into:
    - Single Pit
    - Twin Pit
    - Unknown
    """

    if value is None:
        return "Unknown"

    v = str(value).strip().lower()

    if not v or v in ["none", "null", "na", "n/a", "-"]:
        return "Unknown"

    if "single" in v and "pit" in v:
        return "Single Pit"

    if ("twin" in v or "double" in v) and "pit" in v:
        return "Twin Pit"


    return "Unknown"




def getHouseholdToiletsType(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)

        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Toilet type", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        toilet_counts = {
            'Single Pit': 0,
            'Twin Pit': 0,
            'Unknown': 0
        }

        valid_households = households.count()

        if valid_households == 0:
            table_data.append(["1", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        # Count types
        for hh in households:
            toilet_type = normalize_toilet_type(hh.type_of_toilet)

            # Safety check (prevents KeyError)
            if toilet_type not in toilet_counts:
                toilet_type = "Unknown"

            toilet_counts[toilet_type] += 1

        # Build table
        sr_no = 1
        total_pct = 0

        for toilet, count in toilet_counts.items():
            percent = round((count / valid_households) * 100, 2)
            total_pct += percent

            table_data.append([
                str(sr_no),
                toilet,
                str(count),
                f"{percent}%"
            ])
            sr_no += 1

        table_data.append([
            "",
            "Total",
            str(valid_households),
            "100%"
        ])

        return table_data

    except Exception as e:
        print("❌ Toilet table error:", e)
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Type of Household Toilet", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]



def normalize_sludge_disposal(value):
    if not value:
            return 'No de-sludge'

    v = value.lower()

    if 'nearby' in v and 'open' in v:
        return 'Nearby open area'

    if 'agriculture' in v:
        return 'Agriculture Land'

    if 'tanker' in v:
        return 'Collected by tanker'

    return 'No de-sludge'


def getDe_sludgeMaterial(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("De-sludge material disposal method", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        # ✅ ALL options declared upfront
        disposal_counts = {
            'Nearby open area': 0,
            'Agriculture Land': 0,
            'Collected by tanker': 0,
            'No de-sludge': 0
        }

        if total_households == 0:
            for i, key in enumerate(disposal_counts.keys(), start=1):
                table_data.append([str(i), key, "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data

        # -----------------------------
        # COUNTING
        # -----------------------------
        for hh in households:
            method = normalize_sludge_disposal(hh.sludge_be_disposed_type)
            if method in disposal_counts:
                disposal_counts[method] += 1

        # -----------------------------
        # BUILD TABLE (ALWAYS ALL ROWS)
        # -----------------------------
        sr_no = 1
        total_pct = 0
        for method, count in disposal_counts.items():
            percent = round((count / total_households) * 100)
            total_pct += percent

            table_data.append([
                str(sr_no),
                method.title(),
                str(count),
                f"{percent}%"
            ])
            sr_no += 1

        table_data.append([
            "",
            "Total",
            str(total_households),
            f"{total_pct}%"
        ])

        return table_data

    except Exception as e:
        print("❌ De-sludge error:", e)
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("De-sludge Material Disposal Method", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Nearby open area", "N/A", "N/A"],
            ["2", "Agriculture Land", "N/A", "N/A"],
            ["3", "Collected by tanker", "N/A", "N/A"],
            ["4", "No de-sludge", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]

    
def getElectricityconnection(vilage_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=vilage_id)

        # Header (added S. No.)
        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Electricity connection", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        electricity_qs = (
            households
            .exclude(house_has_electric_connection__isnull=True)
            .exclude(house_has_electric_connection__exact="")
            .annotate(electricity_n=Lower(Trim("house_has_electric_connection")))
            .values("electricity_n")
            .annotate(count=Count("electricity_n"))
        )

        yes_count = 0
        no_count = 0
        
        for row in electricity_qs:
            value = row["electricity_n"]
            count = row["count"]
            if value in ["yes", "y", "true", "1"]:
                yes_count += count
            elif value in ["no", "n", "false", "0"]:
                no_count += count
        
        valid_households = yes_count + no_count

        if valid_households == 0:
            table_data.append(["1", "No data available", "0", "0%"])
            table_data.append(["", "Total", "0", "0%"])
            return table_data
        
        yes_percentage = round((yes_count / valid_households) * 100)
        no_percentage = round((no_count / valid_households) * 100)
        total_pct = f"{yes_percentage + no_percentage}%"
        
        table_data.append(["1", "Yes", str(yes_count), f"{yes_percentage}%"])
        table_data.append(["2", "No", str(no_count), f"{no_percentage}%"])

        # Total row (no S. No.)
        table_data.append([
            "",
            "Total",
            str(valid_households),
            total_pct
        ])

        return table_data

    except Exception:
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Electricity connection", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["", "No data available", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]

def normalize_electricity_source(value):
    """
    Normalize electricity source into:
    - Grid
    - Solar
    - Grid & Solar
    - Unknown
    """

    if value is None:
        return 'Unknown'

    v = str(value).strip().lower()

    # Handle blanks and text-based nulls
    if not v or v in ['none', 'null', 'na', 'n/a', '-']:
        return 'Unknown'

    if 'grid' in v and 'solar' in v:
        return 'Grid & Solar'

    if 'grid' in v:
        return 'Grid'

    if 'solar' in v:
        return 'Solar'

    return 'Unknown'


from django.db.models import Count

def getElectricitySource(village_id):
    try:
        households = HouseholdSurvey.objects.filter(village_id=village_id)
        total_households = households.count()

        table_data = [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Source of electricity", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)]
        ]

        # Fixed categories (always shown)
        source_counts = {
            'Grid': 0,
            'Solar': 0,
            'Grid & Solar': 0,
            'Unknown': 0
        }

        if total_households == 0:
            sr_no = 1
            for key in source_counts:
                table_data.append([str(sr_no), key, "0", "0%"])
                sr_no += 1

            table_data.append(["", "Total", "0", "0%"])
            return table_data

        # -----------------------------
        # COUNTING
        # -----------------------------
        for hh in households:
            src = normalize_electricity_source(hh.source_of_electricity)

            if src not in source_counts:
                src = "Unknown"

            source_counts[src] += 1

        # -----------------------------
        # BUILD TABLE
        # -----------------------------
        sr_no = 1

        for source, count in source_counts.items():
            percent = round((count / total_households) * 100, 2)

            table_data.append([
                str(sr_no),
                source,
                str(count),
                f"{percent}%"
            ])
            sr_no += 1

        table_data.append([
            "",
            "Total",
            str(total_households),
            "100%"
        ])

        return table_data

    except Exception as e:
        print("Electricity source error:", e)
        return [
            [Paragraph("S. No.", bold_center_style_9), Paragraph("Source of electricity", bold_center_style_9), Paragraph("No. of households", bold_center_style_9), Paragraph("%", bold_center_style_9)],
            ["1", "Grid", "N/A", "N/A"],
            ["2", "Solar", "N/A", "N/A"],
            ["3", "Grid & Solar", "N/A", "N/A"],
            ["4", "Unknown", "N/A", "N/A"],
            ["", "Total", "N/A", "N/A"]
        ]



def draw_village_profile(elements,village_id):

    village_maps = VdmpVillageMapData.objects.filter(village_id=village_id).values(
        'village_id',
        'distribution_of_building',
        'road_infrastructure',
        'landuse',
        'flood_erosion',
        'essential_facilities',
        'electrical_infrastructure'
    ).first() or {}
    district_id = tblVillage.objects.filter(id=village_id).values_list(
        'gram_panchayat__circle__district_id',
        flat=True
    ).first()
    district_maps = {}
    if district_id:
        district_maps = VdmDistrictMapData.objects.filter(district_id=district_id).values(
            'wind_hazard',
            'earthquake_hazard'
        ).first() or {}
    map_file_fields = {**village_maps, **district_maps}


    styles = getSampleStyleSheet()
    heading = Paragraph("<a name='village_profile'/><b>3 Village Profile</b>", blue_heading)
    # add_heading_with_toc("Village Profile", blue_heading, level=1, elements=elements)
    elements.append(heading)
    # elements.append(Spacer(1, 3))


    heading = Paragraph("<b>3.1 Location details</b>", blue_sub_heading)
    # add_heading_with_toc("Location details", blue_sub_heading, level=2, elements=elements)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    data=getVillageLocationDetails(village_id)
    table = create_styled_table(data, [250,250], False, False, None, "Location Details")
    elements.append(table)
    elements.append(Spacer(1, 12))
    # --------------------- 3.2 ------------------
    custom_styles=[
       ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        # ('FONTNAME', (1, -2), (-1, -1), 'Helvetica-Bold'),
    ]
    heading = Paragraph("<b>3.2	Socio-economic profile</b>", blue_sub_heading) 
    # add_heading_with_toc("Socio economic profile", blue_sub_heading, level=2, elements=elements)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-1: Demographic profile", table_sub_title) 
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getVillageDemographic(village_id)
    table = create_styled_table(data, [40,260, 200], False, True, custom_styles, "Demographic Profile")
    elements.append(table)
    # -------------------- 3 2 ------------------
    # style to make number right align
    custom_styles=[
         ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
    ]
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-2: Socio-economic status of Head of Household", table_sub_title) 
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, summary = getSocialEconomicStatusData(village_id)
    table = create_styled_table(data, [40,150,40,40,40,50,50,50,40], False, True, custom_styles, "Socio Economic Status")
   
    elements.append(table)
    para=Paragraph("Note: Antyodaya (AAY), Above Poverty Line (APL), Annapurna Yojna (AY), Below Poverty Line (BPL), Priority Household (PHH).", notes_style)
    elements.append(para)
    elements.append(Spacer(1, 6))
    points = [
        f"Below Poverty Line (BPL {summary['bpl_percent']}%) followed by Priority Household (PHH-{summary['phh_percent']}%), and Antyodaya Anna Yojana (AAY {summary['aay_percent']}%).",
        f"{summary['widow_percent']}% of households are headed by widows.",
        f"{summary['married_male_percent']}% of households are headed by married males."
    ]

    bullet_items = ListFlowable(
        [ListItem(Paragraph(text, styles["Normal"])) for text in points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )

    elements.append(bullet_items)
    elements.append(Spacer(1, 12))

    
    # -------------------- 3.3 ----------------
    custom_styles=[
         ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    sub_title=Paragraph("Table 3-3: Household level agriculture land holding", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, land_stats = getAgricultureLandHoldingData(village_id)
    table = create_styled_table(data, [40,235, 45,45,45,45,45], False, True, custom_styles, "Agriculture Land Holding")
    elements.append(table)
    para=Paragraph("Note: 1 Bigha = 0.68 Hectare", notes_style)
    elements.append(para)
    
    
    # Define bullet point content
    points = [
     
        f"Only {land_stats['owned_land_percent']}% of the community owns agricultural land. This reflects a low overall economic status, limited asset ownership, and consequently reduced access to formal credit and financial services. Farmers using leased land get informal credit and financial support from small aggregators.",
        # f"Though the community in general doesn’t keep track of exact expenditure, the major expenditure (43%) goes for daily expenditure and about 10% each for agriculture, festival and house repair."
    ]
    
     #Create bullet items
    bullet_items = ListFlowable(
        [ListItem(Paragraph(text, styles["Normal"])) for text in points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )

    # Append to your PDF elements
    elements.append(Spacer(1, 12))  # Add spacing before the list
    elements.append(bullet_items)

    # -------------------------- 3 4 ---------------
    custom_styles=[
         ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Table 3-4: Annual household income", table_sub_title) 
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, income_stats = getIncomeGroupData(village_id)
    table = create_styled_table(data, [40,155,150,155], False, True, custom_styles, "Annual Household Income")
    elements.append(table)
    elements.append(Spacer(1, 12))

      # Define bullet point content
    points = [
        f"Low income dominance - {income_stats['low_income_percent']}% of the household has annual income of about INR 1.5 lakhs.",
    ]
    
     #Create bullet items
    bullet_items = ListFlowable(
        [ListItem(Paragraph(text, styles["Normal"])) for text in points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )

    # Append to your PDF elements
   
    elements.append(bullet_items)
    
    #-------------------- 3 5-----------------
    custom_styles=[
       ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-5: Average expenditure break down for household", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getAverageExpenditureBreakdownData(village_id)
    table = create_styled_table(data, [40,360,100], False, True, custom_styles, "Average Expenditure Breakdown")
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(PageBreak())    
    
    # ------------------- 3 6 ----------
    sub_title=Paragraph("Table 3-6: Household debit liability in the last 5 years", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getHouseholdDebtLiabilityData(village_id)
    table = create_styled_table(data, [40,153.333,153.333,153.333], False, True, custom_styles, "Household Debt Liability")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # -------------------
    
    # 💡 Define custom merges and styles
    custom_styles = [
        ('SPAN', (1, 0), (1, 1)),  
        ('SPAN', (2, 0), (-1, 0)),  
        ('ALIGN', (1, 0), (2, 0), 'CENTER'),
        ('ALIGN', (0, 0), (0, 1), 'CENTER'),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ('SPAN', (0, 0), (0, 1)),  
        ('BACKGROUND', (0, 1), (-1, 1), tb_header_bg),
       ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
         ('ALIGN', (2, 2), (-1, -1), 'RIGHT'),
        
    ]
    
    heading = Paragraph("<b>3.3	Livelihood profile </b>", blue_sub_heading)
    elements.append(heading)
    sub_title=Paragraph("Table 3-7: Livelihood distribution (primary economic activity)", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 12))
    data=getPrimaryLivelihoodDistributionData(village_id)
    
    table = create_styled_table(data, [40,240, 100,120], True, True, custom_styles, "Primary Livelihood Distribution (primary economic activity)")
    elements.append(table)
    elements.append(Spacer(1, 6))
    
    #------------------------
    sub_title=Paragraph("Table 3-8: Livelihood distribution (secondary economic activity)", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getPrimaryLivelihoodDistributionData(village_id, 'secondary')
    table = create_styled_table(data, [40,240, 100, 120], True, True, custom_styles, "Secondary Livelihood Distribution (secondary economic activity)")
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(PageBreak())
    
    # ------------------------
    custom_styles=[
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
         ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]
    sub_title=Paragraph("Table 3-9: Number of crops cultivated", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getCropCultivationData(village_id)
    table = create_styled_table(data, [40,200, 160, 100], False, True, custom_styles, "Crop Cultivation")
    elements.append(table)
    elements.append(Spacer(1, 12))
    # Define bullet point content
    points = [
        f"	Key crops cultivated include paddy, potato, maize, mustard, jute, sugarcane, vegetables, lentils, and white wheat. ",
        f"	About 10% of farmers avail agricultural insurance. People are not aware of agricultural insurance facilities.",
       
    ]
    
     #Create bullet items
    bullet_items = ListFlowable(
        [ListItem(Paragraph(text, styles["Normal"])) for text in points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )

    # Append to your PDF elements
    elements.append(Spacer(1, 12))  # Add spacing before the list
    elements.append(bullet_items)
    
    # -----------------------
    elements.append(Spacer(1, 12))
    custom_styles2 = [
        # Merge header cells
        ('SPAN', (2, 0), (3, 0)),  # Merge 'HH with big cattle' and '%'
        ('SPAN', (4, 0), (5, 0)),  # Merge 'HH with small cattle' and '%'
        ('SPAN', (0, 0), (0, 1)),  # Merge S. No.cells
        ('SPAN', (1, 0), (1, 1)),  # Merge Count cells

        # Center align all text
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND',(0,1),(-1,1),tb_header_bg),
        
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
         ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    sub_title=Paragraph("Table 3-10: Household with Livestock", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getLivestockOwnershipData(village_id)
    table = create_styled_table(data, [40,90, 110, 50, 110, 100], True, True, custom_styles2, "Livestock Ownership")
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Cropping Pattern and Cropping calendar
    fgd_data = getFGDLivelihoodData(village_id)
    
    sub_title = Paragraph("Cropping Pattern", bold_style)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    if fgd_data['cropping_pattern']:
        bullet_items = ListFlowable(
            [ListItem(Paragraph(text, styles["Normal"])) for text in fgd_data['cropping_pattern']],
            bulletType='bullet',
            start='•',
           leftIndent=20,
            bulletFontName='Helvetica',
            bulletFontSize=10
        )
        elements.append(bullet_items)
    else:
        elements.append(Paragraph("No data available", styles["Normal"]))
    elements.append(Spacer(1, 12))

    sub_title = Paragraph("Cropping Calendar", bold_style)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    if fgd_data['cropping_calendar']:
        bullet_items = ListFlowable(
            [ListItem(Paragraph(text, styles["Normal"])) for text in fgd_data['cropping_calendar']],
            bulletType='bullet',
            start='•',
           leftIndent=20,
            bulletFontName='Helvetica',
            bulletFontSize=10
        )
        elements.append(bullet_items)
    else:
        elements.append(Paragraph("No data available", styles["Normal"]))
    elements.append(Spacer(1, 12))

    
    

    sub_title = Paragraph("Livestock and Allied Activities", bold_style)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    if fgd_data['livestock_and_allied_activities']:
        bullet_items = ListFlowable(
            [ListItem(Paragraph(text, styles["Normal"])) for text in fgd_data['livestock_and_allied_activities']],
            bulletType='bullet',
            start='•',
           leftIndent=20,
            bulletFontName='Helvetica',
            bulletFontSize=10
        )
        elements.append(bullet_items)
    else:
        elements.append(Paragraph("No data available", styles["Normal"]))
    elements.append(Spacer(1, 12))



    sub_title = Paragraph("Departmental support", bold_style)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    if fgd_data['departmental_support']:
        bullet_items = ListFlowable(
            [ListItem(Paragraph(text, styles["Normal"])) for text in fgd_data['departmental_support']],
            bulletType='bullet',
            start='•',
           leftIndent=20,
            bulletFontName='Helvetica',
            bulletFontSize=10
        )
        elements.append(bullet_items)
    else:
        elements.append(Paragraph("No data available", styles["Normal"]))
    elements.append(Spacer(1, 12))
    #--------------------------------
    heading = Paragraph("<b>3.4	Asset profile </b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    custom_styles=[
       ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    sub_title=Paragraph("Table 3-11: Distribution of house by typology", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getHousingTypologyData(village_id)
    table = create_styled_table(data, [40,120,85,85,85,85], False, True, custom_styles, "Housing Typology")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    p=Paragraph("Note: ", notes_style)
    elements.append(p)
    
    # Kachcha House definitions
    p = Paragraph("Kachcha House includes-", bold_style)
    elements.append(p)
    elements.append(Spacer(1, 3))
    
    kachcha_types = [
        "(Mud House): Grass/leaves/plastic & cow dung/mud+Tin+Mud",
        "(Ikra House): Wood, Bamboo & cow dung/mud+Tin+Mud",
        "(Ikra House): Bamboo+ Straw + Cement Plaster+GI Sheet+Cement",
        "(Chang House): Bamboo+GI Sheet+Bamboo+ Wood (on RCC Stilt)",
        "(Chang House): Brick + Cement+GI Sheet+Brick, cement and steel (on Stilt)",
        "Bamboo House: Bamboo + Straw/ Jati+GI Sheet+Bamboo +Wood (on Bamboo Stilt)",
        "Tin House: Tin+Tin+Mud",
        "Tin House: Tin+Tin+Cement"
    ]
    
    for house_type in kachcha_types:
        p = Paragraph(house_type, indented_style)
        elements.append(p)
        elements.append(Spacer(1, 3))
    
    # Semi pucca house definitions
    p = Paragraph("Semi pucca house includes-", bold_style)
    elements.append(p)
    elements.append(Spacer(1, 3))
    
    semi_pucca_types = [
        "Semi Pucca (Mud Floor): Brick with Cement+Tin+Mud",
        "Semi Pucca (Cement Floor): Brick with Cement+Tin+Cement"
    ]
    
    for house_type in semi_pucca_types:
        p = Paragraph(house_type, indented_style)
        elements.append(p)
        elements.append(Spacer(1, 3))
    
    # Pucca house definitions
    p = Paragraph("Pucca house includes-", bold_style)
    elements.append(p)
    elements.append(Spacer(1, 3))
    
    p = Paragraph("(Pucca house): Brick with Cement+Concrete+Cement", indented_style)
    elements.append(p)
    elements.append(Spacer(1, 3))
        
    # ---------------------
    # Image from the geoserver 
    elements.append(Spacer(1, 12))
    
    # Add geoserver image with border
   
    image_height = page_height * 0.8

    #img from geoserver
    # layers = ['assam:building_footprint']
    # # geoserver_image_path = get_geoserver_image_path(layers, width=500, height=int(image_height),village_id=village_id)
    # img, actual_width, actual_height = get_geoserver_image_as_rl_image(
    #     layers, village_id=village_id, max_width=500
    # )

    # if img:
    #     # img is already a ReportLab Image object - use directly
    #     img_table = ReportLabTable([[img]])
    #     img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))
    #     elements.append(img_table)
    #     # os.unlink(image_path)

    #img from the model
    img_field = map_file_fields.get('distribution_of_building')
    if img_field:
        # Get the full file path (works for local storage)
        img_path = f"{MEDIA_ROOT}/{img_field}"

        # Create a ReportLab Image object
        img = ReportLabImage(img_path, width=450, height=image_height)  # adjust size

        # Put the Image object inside a table
        img_table = ReportLabTable([[img]])
        img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(img_table)

        elements.append(Spacer(1, 12))
        sub_title=Paragraph("Figure 3-1: Distribution of residential building", image_title)
        elements.append(sub_title)
        elements.append(Spacer(1, 12))
    else:
        #img from geoserver
        layers = ['assam:building_footprint']
        # geoserver_image_path = get_geoserver_image_path(layers, width=500, height=int(image_height),village_id=village_id)
        img, actual_width, actual_height = get_geoserver_image_as_rl_image(
            layers, village_id=village_id, max_width=500
        )

        if img:
            # img is already a ReportLab Image object - use directly
            img_table = ReportLabTable([[img]])
            img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))
            elements.append(img_table)
            # os.unlink(image_path)
   
    
        elements.append(Spacer(1, 12))
        sub_title=Paragraph("Figure 3-1: Distribution of residential building", image_title)
        elements.append(sub_title)
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Image is not available for this village", notes_style))
        
        # Add legends horizontally with text labels
        # elements.append(Spacer(1, 6))
        # elements.append(Paragraph('Residential building Legends', Legend_heading))
        # elements.append(Spacer(1, 6))
        # elements.append(Paragraph('<font color="#a83800">■</font> -- buildings', normal_style))


    # legend_layers = ['assam:household']
    # legend_paths = get_geoserver_legend_path(legend_layers, width=20, height=20)
    # if legend_paths:
    #     from reportlab.platypus import Table
    #     legend_data = []
    #     legend_labels = []
    #     for i, legend_path in enumerate(legend_paths):
    #         if legend_path and i < len(legend_layers):
    #             legend_img = Image(legend_path, width=20, height=20)
    #             legend_data.append(legend_img)
    #             layer_name = legend_layers[i].split(':')[1].replace('_', ' ').title()
    #             legend_labels.append(Paragraph(layer_name, styles['Normal']))
    #     if legend_data and len(legend_data) == len(legend_labels):
    #         legend_table = Table([legend_data, legend_labels])
    #         elements.append(Spacer(1, 12))
    #         elements.append(legend_table)
    
    # ------------------------
    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Table 3-12: Access to social media and information", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getDigitalAccessData(village_id)
    table = create_styled_table(data, [40,200, 130, 130], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Additional asset profile bullet points with dynamic data
    digital_data = getDigitalAccessData(village_id)
    mobile_pct = digital_data[1][2] if len(digital_data) > 1 else "0%"
    tv_mobile_pct = digital_data[3][2] if len(digital_data) > 3 else "0%"
    
    # asset_points = [
    #     f"About {mobile_pct} household has mobile connectivity and access to internet. But use for entertainment. Doesn't have the knowledge to access information useful for farming or relief entitlement",
    #     f"Only three household responded they have solar as alternate electricity source.",
    #     f"All household has toilet and access to drinking water. However, 76% of the household has Kachcha structure as toilet (made of tin, leaves/cloth) and just a pit to dispose the waste. Rest of the house has toilet with double pit septic tank but majority of these tanks are poorly maintained.",
    #     f"Household assets include very basic furniture like wooden coat, wooden table, plastic chairs and kitchen utensils. Community store food grains at home."
    # ]
    
    # asset_bullet_items = ListFlowable(
    #     [ListItem(Paragraph(text, styles["Normal"])) for text in asset_points],
    #     bulletType='bullet',
    #     start='•',
    #     leftIndent=20,
    #     bulletFontName='Helvetica',
    #     bulletFontSize=10
    # )
    
    # elements.append(asset_bullet_items)
    
    
    #------------------------ New table ----------------
    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Table 3-13: Source of drinking water for Household", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getDrinkingWaterSourceData(village_id)

    table = create_styled_table(data, [50,170,140, 140], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-14: Adequacy of drinking water", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getAdequacyOfDrinkingWaterData(village_id)

    table = create_styled_table(data,  [50,150,150, 150], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-15: No of houses connected with JJM", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getJJMHouseConnect(village_id)

    table = create_styled_table(data,  [50,150,150, 150], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-16: Number of houses with sanitation facilities", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getSanitationFacilities(village_id)

    table = create_styled_table(data,  [50,150,150, 150], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-17: Type of household toilets", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getHouseholdToiletsType(village_id)

    table = create_styled_table(data,  [50,150,150, 150], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-18: Disposal of de-sludge material", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getDe_sludgeMaterial(village_id)

    table = create_styled_table(data,  [50,250,100, 100], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-19: Electricity connection", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getElectricityconnection(village_id)

    table = create_styled_table(data,  [50,250,100, 100], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    sub_title=Paragraph("Table 3-20: Source of electricity", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getElectricitySource(village_id)

    table = create_styled_table(data,  [50,250,100, 100], False, True, custom_styles, "Digital Access")
    elements.append(table)
    elements.append(Spacer(1, 12))

    
    # ---------------------
    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Table 3-21: Public assets in the village", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getPublicAssetsData(village_id)
    
    # Fix data structure for consistent columns
    if len(data) > 0 and len(data[0]) == 1:
        # Pad first row to match column count
        data[0] = data[0] + [""] * 7  # Make it 8 columns total
    
    custom_styles3=[
         ('SPAN', (0, 0), (-1, 0)),  
         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
          ('ALIGN', (1, 2), (1, -1), 'LEFT'),
         ("BACKGROUND",(0,1),(-1,1),tb_header_bg),
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
         
           ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
           ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    
    table = create_styled_table(data, [40,90,60,60,60,60,60,70,60], True, True, custom_styles3, "Public Assets")
    elements.append(table)
    elements.append(Spacer(1, 12))
   
    image_height = page_height * 0.70
    
    img_field = map_file_fields.get('essential_facilities')
    if img_field:
        # Get the full file path (works for local storage)
        img_path = f"{MEDIA_ROOT}/{img_field}"

        # Create a ReportLab Image object
        img = ReportLabImage(img_path, width=450, height=image_height)  # adjust size

        # Put the Image object inside a table
        img_table = ReportLabTable([[img]])
        img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(img_table)

        elements.append(Spacer(1, 6))
        sub_title=Paragraph("Figure 3-2: Essential Facilities", image_title)
        elements.append(sub_title)
        elements.append(PageBreak() )

    else:
        sub_title=Paragraph("Figure 3-2: Essential Facilities", image_title)
        elements.append(sub_title)
        elements.append(Paragraph("Image is not available for this village", notes_style))

    # --------------------
    # elements.append(Spacer(1, 12))

    heading = Paragraph("<b>3.5	Infrastructure</b>", blue_sub_heading)
    elements.append(heading)
    # elements.append(Spacer(1, 6))
    heading = Paragraph("<b>3.5.1 Road Infrastructure</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-22: Road length by typology ", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    custom_styles4=[
      
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
          ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
          
    ]
    data=getRoadLengthByTypologyData(village_id,'assam','road_network')
    table = create_styled_table(data, [40,160,150,150], False, True, custom_styles4, "Road Length by Typology")
    elements.append(table)
    elements.append(Spacer(1, 12))
    # Add geoserver image with border
    
    image_height = page_height * 0.75
    

    #img from the model
    img_field = map_file_fields.get('road_infrastructure')
    if img_field:
        # Get the full file path (works for local storage)
        img_path = f"{MEDIA_ROOT}/{img_field}"

        # Create a ReportLab Image object
        img = ReportLabImage(img_path, width=450, height=image_height)  # adjust size

        # Put the Image object inside a table
        img_table = ReportLabTable([[img]])
        img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(img_table)

        elements.append(Spacer(1, 12))
        sub_title=Paragraph("Figure 3-3: Road infrastructure map", image_title)
        elements.append(sub_title)
        elements.append(PageBreak())
    else:
        #img from geoserver
        layers = ['assam:road_network']
        img, actual_width, actual_height = get_geoserver_image_as_rl_image(
        layers, village_id=village_id, max_width=500
        )
        if img:
            # img is already a ReportLab Image object - use directly
            img_table = ReportLabTable([[img]])
            img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))
            elements.append(img_table)    

            elements.append(Spacer(1, 12))
            sub_title=Paragraph("Figure 3-3: Road infrastructure map", image_title)
            elements.append(sub_title)
            
            elements.append(Paragraph("Image is not available for this village", notes_style))
    


            # # Road network legends with colored lines (ReportLab doesn't support text rotation in Paragraph)
            # elements.append(Paragraph('<font color="#db1e2a">━━━━━━━━━━</font> Bituminous', normal_style))
            # elements.append(Paragraph('<font color="#f67872">━━━━━━━━━━</font> Cement Block', normal_style))
            # elements.append(Paragraph('<font color="#796868">━━━━━━━━━━</font> Earthen', normal_style))
            # elements.append(Paragraph('<font color="#000000">━━━━━━━━━━</font> Village Boundary', normal_style))
            
    # Add legends horizontally with text labels
    
    # legend_layers = ['assam:road_network']
    # legend_paths = get_geoserver_legend_path(legend_layers ,width=150, height=100)
    # if legend_paths:
    #     from reportlab.platypus import Table
    #     legend_data = []
    #     legend_labels = []
    #     for i, legend_path in enumerate(legend_paths):
    #         if legend_path and i < len(legend_layers):
    #             legend_img = Image(legend_path, width=150, height=100)
    #             legend_data.append(legend_img)
    #             layer_name = legend_layers[i].split(':')[1].replace('_', ' ').title()
    #             legend_labels.append(Paragraph(layer_name, styles['Normal']))
    #     if legend_data and len(legend_data) == len(legend_labels):
    #         legend_table = Table([legend_data, legend_labels])
    #         elements.append(Spacer(1, 12))
    #         elements.append(legend_table)
    
    elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 6))
    heading = Paragraph("<b>3.5.2 Power Infrastructure</b>", blue_level3_heading)
    elements.append(heading)
    # ----------------------------------
    sub_title=Paragraph("Table 3-23: Power infrastructure ", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))

    
    data=getPowerInfrastructureData_Total(village_id)
    table = create_styled_table(data, [40,360,100], False, True, custom_styles4, "Power Infrastructure")
    elements.append(table)
    elements.append(Spacer(1, 12))

    image_height = page_height * 0.64

    #img from model if not available get from geoserver
    img_field = map_file_fields.get('electrical_infrastructure')
    if img_field:
        # Get the full file path (works for local storage)
        img_path = f"{MEDIA_ROOT}/{img_field}"

        # Create a ReportLab Image object
        img = ReportLabImage(img_path, width=450, height=image_height)  # adjust size

        # Put the Image object inside a table
        img_table = ReportLabTable([[img]])
        img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(img_table)
        elements.append(Spacer(1, 12))
        sub_title=Paragraph("Figure 3-4: Power infrastructure", image_title)
        elements.append(sub_title)
        elements.append(PageBreak())

    else:
        sub_title=Paragraph("Figure 3-4: Power infrastructure", image_title)
        elements.append(sub_title)
        elements.append(Paragraph("Image is not available for this village", notes_style))

    #  ------------------------- 
    
    elements.append(Spacer(1, 12))
    heading = Paragraph("<b>3.6	Access to other facilities</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-24: Access to other facilities", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getFacilityAccessData(village_id)
    table = create_styled_table(data, [40,230, 230], False, True, None, "Facility Access")
    elements.append(table)

    # ------------------------
    elements.append(Spacer(1, 12))
    heading = Paragraph("<b>3.7	Landuse</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3-25: Landuse", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getLULCData(village_id,'assam','lulc')
    table = create_styled_table(data, [40,180, 140, 140], False, True, custom_styles, "Land Use Classification")
    elements.append(table)
    elements.append(Spacer(1, 12))
    # Add geoserver image with border
 
    #img from geoserver
    # layers = ['assam:lulc']
    # img, actual_width, actual_height = get_geoserver_image_as_rl_image(
    #     layers, village_id=village_id, max_width=500
    # )
    # if img:
    #     # img is already a ReportLab Image object - use directly
    #     img_table = ReportLabTable([[img]])
    #     img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))
    #     elements.append(img_table)
    
    #img from the model
    image_height = page_height * 0.75

    img_field = map_file_fields.get('landuse')
    if img_field:
        # Get the full file path (works for local storage)
        img_path = f"{MEDIA_ROOT}/{img_field}"

        # Create a ReportLab Image object
        img = ReportLabImage(img_path, width=450, height=image_height)  # adjust size

        # Put the Image object inside a table
        img_table = ReportLabTable([[img]])
        img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))

        elements.append(img_table)
    else:
        #img from geoserver

        elements.append(Paragraph("Image is not available for this village", notes_style))

    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Figure 3-5: Landuse map", image_title)
    elements.append(sub_title)
    
    # Add legends horizontally with text labels
    # legend_layers = ['assam:lulc']
    # legend_paths = get_geoserver_legend_path(legend_layers,width=500, height=400)
    # if legend_paths:
    #     from reportlab.platypus import Table
    #     legend_data = []
    #     legend_labels = []
    #     for i, legend_path in enumerate(legend_paths):
    #         if legend_path and i < len(legend_layers):
    #             legend_img = Image(legend_path, width=500, height=400)
    #             legend_data.append(legend_img)
    #             layer_name = legend_layers[i].split(':')[1].replace('_', ' ').title()
    #             legend_labels.append(Paragraph(layer_name, styles['Normal']))
    #     if legend_data and len(legend_data) == len(legend_labels):
    #         legend_table = Table([legend_data, legend_labels])
    #         elements.append(Spacer(1, 12))
    #         elements.append(legend_table)
    
    
