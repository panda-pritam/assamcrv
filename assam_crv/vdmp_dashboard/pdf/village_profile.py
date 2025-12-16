from reportlab.platypus import Paragraph, Spacer,  ListFlowable, ListItem, Image

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image as RLImage, Table as ReportLabTable, TableStyle
import os
from reportlab.platypus import Image as ReportLabImage, Table as ReportLabTable, TableStyle
from reportlab.lib import colors
from .global_styles import blue_level3_heading, blue_heading,table_sub_title,blue_sub_heading,image_title,notes_style,tb_header_bg,Legend_heading,indented_style,bold_style,normal_style, bold_center_style,srNoStyle
from .utils.table import create_styled_table
from .utils.geoserverLayerImage import  get_geoserver_legend_path,get_geoserver_image_as_rl_image

from ..models import VillageListOfAllTheDistricts,HouseholdSurvey,Commercial,Critical_Facility,VillageRoadInfo
from village_profile.models import tblVillage
from .dummy_data import getFacilityAccessData
from vdmp_dashboard.models import HouseholdSurvey,VillageRoadInfo, VillageRoadInfoErosion,Critical_Facility,ElectricPole,Transformer

from django.db.models import Sum, Count

import requests
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus import Table as ReportLabTable
from .village_summary import VILLAGE_SUMMARY_DATA

styles = getSampleStyleSheet()
page_width, page_height = A4


# ------------------ data query -------------------------------

from shapefiles.models import ShapefileElectricPole ,ShapefileTransformer

def getPowerInfrastructureData_Total(village_id):
    try:
        # Get village object
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
        electric_data_total = ShapefileElectricPole.objects.filter(vill_id=village_code).count()
        transformer_data_total = ShapefileTransformer.objects.filter(vill_id=village_code).count()
        return [
            [Paragraph("Sr. No.", bold_center_style), Paragraph("Type", bold_center_style), Paragraph("Number")],
            ["1", Paragraph("Electric post and network", normal_style), str(electric_data_total)],
            ["2", Paragraph("Transformer", normal_style), str(transformer_data_total)],
        ]
    except Exception:
        return [
            [Paragraph("Sr. No.", bold_center_style), Paragraph("Type", bold_center_style), Paragraph("Number")],
             ["1", Paragraph("Electric post and network", normal_style), "N/A"],
            ["2", Paragraph("Transformer", normal_style), "N/A"],
        ]




def getVillageLocationDetails(village_id):
    try:
        village_data = VillageListOfAllTheDistricts.objects.select_related('village__gram_panchayat__circle__district').get(village=village_id)
        return [
          
            [Paragraph("Village", bold_style), Paragraph(village_data.village.name or "N/A", normal_style)],
            [Paragraph("Block", bold_style), Paragraph(village_data.block_name or "N/A", normal_style)],
            # [Paragraph("Revenue Circle", bold_style), Paragraph(village_data.revenue_circle or "N/A", normal_style)],
            [Paragraph("Circle", bold_style), Paragraph(village_data.village.gram_panchayat.circle.name or "N/A", normal_style)],
            [Paragraph("District", bold_style), Paragraph(village_data.village.gram_panchayat.circle.district.name or "N/A", normal_style)],
            # [Paragraph("District Code", bold_style), Paragraph(village_data.district_code or "N/A", normal_style)],
            # [Paragraph("Village Code", bold_style), Paragraph(village_data.village_code or "N/A", normal_style)],
            [Paragraph("Distance from Headquarter (km)", bold_style), Paragraph(str(village_data.distance_from_headquarter) if village_data.distance_from_headquarter else "N/A", normal_style)],
            [Paragraph("Total Area (sq km)", bold_style), Paragraph(str(village_data.total_area) if village_data.total_area else "N/A", normal_style)],
            [Paragraph("Average Elevation (m)", bold_style), Paragraph(str(village_data.average_elevation) if village_data.average_elevation else "N/A", normal_style)],
            [Paragraph("Topography", bold_style), Paragraph(village_data.topography or "N/A", normal_style)],
            [Paragraph("State", bold_style), Paragraph("Assam", normal_style)]
        ]
    except VillageListOfAllTheDistricts.DoesNotExist:
        return [
          
            [Paragraph("Village Name", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Block", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("Revenue Circle", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("District", bold_style), Paragraph("N/A", normal_style)],
            [Paragraph("State", bold_style), Paragraph("Assam", normal_style)]
        ]


def getVillageDemographic(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        def safe_int(value):
            try:
                return int(value) if value and value.strip() else 0
            except (ValueError, AttributeError):
                return 0
        
        total_males = sum(safe_int(h.number_of_males_including_children) for h in households)
        total_females = sum(safe_int(h.number_of_females_including_children) for h in households)
        total_population = total_males + total_females
        total_households = households.count()
        
        avg_family_size = round(total_population / total_households, 1) if total_households > 0 else 0
        male_female_ratio = round((total_males / total_females) * 1000) if total_females > 0 else 0
        
        VILLAGE_SUMMARY_DATA['total_population']=total_population
        VILLAGE_SUMMARY_DATA['total_households']=total_households
        
        return [
            ['Sr. No.',"Household Characteristic", "Total"],
            ['1',"No of Males", f"{total_males:,}"],
            ['2',"No of Females", f"{total_females:,}"],
            ['3',"Total Population", f"{total_population:,}"],
            ["4","Number of Households", f"{total_households:,}"],
            ['5',"Absentee House", "N/A"],
            ['6',"Average Family Size", str(avg_family_size)],
            ['7',"Male-Female Ratio", str(male_female_ratio)]
        ]
    except Exception:
        return [
            ['Sr. No.',"Household Characteristic", "Total"],
            ["1","No of Males", "N/A"],
            ["2","No of Females", "N/A"],
            ["3","Total Population", "N/A"],
            ["4","Number of Households", "N/A"],
            ["5","Absentee House", "N/A"],
            ["6","Average Family Size", "N/A"],
            ["7","Male-Female Ratio", "N/A"]
        ]

def getSocialEconomicStatusData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        # Initialize counters
        data = {
            'Married Male': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Single Man': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Single Women': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0},
            'Widow': {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0}
        }
        
        # Count households by social_status and economic_status
        for hh in households:
            social = hh.social_status or ''
            economic = hh.economic_status or ''
            
            # Map social status
            if 'married' in social.lower() and 'male' in social.lower():
                social_key = 'Married Male'
            elif 'single' in social.lower() and 'man' in social.lower():
                social_key = 'Single Man'
            elif 'single' in social.lower() and 'women' in social.lower():
                social_key = 'Single Women'
            elif 'widow' in social.lower():
                social_key = 'Widow'
            else:
                social_key = 'Married Male'  # Default
            
            # Map economic status - check for both abbreviations and full forms
            economic_key = None
            if economic.upper() == 'AAY' or 'antyodaya' in economic.lower():
                economic_key = 'AAY'
            elif economic.upper() == 'APL' or 'above poverty line' in economic.lower():
                economic_key = 'APL'
            elif economic.upper() == 'AY' or 'annapurna yojna' in economic.lower():
                economic_key = 'AY'
            elif economic.upper() == 'BPL' or 'below poverty line' in economic.lower():
                economic_key = 'BPL'
            elif economic.upper() == 'PHH' or 'priority household' in economic.lower():
                economic_key = 'PHH'
            
            if economic_key:
                data[social_key][economic_key] += 1
        
        # Calculate totals and percentages
        result = [["Sr. No.", "Social/Economic Status Household", "AAY", "APL", "AY", "BPL", "PHH", "Total", "%"]]
    
        total_households = households.count()
        col_totals = {'AAY': 0, 'APL': 0, 'AY': 0, 'BPL': 0, 'PHH': 0}
        
        sr_no = 1
        for social_status, counts in data.items():
            row_total = sum(counts.values())
            row_percent = f"{round(row_total/total_households*100)}%" if total_households > 0 else "0%"
            
            result.append([
                str(sr_no),
                social_status,
                str(counts['AAY']),
                str(counts['APL']),
                str(counts['AY']),
                str(counts['BPL']),
                str(counts['PHH']),
                str(row_total),
                row_percent
            ])
            sr_no += 1
            
            # Add to column totals
            for key in col_totals:
                col_totals[key] += counts[key]
        
        # Add total row
        result.append([
            str(sr_no),
            "Total",
            str(col_totals['AAY']),
            str(col_totals['APL']),
            str(col_totals['AY']),
            str(col_totals['BPL']),
            str(col_totals['PHH']),
            str(total_households),
            ""
        ])
        
        # Add percentage row
        result.append([
            str(sr_no + 1),
            "%",
            f"{round(col_totals['AAY']/total_households*100)}%" if total_households > 0 else "0%",
            f"{round(col_totals['APL']/total_households*100)}%" if total_households > 0 else "0%",
            f"{round(col_totals['AY']/total_households*100)}%" if total_households > 0 else "0%",
            f"{round(col_totals['BPL']/total_households*100)}%" if total_households > 0 else "0%",
            f"{round(col_totals['PHH']/total_households*100)}%" if total_households > 0 else "0%",
            "",
            ""
        ])
        
        # Calculate summary stats
        summary = {
            'bpl_percent': round(col_totals['BPL']/total_households*100) if total_households > 0 else 0,
            'phh_percent': round(col_totals['PHH']/total_households*100) if total_households > 0 else 0,
            'aay_percent': round(col_totals['AAY']/total_households*100) if total_households > 0 else 0,
            'widow_percent': round(sum(data['Widow'].values())/total_households*100) if total_households > 0 else 0,
            'married_male_percent': round(sum(data['Married Male'].values())/total_households*100) if total_households > 0 else 0
        }
        
        return result, summary
        
    except Exception:
        return [
            ["Sr. No.", Paragraph("Social/Economic Status Household"), "AAY", "APL", "AY", "BPL", "PHH", "Total", "%"],
            ["1", "Married Male", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
        ], {'bpl_percent': 0, 'phh_percent': 0, 'aay_percent': 0, 'widow_percent': 0, 'married_male_percent': 0}


def getIncomeGroupData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        # Count households by income class
        upto_50k = households.filter(income_class='Upto 50K').count()
        upto_150k = households.filter(income_class='Upto 1000K').count()
        upto_250k = households.filter(income_class='Upto 250K').count()
        above_250k = households.filter(income_class='>250K').count()
        
        total = upto_50k + upto_150k + upto_250k + above_250k
        
        # Calculate percentages
        upto_50k_pct = round(upto_50k/total*100, 1) if total > 0 else 0
        upto_150k_pct = round(upto_150k/total*100, 1) if total > 0 else 0
        upto_250k_pct = round(upto_250k/total*100, 1) if total > 0 else 0
        above_250k_pct = round(above_250k/total*100, 1) if total > 0 else 0
        
        # Calculate low income dominance (first 2 rows)
        low_income_percent = (upto_50k_pct + upto_150k_pct)
        
        stats = {
            'low_income_percent': low_income_percent
        }
        
        table_data = [
            ["Sr. No.", "Income Group", "No. of Household", "Percentage"],
            ["1", "Upto 50,000", str(upto_50k), f"{upto_50k_pct}%"],
            ["2", "Upto 1,50,000", str(upto_150k), f"{upto_150k_pct}%"],
            ["3", "Upto 2,50,000", str(upto_250k), f"{upto_250k_pct}%"],
            ["4", "> 2,50,000", str(above_250k), f"{above_250k_pct}%"],
            ["5", "Total", str(total), "100%"]
        ]
        
        return table_data, stats
    except Exception:
        return [
            ["Sr. No.", "Income Group", "No. of Household", "Percentage"],
            ["1", "Upto 50,000", "N/A", "N/A"],
            ["2", "Upto 1,50,000", "N/A", "N/A"],
            ["3", "Upto 2,50,000", "N/A", "N/A"],
            ["4", "> 2,50,000", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A"]
        ], {'low_income_percent': 0}

def getAgricultureLandHoldingData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        
        # Count leased land by agriculture land class
        leased_under_05 = households.filter(own_agriculture_land='No', agrculture_land_class='Lessthan 0.5').count()
        leased_05_15 = households.filter(own_agriculture_land='No', agrculture_land_class='Upto 1.5 Bigha').count()
        leased_15_25 = households.filter(own_agriculture_land='No', agrculture_land_class='Upto 2.5 Bigha').count()
        leased_above_25 = households.filter(own_agriculture_land='No', agrculture_land_class='Morethan 2.5 Bigha').count()
        
        # Count owned land by agriculture land class
        owned_under_05 = households.filter(own_agriculture_land='Yes', agrculture_land_class='Lessthan 0.5').count()
        owned_05_15 = households.filter(own_agriculture_land='Yes', agrculture_land_class='Upto 1.5 Bigha').count()
        owned_15_25 = households.filter(own_agriculture_land='Yes', agrculture_land_class='Upto 2.5 Bigha').count()
        owned_above_25 = households.filter(own_agriculture_land='Yes', agrculture_land_class='Morethan 2.5 Bigha').count()
        
        # Count no land households
        no_land = households.filter(agrculture_land_class__isnull=True).count() + households.filter(agrculture_land_class='').count()
        
        # Calculate totals
        total_leased = leased_under_05 + leased_05_15 + leased_15_25 + leased_above_25
        total_owned = owned_under_05 + owned_05_15 + owned_15_25 + owned_above_25
        total_all = total_leased + total_owned + no_land
        
        # Calculate percentages for leased
        leased_under_05_pct = f"{round(leased_under_05/total_leased*100)}%" if total_leased > 0 else "0%"
        leased_05_15_pct = f"{round(leased_05_15/total_leased*100)}%" if total_leased > 0 else "0%"
        leased_15_25_pct = f"{round(leased_15_25/total_leased*100)}%" if total_leased > 0 else "0%"
        leased_above_25_pct = f"{round(leased_above_25/total_leased*100)}%" if total_leased > 0 else "0%"
        leased_total_pct = "100%" if total_leased > 0 else "0%"
        
        # Calculate percentages for owned
        owned_under_05_pct = f"{round(owned_under_05/total_owned*100)}%" if total_owned > 0 else "0%"
        owned_05_15_pct = f"{round(owned_05_15/total_owned*100)}%" if total_owned > 0 else "0%"
        owned_15_25_pct = f"{round(owned_15_25/total_owned*100)}%" if total_owned > 0 else "0%"
        owned_above_25_pct = f"{round(owned_above_25/total_owned*100)}%" if total_owned > 0 else "0%"
        owned_total_pct = "100%" if total_owned > 0 else "0%"
        
        # Calculate statistics for bullet points
        owned_land_percent = round(total_owned/total_all*100) if total_all > 0 else 0
        
        stats = {
            'owned_land_percent': owned_land_percent
        }
        
        table_data = [
            ["Sr. No.", "Agricultural land ownership (in bigha)", "< 0.5", "0.5-1.5", "1.5-2.5", ">2.5", "Total"],
            ["1", "Leased", str(leased_under_05), str(leased_05_15), str(leased_15_25), str(leased_above_25), str(total_leased)],
            ["2", "% leased to total leased", leased_under_05_pct, leased_05_15_pct, leased_15_25_pct, leased_above_25_pct, leased_total_pct],
            ["3", "Owned", str(owned_under_05), str(owned_05_15), str(owned_15_25), str(owned_above_25), str(total_owned)],
            ["4", "% owned to total HH with own agriculture land", owned_under_05_pct, owned_05_15_pct, owned_15_25_pct, owned_above_25_pct, owned_total_pct],
            ["5", "No land (basically manual labour)", "", "", "", "", str(no_land)],
            ["6", "Total", "", "", "", "", str(total_all)]
        ]
        
        return table_data, stats
    except Exception:
        return [
            ["Sr. No.", "Agricultural land ownership (in bigha)", "< 0.5", "0.5-1.5", "1.5-2.5", ">2.5", "Total"],
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
                ["Sr. No.", "Expenditure Category", "Percentage"],
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
            pct = (Decimal(x) / grand_total * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return str(pct) if pct == 0 else f"{pct}%"

        return [
            ["Sr. No.", Paragraph("Expenditure Category", normal_style), "Percentage"],
            ["1", Paragraph("Agriculture", normal_style), percentage(agri_sum)],
            ["2", Paragraph("Festival and marriage", normal_style), percentage(festival_sum)],
            ["3", Paragraph("House repair", normal_style), percentage(repair_sum)],
            ["4", Paragraph("Tobacco and liquor", normal_style), percentage(tobacco_sum)],
            ["5", Paragraph("Education", normal_style), percentage(education_sum)],
            ["6", Paragraph("Health", normal_style), percentage(health_sum)],
            ["7", Paragraph("Food", normal_style), percentage(food_sum)],
            ["8", "Total", "100%" if grand_total > 0 else "0"]
        ]

    except Exception as e:
        print(f"Error in getAverageExpenditureBreakdownData: {e}")
        return [
            ["Sr. No.", Paragraph("Expenditure Category", normal_style), "Percentage"],
            ["1", Paragraph("Agriculture", normal_style), "N/A"],
            ["2", Paragraph("Festival and marriage", normal_style), "N/A"],
            ["3", Paragraph("House repair", normal_style), "N/A"],
            ["4", Paragraph("Tobacco and liquor", normal_style), "N/A"],
            ["5", Paragraph("Education", normal_style), "N/A"],
            ["6", Paragraph("Health", normal_style), "N/A"],
            ["7", Paragraph("Food", normal_style), "N/A"],
            ["8", Paragraph("Total", normal_style), "N/A"]
        ]
        
def getHouseholdDebtLiabilityData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Loan Amount (INR)", "Number of HH", "%"], ["0", "-", "-"], ["<10k", "-", "-"], ["10–50K", "-", "-"], ["50–100K", "-", "-"], [">100K", "-", "-"], ["Total", "-", "-"]]
        
        # Count households by loan class
        no_loan = households.filter(loan_class='No Loan').count()
        loan_10k = households.filter(loan_class='10K').count()
        loan_50k = households.filter(loan_class='50K').count()
        loan_100k = households.filter(loan_class='100K').count()
        loan_above_100k = households.filter(loan_class='>100K').count()
        
        # Calculate percentages
        no_loan_pct = f"{round(no_loan/total_households*100, 2)}%"
        loan_10k_pct = f"{round(loan_10k/total_households*100, 2)}%"
        loan_50k_pct = f"{round(loan_50k/total_households*100, 2)}%"
        loan_100k_pct = f"{round(loan_100k/total_households*100, 2)}%"
        loan_above_100k_pct = f"{round(loan_above_100k/total_households*100, 2)}%"
        
        return [
            ["Sr. No.", "Loan Amount (INR)", "Number of HH", "Percentage"],
            ["1", "0", str(no_loan), no_loan_pct],
            ["2", "<10k", str(loan_10k), loan_10k_pct],
            ["3", "10–50K", str(loan_50k), loan_50k_pct],
            ["4", "50–100K", str(loan_100k), loan_100k_pct],
            ["5", ">100K", str(loan_above_100k), loan_above_100k_pct],
            ["6", "Total", str(total_households), "100%"]
        ]
    except Exception:
        return [
            ["Sr. No.", "Loan Amount (INR)", "Number of HH", "Percentage"],
            ["1", "0", "N/A", "N/A"],
            ["2", "<10k", "N/A", "N/A"],
            ["3", "10–50K", "N/A", "N/A"],
            ["4", "50–100K", "N/A", "N/A"],
            ["5", ">100K", "N/A", "N/A"],
            ["6", "Total", "N/A", "N/A"]
        ]

def getPrimaryLivelihoodDistributionData(village_id, type='primary'):
   
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        field_name = 'livelihood_primary' if type == 'primary' else 'livelihood_secondary'
        activity_type = 'Primary economic activity' if type == 'primary' else 'Secondary economic activity'
        
        if total_households == 0:
            return [['Livelihood', activity_type], ["", "No. of Household", "Percentage"], ["Agriculture", "0", "0%"], ["Fishing", "0", "0%"], ["Livestock", "0", "0%"], ["Manual labour", "0", "0%"], ["No job", "0", "0%"], ["Service", "0", "0%"], ["Shop", "0", "0%"], ["Total", "0", "0%"]]
        
        # Count households by livelihood
        agriculture = households.filter(**{field_name: 'Agriculture'}).count()
        fishing = households.filter(**{field_name: 'Fishing'}).count()
        livestock = households.filter(**{field_name: 'Livestock'}).count()
        manual_labour = households.filter(**{field_name: 'Manual Labour'}).count()
        no_job = households.filter(**{field_name: 'No Job'}).count()
        service = households.filter(**{field_name: 'Service'}).count()
        shop = households.filter(**{field_name: 'Shop'}).count()
        
        # Find max occupation for primary livelihood only
        if type == 'primary':
            counts = {'Agriculture': agriculture, 'Fishing': fishing, 'Livestock': livestock, 'Manual Labour': manual_labour, 'No Job': no_job, 'Service': service, 'Shop': shop}
            max_occupation = max(counts, key=counts.get)
            VILLAGE_SUMMARY_DATA['occupational_category'] = max_occupation
        
        # Calculate percentages
        agriculture_pct = f"{round(agriculture/total_households*100)}%"
        fishing_pct = f"{round(fishing/total_households*100)}%"
        livestock_pct = f"{round(livestock/total_households*100)}%"
        manual_labour_pct = f"{round(manual_labour/total_households*100)}%"
        no_job_pct = f"{round(no_job/total_households*100)}%"
        service_pct = f"{round(service/total_households*100)}%"
        shop_pct = f"{round(shop/total_households*100)}%"
        
        return [
            ['Sr. No.', 'Livelihood', activity_type],
            ["", "", "No. of Household", "Percentage"],
            ["1", "Agriculture", str(agriculture), agriculture_pct],
            ["2", "Fishing", str(fishing), fishing_pct],
            ["3", "Livestock", str(livestock), livestock_pct],
            ["4", "Manual labour", str(manual_labour), manual_labour_pct],
            ["5", "No job", str(no_job), no_job_pct],
            ["6", "Service", str(service), service_pct],
            ["7", "Shop", str(shop), shop_pct],
            ["8", "Total", str(total_households), "100%"]
        ]
    except Exception:
        activity_type = 'Primary economic activity' if type == 'primary' else 'Secondary economic activity'
        return [
            ['Sr. No.', 'Livelihood', activity_type],
            ["", "", "No. of Household", "Percentage"],
            ["1", "Agriculture", "N/A", "N/A"],
            ["2", "Fishing", "N/A", "N/A"],
            ["3", "Livestock", "N/A", "N/A"],
            ["4", "Manual labour", "N/A", "N/A"],
            ["5", "No job", "N/A", "N/A"],
            ["6", "Service", "N/A", "N/A"],
            ["7", "Shop", "N/A", "N/A"],
            ["8", "Total", "N/A", "N/A"]
        ]

def getCropCultivationData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Number of crops", "No. of Household", "Percentage"], ["One crop", "0", "0%"], ["Two crops", "0", "0%"], ["More than 2 crops", "0", "0%"], ["No agriculture", "0", "0%"], ["Total", "0", "0%"]]
        
        one_crop = 0
        two_crops = 0
        more_than_two = 0
        no_agriculture = 0
        
        for hh in households:
            crops = hh.crops_cultivated or ''
            if not crops.strip():
                no_agriculture += 1
            else:
                crop_count = len([c.strip() for c in crops.split(',') if c.strip()])
                if crop_count == 1:
                    one_crop += 1
                elif crop_count == 2:
                    two_crops += 1
                elif crop_count > 2:
                    more_than_two += 1
                else:
                    no_agriculture += 1
        
        # Calculate percentages
        one_crop_pct = f"{round(one_crop/total_households*100)}%"
        two_crops_pct = f"{round(two_crops/total_households*100)}%"
        more_than_two_pct = f"{round(more_than_two/total_households*100)}%"
        no_agriculture_pct = f"{round(no_agriculture/total_households*100)}%"
        
        return [
            ["Sr. No.", "Number of crops", "No. of Household", "Percentage"],
            ["1", "One crop", str(one_crop), one_crop_pct],
            ["2", "Two crops", str(two_crops), two_crops_pct],
            ["3", "More than 2 crops", str(more_than_two), more_than_two_pct],
            ["4", "No agriculture", str(no_agriculture), no_agriculture_pct],
            ["5", "Total", str(total_households), "100%"]
        ]
    except Exception:
        return [
            ["Sr. No.", "Number of crops", "No. of Household", "Percentage"],
            ["1", "One crop", "N/A", "N/A"],
            ["2", "Two crops", "N/A", "N/A"],
            ["3", "More than 2 crops", "N/A", "N/A"],
            ["4", "No agriculture", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A"]
        ]

def getLivestockOwnershipData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Count", "Livestock","","Small cattle"], ["", "HH with Big Cattle", "Percentage", "HH with Small Cattle", "Percentage"], ["0", "-", "-", "-", "-"], ["< 3", "-", "-", "-", "-"], ["3–6", "-", "-", "-", "-"], [">6", "-", "-", "-", "-"]]
        
        # Count big cattle
        big_0 = households.filter(big_cattle='No Big Cattle').count()
        big_3 = households.filter(big_cattle='Upto 3 Big Cattle').count()
        big_3_6 = households.filter(big_cattle='3 To 6 Big Cattle').count()
        big_6_plus = households.filter(big_cattle='Morethan 6 Big Cattle').count()
        
        # Count small cattle
        small_0 = households.filter(small_cattle='No Small Cattle').count()
        small_3 = households.filter(small_cattle='Upto 3 Small Cattle').count()
        small_3_6 = households.filter(small_cattle='3 To 6 Small Cattle').count()
        small_6_plus = households.filter(small_cattle='Morethan 6 Small Cattle').count()
        
        # Calculate percentages
        big_0_pct = f"{round(big_0/total_households*100)}%"
        big_3_pct = f"{round(big_3/total_households*100)}%"
        big_3_6_pct = f"{round(big_3_6/total_households*100)}%"
        big_6_plus_pct = f"{round(big_6_plus/total_households*100)}%"
        
        small_0_pct = f"{round(small_0/total_households*100, 2)}%"
        small_3_pct = f"{round(small_3/total_households*100, 2)}%"
        small_3_6_pct = f"{round(small_3_6/total_households*100, 2)}%"
        small_6_plus_pct = f"{round(small_6_plus/total_households*100, 2)}%"
        
        # Calculate totals
        total_big = big_0 + big_3 + big_3_6 + big_6_plus
        total_small = small_0 + small_3 + small_3_6 + small_6_plus
        
        return [
            ["Sr. No.", "Count", "Livestock","","Small cattle"],
            ["", "", "HH with Big Cattle", "%", "HH with Small Cattle", "%"],
            ["1", "0", str(big_0), big_0_pct, str(small_0), small_0_pct],
            ["2", "< 3", str(big_3), big_3_pct, str(small_3), small_3_pct],
            ["3", "3–6", str(big_3_6), big_3_6_pct, str(small_3_6), small_3_6_pct],
            ["4", ">6", str(big_6_plus), big_6_plus_pct, str(small_6_plus), small_6_plus_pct],
            ["5", "Total", str(total_big), "100%", str(total_small), "100%"]
        ]
    except Exception:
        return [
            ["Sr. No.", "Count", "Livestock","","Small cattle"],
            ["", "", "HH with Big Cattle", "%", "HH with Small Cattle", "%"],
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
        VILLAGE_SUMMARY_DATA['dominant_house_type'] = f"{max_house_type} - {max_percentage}%"
        
        # Calculate percentages as numbers first
        kachcha_pct_val = round(kachcha / total_households * 100, 1)
        semi_pucca_pct_val = round(semi_pucca / total_households * 100, 1)
        pucca_pct_val = round(pucca / total_households * 100, 1)

        # Total percentage (fix rounding by ensuring max 100%)
        total_pct_val = min(100.0, round(kachcha_pct_val + semi_pucca_pct_val + pucca_pct_val, 1))

        # Convert to strings with %
        kachcha_pct = f"{kachcha_pct_val}%"
        semi_pucca_pct = f"{semi_pucca_pct_val}%"
        pucca_pct = f"{pucca_pct_val}%"
        total_pct = f"{total_pct_val}%"

        return [
            ["Sr. No.", "Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
            ["1", "No. of Household", str(kachcha), str(semi_pucca), str(pucca), str(total_households)],
            ["2", "Percentage %", kachcha_pct, semi_pucca_pct, pucca_pct, total_pct]
        ]

    except Exception:
        return [
            ["Sr. No.", "Typology", "Kachcha", "Semi Pucca", "Pucca", "Total"],
            ["1", "No. of Household", "N/A", "N/A", "N/A", "N/A"],
            ["2", "Percentage %", "N/A", "N/A", "N/A", ""]
        ]
        
def getDigitalAccessData(village_id):
    try:
        households = HouseholdSurvey.objects.select_related('village').filter(village_id=village_id)
        total_households = households.count()
        
        if total_households == 0:
            return [["Digital Media Owned", "Number of HH", "Percentage"], ["Mobile Phone", "-", "-"], ["TV", "-", "-"], ["Radio", "-", "-"], ["Radio and Mobile Phone", "-", "-"], ["TV and Mobile Phone", "-", "-"], ["None", "-", "-"], ["Total", "-", "-"]]
        
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
            elif has_tv and not has_mobile and not has_radio:
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
        
        return [
            ["Sr. No.", "Digital Media Owned", "Number of HH", "Percentage"],
            ["1", "Mobile Phone", str(mobile_only), mobile_pct],
            ["2", "TV", str(tv_only), tv_pct],
            ["3", "Radio", str(radio_only), radio_pct],
            ["4", "Radio and Mobile Phone", str(radio_mobile), radio_mobile_pct],
            ["5", "TV and Mobile Phone", str(tv_mobile), tv_mobile_pct],
            ["6", "None", str(none_count), none_pct],
            ["7", "Total", str(total_households), "100%"]
        ]
    except Exception:
        return [
            ["Sr. No.", "Digital Media Owned", "Number of HH", "Percentage"],
            ["1", "Mobile Phone", "N/A", "N/A"],
            ["2", "TV", "N/A", "N/A"],
            ["3", "Radio", "N/A", "N/A"],
            ["4", "Radio and Mobile Phone", "N/A", "N/A"],
            ["5", "TV and Mobile Phone", "N/A", "N/A"],
            ["6", "None", "N/A", "N/A"],
            ["7", "Total", "N/A", "N/A"]
        ]

def getPublicAssetsData(village_id):
    try:
        
        facilities = Critical_Facility.objects.select_related('village').filter(village_id=village_id)
        
        if facilities.count() == 0:
            return [["Presence of facilities"], ["Sr. No.", "Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"], ["1", "Anganwadi", "-", "-", "-", "-", "-", "-"], ["2", "LP School", "-", "-", "-", "-", "-", "-"], ["3", "Middle School", "-", "-", "-", "-", "-", "-"], ["4", "Religious Place", "-", "-", "-", "-", "-", "-"], ["5", "Total", "-", "-", "-", "-", "-", "-"]]
        
        facility_types = ['Anganwadi', 'School', 'Govt Office', 'Religious Place']
        result = [["Presence of facilities"], ["Sr. No.", "Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"]]
        
        # Initialize totals
        total_facilities = 0
        total_electricity = 0
        total_drinking_water = 0
        total_sanitation = 0
        total_good_road = 0
        total_good_building = 0
        
        for i, facility_type in enumerate(facility_types, 1):
            type_facilities = facilities.filter(occupancy_type=facility_type)
            total_count = type_facilities.count()
            
            electricity_count = type_facilities.filter(house_has_electric_connection='Yes').count()
            drinking_water_count = type_facilities.exclude(drinking_water_source__isnull=True).exclude(drinking_water_source='yes').count()
            sanitation_count = type_facilities.exclude(toilet_facility__isnull=True).exclude(toilet_facility='yes').count()
            good_road_count = type_facilities.filter(access_road_during_flood='Good Road').count()
            good_building_count = type_facilities.filter(building_quality__icontains='good').count()
            
            # Add to totals
            total_facilities += total_count
            total_electricity += electricity_count
            total_drinking_water += drinking_water_count
            total_sanitation += sanitation_count
            total_good_road += good_road_count
            total_good_building += good_building_count
            
            result.append([
                str(i),
                facility_type,
                str(total_count),
                str(electricity_count),
                str(drinking_water_count),
                str(sanitation_count),
                str(good_road_count),
                str(good_building_count)
            ])
        
        # Add total row
        result.append([
            "5",
            "Total",
            str(total_facilities),
            str(total_electricity),
            str(total_drinking_water),
            str(total_sanitation),
            str(total_good_road),
            str(total_good_building)
        ])
        
        return result
    except Exception:
        return [
            ["Presence of facilities"],
            ["Sr. No.", "Type", "Number", "Electricity", "Drinking Water", "Sanitation", "Good Road Access", "Building Condition (Good)"],
            ["1", "Anganwadi", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["2", "LP School", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["3", "Middle School", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["4", "Religious Place", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"],
            ["5", "Total", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
        ]


def getRoadLengthByTypologyData(village_id, workspace, layer): 
    try:
        # Get village code
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return [
            ["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
            ["", "Village not found", "0", "0%"]
        ]

    try:
        # Build WFS request
        wfs_url = f"http://localhost:8080/geoserver/{workspace}/ows"
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": f"{workspace}:{layer}",
            "outputFormat": "application/json",
            "CQL_FILTER": f"vill_id='{village_code}'"
        }

        response = requests.get(wfs_url, params=params)
        print(response)
        if response.status_code != 200:
            return [["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
                    ["", "Error fetching data", "0", "0%"]]

        try:
            geojson = response.json()
            # print("Geo json-> ",geojson)
        except Exception as e:
            print("Error parsing JSON:", e)
            return [["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
                    ["", "Invalid response from server", "0", "0%"]]

        features = geojson.get("features", [])
        if not features:
            return [
                ["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
                ["1", "PNRD (Earthen road)", "0", "0%"],
                ["2", "PWD (Bituminous road)", "0", "0%"],
                ["3", "PWD (Cement block road)", "0", "0%"],
                ["4", "PNRD (Cement block road)", "0", "0%"],
                ["5", "PNRD (Concrete road)", "0", "0%"],
                ["6", "WRD (Earthen road)", "0", "0%"],
                ["7", "Total", "0", "0%"]
            ]

        # Aggregate lengths
        surface_lengths = defaultdict(float)
        for feature in features:
            props = feature.get("properties", {})
            surface_type = props.get("rsur_type", "Unknown").strip()
            length_m = props.get("length", 0.0) or 0.0
            surface_lengths[surface_type] += float(length_m)

        # Convert to km and calculate total
        total_length = sum(surface_lengths.values()) / 1000
        
        # Build result dynamically
        result = [["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"]]
        
        for idx, (surface_type, length_m) in enumerate(surface_lengths.items(), 1):
            length_km = length_m / 1000
            percentage = f"{round(length_km / total_length * 100, 2)}%" if total_length > 0 else "0%"
            result.append([
                str(idx),
                surface_type,
                f"{length_km:.2f}",
                percentage
            ])
        
        # Add total row
        result.append([
            str(len(surface_lengths) + 1),
            "Total",
            f"{total_length:.2f}",
            "100.00%" if total_length > 0 else "0%"
        ])
        
        return result

    except Exception:
        return [
            ["Sr. No.", "Surface Type", "Length (km)", "% to Total Road Length"],
            ["1", "PNRD (Earthen road)", "N/A", "N/A"],
            ["2", "PWD (Bituminous road)", "N/A", "N/A"],
            ["3", "PWD (Cement block road)", "N/A", "N/A"],
            ["4", "PNRD (Cement block road)", "N/A", "N/A"],
            ["5", "PNRD (Concrete road)", "N/A", "N/A"],
            ["6", "WRD (Earthen road)", "N/A", "N/A"],
            ["7", "Total", "N/A", "N/A"]
        ]




def getLULCData(village_id, workspace, layer):
    try:
        village = tblVillage.objects.get(id=village_id)
        village_code = village.code
    except tblVillage.DoesNotExist:
        return [["Sr. No.", "Landuse", "Area (sqm)", "Percentage"], ["", "Village not found", "0", "0%"]]

    wfs_url = f"http://localhost:8080/geoserver/{workspace}/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": f"{workspace}:{layer}",
        "outputFormat": "application/json",
        "CQL_FILTER": f"vill_id='{village_code}'"
    }

    response = requests.get(wfs_url, params=params)
    if response.status_code != 200:
        return [["Sr. No.", "Landuse", "Area (sqm)", "Percentage"], ["", "Error fetching data", "0", "0%"]]

    geojson = response.json()
    features = geojson.get("features", [])

    if not features:
        return [["Sr. No.", "Landuse", "Area (sqm)", "Percentage"], ["", "No data available for this village", "0", "0%"]]

    from collections import defaultdict
    from decimal import Decimal, ROUND_HALF_UP

    class_area = defaultdict(float)
    for feature in features:
        props = feature["properties"]
        class_name = props.get("class_name", "Unknown")
        area_sqm = props.get("shape_area", 0.0) or 0.0
        class_area[class_name] += float(area_sqm)

    total_area = sum(class_area.values())
    
    # Find max land use and update global dictionary
    if class_area:
        max_land_use = max(class_area, key=class_area.get)
        max_area = class_area[max_land_use]
        percentage = round((max_area / total_area) * 100) if total_area > 0 else 0
        VILLAGE_SUMMARY_DATA['major_land_use'] = f"{max_land_use} - {percentage}%"

    def format_number(n):
        return f"{int(n):,}"

    result = [["Sr. No.", "Landuse", "Area (sqm)", "Percentage"]]
    
    total_percent = Decimal("0")
    for idx, (class_name, area) in enumerate(class_area.items(), start=1):
        percent = (Decimal(area) / Decimal(total_area) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        total_percent += percent
        result.append([
            str(idx),
            class_name,
            format_number(area),
            f"{percent}%"
        ])
    total_percent = min(Decimal("100"), total_percent)
    result.append(["", "Total Area", format_number(total_area), f"{total_percent}%"])
    return result


from vdmp_dashboard.models import VDMP_Maps_Data
from assam_crv.settings import MEDIA_ROOT

def draw_village_profile(elements,village_id):

    map_file_fields = VDMP_Maps_Data.objects.filter(village_id=village_id).values(
        'village_id',
        'distribution_of_building',
        'road_infrastructure',
        'landuse',
        'flood_erosion',
        'wind_hazard',
        'earthquake_hazard',
        'essential_facilities',
        'electrical_infrastructure'
    ).first()


    styles = getSampleStyleSheet()
    heading = Paragraph("<a name='village_profile'/><b>3 Village Profile</b>", blue_heading)
    # add_heading_with_toc("Village Profile", blue_heading, level=1, elements=elements)
    elements.append(heading)
    # elements.append(Spacer(1, 12))

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
    heading = Paragraph("<b>3.2	Socio economic profile</b>", blue_sub_heading) 
    # add_heading_with_toc("Socio economic profile", blue_sub_heading, level=2, elements=elements)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 1: Demographic profile", table_sub_title) 
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
        ('FONTNAME', (1, -2), (-1, -1), 'Helvetica-Bold'),
    ]
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 2: Socio economic status", table_sub_title) 
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, summary = getSocialEconomicStatusData(village_id)
    table = create_styled_table(data, [40,150,40,40,40,50,50,50,40], False, True, custom_styles, "Socio Economic Status")
   
    elements.append(table)
    para=Paragraph("Note: Antyodaya (AAY), Above Poverty Line (APL), Annapurna Yojna (AY), Below Poverty Line (BPL), Priority Household (PHH).", notes_style)
    elements.append(para)
    
    p = Paragraph(
    f'<bullet>&bull;</bullet> Majority ({summary["bpl_percent"]}%) are Below Poverty Line (BPL) followed by Priority Household (PHH-{summary["phh_percent"]}%), and {summary["aay_percent"]}% under Antyodaya Anna Yojana (AAY).',
    styles["Normal"]
    )
    elements.append(p)
    
    p2 = Paragraph(
    f'<bullet>&bull;</bullet> {summary["widow_percent"]}% of households are headed by widows.',
    styles["Normal"]
    )
    elements.append(p2)
    
    p3 = Paragraph(
    f'<bullet>&bull;</bullet> {summary["married_male_percent"]}% of households are headed by married males.',
    styles["Normal"]
    )
    elements.append(p3)
    elements.append(Spacer(1, 12))
    # -------------------------- 3 3 ---------------
    custom_styles=[
         ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    sub_title=Paragraph("Table 3 3: Annual household income", table_sub_title) 
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, income_stats = getIncomeGroupData(village_id)
    table = create_styled_table(data, [40,155,150,155], False, True, custom_styles, "Annual Household Income")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # -------------------- 3.4 ----------------
    custom_styles=[
         ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    sub_title=Paragraph("Table 3 4: Household level agriculture land holding", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data, land_stats = getAgricultureLandHoldingData(village_id)
    table = create_styled_table(data, [40,235, 45,45,45,45,45], False, True, custom_styles, "Agriculture Land Holding")
    elements.append(table)
    para=Paragraph("Note: 1 Bigha = 0.68 Hectare", notes_style)
    elements.append(para)
    elements.append(Spacer(1, 12))
    
    # Define bullet point content
    points = [
        f"Low income dominance - {income_stats['low_income_percent']}% of the household has annual income of about INR 1.5 lakhs.",
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
    
    #-------------------- 3 5-----------------
    custom_styles=[
       ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
    ]
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 5: Average expenditure break down for household", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getAverageExpenditureBreakdownData(village_id)
    table = create_styled_table(data, [40,360,100], False, True, custom_styles, "Average Expenditure Breakdown")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # ------------------- 3 6 ----------
    sub_title=Paragraph("Table 3 6: Household debit liability in the last 5 years", table_sub_title)
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
    sub_title=Paragraph("Table 3 7: Primary livelihood distribution (primary economic activity)", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 12))
    data=getPrimaryLivelihoodDistributionData(village_id)
    
    table = create_styled_table(data, [40,240, 100,120], True, True, custom_styles, "Primary Livelihood Distribution (primary economic activity)")
    elements.append(table)
    elements.append(Spacer(1, 6))
    
    #------------------------
    sub_title=Paragraph("Table 3 8: Livelihood distribution (secondary economic activity)", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getPrimaryLivelihoodDistributionData(village_id, 'secondary')
    table = create_styled_table(data, [40,240, 100, 120], True, True, custom_styles, "Secondary Livelihood Distribution (secondary economic activity)")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # ------------------------
    custom_styles=[
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
         ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
         ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]
    sub_title=Paragraph("Table 3 9: Number of crops cultivated", table_sub_title)
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
        ('SPAN', (0, 0), (0, 1)),  # Merge Sr. No. cells
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
    sub_title=Paragraph("Table 3 10: Household with Livestock", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getLivestockOwnershipData(village_id)
    table = create_styled_table(data, [40,90, 110, 50, 110, 100], True, True, custom_styles2, "Livestock Ownership")
    elements.append(table)
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
    sub_title=Paragraph("Table 3 11: Distribution of house by typology", table_sub_title)
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
   
    image_height = page_height * 0.77

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
    img_field = map_file_fields['distribution_of_building']
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
        sub_title=Paragraph("Figure 3 1: Distribution of residential building", image_title)
        elements.append(sub_title)
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
        sub_title=Paragraph("Figure 3 1: Distribution of residential building", image_title)
        elements.append(sub_title)
        elements.append(Spacer(1, 12))
        
        # Add legends horizontally with text labels
        elements.append(Spacer(1, 6))
        elements.append(Paragraph('Residential building Legends', Legend_heading))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph('<font color="#a83800">■</font> -- buildings', normal_style))


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
    sub_title=Paragraph("Table 3 12: Access to social media and information", table_sub_title)
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
    
    asset_points = [
        f"About {mobile_pct} household has mobile connectivity and access to internet. But use for entertainment. Doesn't have the knowledge to access information useful for farming or relief entitlement",
        f"Only three household responded they have solar as alternate electricity source.",
        f"All household has toilet and access to drinking water. However, 76% of the household has Kachcha structure as toilet (made of tin, leaves/cloth) and just a pit to dispose the waste. Rest of the house has toilet with double pit septic tank but majority of these tanks are poorly maintained.",
        f"Household assets include very basic furniture like wooden coat, wooden table, plastic chairs and kitchen utensils. Community store food grains at home."
    ]
    
    asset_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, styles["Normal"])) for text in asset_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    
    elements.append(asset_bullet_items)
    
    
    
    
    
    # ---------------------
    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Table 3 13: Public assets in the village", table_sub_title)
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
   
    image_height = page_height * 0.75
    
    img_field = map_file_fields['essential_facilities']
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
        sub_title=Paragraph("Figure 3 2: Critical Facilities", image_title)
        elements.append(sub_title)

    # --------------------
    elements.append(Spacer(1, 12))
    heading = Paragraph("<b>3.5	Infrastructure</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    heading = Paragraph("<b>3.5.1 Road Infrastructure</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 14: Road length by typology ", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getRoadLengthByTypologyData(village_id,'assam','road_network')
    table = create_styled_table(data, [40,160,150,150], False, True, custom_styles, "Road Length by Typology")
    elements.append(table)
    elements.append(Spacer(1, 12))
    # Add geoserver image with border
    
    image_height = page_height * 0.75
    

    #img from the model
    img_field = map_file_fields['road_infrastructure']
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
        sub_title=Paragraph("Figure 3 3: Road infrastructure map", image_title)
        elements.append(sub_title)
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
            sub_title=Paragraph("Figure 3 3: Road infrastructure map", image_title)
            elements.append(sub_title)
            
            elements.append(Spacer(1, 6))
            elements.append(Paragraph('Road Network Legends', Legend_heading))
            elements.append(Spacer(1, 6))
    


            # Road network legends with colored lines (ReportLab doesn't support text rotation in Paragraph)
            elements.append(Paragraph('<font color="#db1e2a">━━━━━━━━━━</font> Bituminous', normal_style))
            elements.append(Paragraph('<font color="#f67872">━━━━━━━━━━</font> Cement Block', normal_style))
            elements.append(Paragraph('<font color="#796868">━━━━━━━━━━</font> Earthen', normal_style))
            elements.append(Paragraph('<font color="#000000">━━━━━━━━━━</font> Village Boundary', normal_style))
            
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
    sub_title=Paragraph("Table 3 15: Power infrastructure ", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getPowerInfrastructureData_Total(village_id)
    table = create_styled_table(data, [40,360,100], False, True, custom_styles, "Power Infrastructure")
    elements.append(table)
    elements.append(Spacer(1, 12))

    image_height = page_height * 0.64

    #img from model if not available get from geoserver
    img_field = map_file_fields['electrical_infrastructure'] if map_file_fields else None
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
        sub_title=Paragraph("Figure 3 4: Power infrastructure", image_title)
        elements.append(sub_title)

    #  ------------------------- 
    
    elements.append(Spacer(1, 12))
    heading = Paragraph("<b>3.6	Access to other facilities</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 16: Access to other facilities", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getFacilityAccessData()
    table = create_styled_table(data, [40,200, 120, 100], False, True, [('ALIGN', (0, 1), (0, -1), 'RIGHT')], "Facility Access")
    elements.append(table)

    # ------------------------
    elements.append(Spacer(1, 12))
    heading = Paragraph("<b>3.7	Landuse</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    sub_title=Paragraph("Table 3 17: Landuse", table_sub_title)
    elements.append(sub_title)
    elements.append(Spacer(1, 6))
    data=getLULCData(village_id,'assam','lulc')
    table = create_styled_table(data, [40,180, 120, 120], False, True, custom_styles, "Land Use Classification")
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

    img_field = map_file_fields['landuse']
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
        layers = ['assam:lulc']
        img, actual_width, actual_height = get_geoserver_image_as_rl_image(
            layers, village_id=village_id, max_width=500
        )
        if img:
            # img is already a ReportLab Image object - use directly
            img_table = ReportLabTable([[img]])
            img_table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.black)]))
            elements.append(img_table)

    elements.append(Spacer(1, 12))
    sub_title=Paragraph("Figure 3 5: Landuse map", image_title)
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
    
    
