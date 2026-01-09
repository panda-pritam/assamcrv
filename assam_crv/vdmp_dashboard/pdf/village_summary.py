from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from village_profile.models import tblVillage
from datetime import datetime

from vdmp_dashboard.models import HouseholdSurvey, Critical_Facility, Risk_Assesment
from vdmp_progress.models import Risk_Assessment_Result
from collections import Counter

from .village_profile import getVillageArea, getLULCData
from django.db.models import Count,Sum



from .dummy_data import  getHazardAssessment,getMitigationIntervention,getDistrictLevelOfficialsData,getEmergencyTollFreeContactData,getImportantEmergencyContactData

from .global_styles import blue_heading, underline_heading, notes_style

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

# Get village related data from the database
def generate_general_summary_table(village_id=None):
   
    if village_id:
        # Optimized query with select_related to avoid N+1 queries
        village = tblVillage.objects.select_related(
            'gram_panchayat',
            'gram_panchayat__circle', 
            'gram_panchayat__circle__district'
        ).get(id=village_id)
        
        # Get village area
        village_area = getVillageArea(village_id)
        area_text = f"{village_area:.2f} sq km" if village_area > 0 else "N/A"
        
        # Get major land use
        lulc_data = getLULCData(village_id, 'assam', 'lulc', True)
        major_land_use = lulc_data if lulc_data else "N/A"
        print(major_land_use)
        VILLAGE_SUMMARY_DATA['major_land_use'] = major_land_use
        
        return [
            ['General Summary Table'],
            ['Date of Preparation', datetime.now().strftime('%B %Y')],
            ['Village Name', village.name],
            ['Block', village.gram_panchayat.name],
            ['Village area', area_text],
            ['Revenue Circle', village.gram_panchayat.circle.name],
            ['District', village.gram_panchayat.circle.district.name]
            
        ]
    else:
        return [
            ['General Summary Table'],
            ['Date of Preparation', datetime.now().strftime('%B %Y')],
            ['Village Name', 'N/A'],
            ['Block', 'N/A'],
            ['Village area', 'N/A'],
            ['Revenue Circle', 'N/A'],
            ['District', 'N/A'],
            ['Major Land Use', 'N/A']
        ] 
        
    
    
def generate_socio_economic_summary_table(village_id):
  
    
    households = HouseholdSurvey.objects.filter(village_id=village_id)
    
    # Calculate total population
    total_population = sum(
        int(h.number_of_males_including_children or 0) + 
        int(h.number_of_females_including_children or 0) 
        for h in households
    )
    
    # Count sanitation types using filter
    community_toilet = households.filter(Sanitation_Type='Community Toilet').count()
    own_toilet = households.filter(Sanitation_Type='Own').count()
    open_defecation = households.filter(Sanitation_Type='Open').count()
    total_households_count = households.count()
    
    # Find dominant sanitation type
    counts = {'Community Toilet': community_toilet, 'Own': own_toilet, 'Open': open_defecation}
    if total_households_count > 0:
        max_sanitation_type = max(counts, key=counts.get)
        max_percentage = round((counts[max_sanitation_type] / total_households_count) * 100)
        sanitation_text = f"{max_sanitation_type} - {max_percentage}%"
    else:
        sanitation_text = 'No data available'
    
    # Update global dictionary
    VILLAGE_SUMMARY_DATA['total_population'] = total_population
    VILLAGE_SUMMARY_DATA['total_households'] = total_households_count
    VILLAGE_SUMMARY_DATA['sanitation_facilities'] = sanitation_text

    # Count households by house type
    kachcha = households.filter(house_type='Kachcha').count()
    semi_pucca = households.filter(house_type='Semi Pucca').count()
    pucca = households.filter(house_type='Pucca').count()
    
    # Find dominant house type and update global dictionary
    counts = {'Kachcha': kachcha, 'Semi Pucca': semi_pucca, 'Pucca': pucca}
    if total_households_count > 0:
        max_house_type = max(counts, key=counts.get)
        max_percentage = round((counts[max_house_type] / total_households_count) * 100, 1)
        VILLAGE_SUMMARY_DATA['dominant_house_type'] = f"{max_house_type} - {max_percentage}%"
    else:
        VILLAGE_SUMMARY_DATA['dominant_house_type'] = 'N/A'
        
    
    livelihood_qs = (
        households
        .exclude(livelihood_primary__isnull=True)
        .exclude(livelihood_primary__exact='')
        .values('livelihood_primary')
        .annotate(count=Count('livelihood_primary'))
        .order_by('-count')
    )

    if livelihood_qs.exists() and total_households_count > 0:
        top_livelihood = livelihood_qs[0]['livelihood_primary']
        top_count = livelihood_qs[0]['count']
        percentage = round((top_count / total_households_count) * 100)

        VILLAGE_SUMMARY_DATA['occupational_category'] = (
            f"{top_livelihood} - {percentage}%"
        )
    else:
        VILLAGE_SUMMARY_DATA['occupational_category'] = 'No data available'


    return [
        ['Socio-Economic Summary'],
        ['Total Population', VILLAGE_SUMMARY_DATA['total_population']],
        ['Total Households', VILLAGE_SUMMARY_DATA['total_households']],
        ['Dominant House Type', VILLAGE_SUMMARY_DATA['dominant_house_type']],
        ['Major Land Use', VILLAGE_SUMMARY_DATA['major_land_use']],
        ['Occupational Category', VILLAGE_SUMMARY_DATA['occupational_category']],
        ['Sanitation Facilities', VILLAGE_SUMMARY_DATA['sanitation_facilities']]
    ]


def getRiskAssessment(village_id):
   
   
    
    # Get risk assessment data for the village
    risk_data = Risk_Assessment_Result.objects.filter(village_id=village_id)
    
    if not risk_data.exists():
        return [
            ['Risk Assessment (excluding content loss in INR Crore)'],
            ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
            ['Residential', 'No data', 'No data', 'No data'],
            ['Commercial', 'No data', 'No data', 'No data'],
            ['Critical Facilities', 'No data', 'No data', 'No data'],
            ['Roads', '-', '-', '-'],
            ['Agriculture', '-', '-', '-'],
            ['Note', 'Excluding content loss', '', '']
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
    
    return [
        ['Risk Assessment (excluding content loss in INR Crore)'],
        ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
        ['Residential', f'{household_flood:.2f}', f'{household_eq:.2f}', f'{household_wind:.2f}'],
        ['Commercial', f'{commercial_flood:.2f}', f'{commercial_eq:.2f}', f'{commercial_wind:.2f}'],
        ['Critical Facilities', f'{critical_flood:.2f}', f'{critical_eq:.2f}', f'{critical_wind:.2f}'],
        ['Roads', '-', '-', '-'],
        ['Agriculture', '-', '-', '-'],
        ['Note', 'Excluding content loss', '', '']
    ]


def getVulnerabilityAssessment(village_id):
    from django.db.models import Q
    
    households = HouseholdSurvey.objects.filter(village_id=village_id)
    total_households = households.count()
    
    if total_households == 0:
        return [
            ["Vulnerability Assessment"],
            ['Economic Status', 'No data'],
            ['Vulnerable Population', 'No data'],
            ['Flood Vulnerability Houses', 'No data'],
            ['Erosion Vulnerability Houses', 'No data'],
            ['Flood Vulnerability Roads', 'No data'],
            ['Erosion Vulnerability Roads', 'No data'],
            ['Schools', 'No data'],
            ['Livelihood Vulnerability Index', 'No data'],
            ['Index Interpretation', 'No data']
        ]
    
    # Economic Status - show BPL and PHH percentages only
    bpl_count = 0
    phh_count = 0
    
    for household in households:
        economic = household.economic_status or ''
        if economic.upper() == 'BPL' or 'below poverty line' in economic.lower():
            bpl_count += 1
        elif economic.upper() == 'PHH' or 'priority household' in economic.lower():
            phh_count += 1
    
    bpl_percent = round((bpl_count / total_households) * 100) if bpl_count > 0 else 0
    phh_percent = round((phh_count / total_households) * 100) if phh_count > 0 else 0
    
    economic_status = f"BPL - {bpl_percent}%, Priority Household - {phh_percent}%"
    
    # Vulnerable Population (age < 6, >60, pregnant women, lactating mother, permanently disabled or chronic disease)
    vulnerable_count = 0
    total_population = 0
    
    for household in households:
        try:
            vulnerable_count += int(household.persons_with_disability_or_chronic_disease or 0)
            vulnerable_count += int(household.lactating_women or 0)
            vulnerable_count += int(household.pregnant_women or 0)
            vulnerable_count += int(household.senior_citizens or 0)
            vulnerable_count += int(household.children_below_6_years or 0)
            total_population += int(household.number_of_males_including_children or 0) + int(household.number_of_females_including_children or 0)
        except (ValueError, TypeError):
            continue
    
    if total_population > 0:
        vulnerable_percent = round((vulnerable_count / total_population) * 100)
        vulnerable_population = f"{vulnerable_count} ({vulnerable_percent}%)"
    else:
        vulnerable_population = 'No data'
    
    # Houses vulnerable to flood (flood_depth_m >= 0.5)
    flood_vulnerable_houses = 0
    for household in households:
        try:
            flood_depth = float(household.flood_depth_m or 0)
            if flood_depth >= 0.5:
                flood_vulnerable_houses += 1
        except (ValueError, TypeError):
            continue
    
    flood_vulnerable_percent = round((flood_vulnerable_houses / total_households) * 100) if flood_vulnerable_houses > 0 else 0
    flood_vulnerability_houses = f"{flood_vulnerable_houses} ({flood_vulnerable_percent}%)"
    
    # Houses vulnerable to erosion
    erosion_vulnerable_houses = households.filter(house_vulnerable_to_erosion__iexact='yes').count()
    erosion_vulnerable_percent = round((erosion_vulnerable_houses / total_households) * 100) if erosion_vulnerable_houses > 0 else 0
    erosion_vulnerability_houses = f"{erosion_vulnerable_houses} ({erosion_vulnerable_percent}%)"
    
    # Schools vulnerable to flood
    schools_vulnerable = 0
    critical_facilities = Critical_Facility.objects.filter(village_id=village_id)
    
    for facility in critical_facilities:
        if facility.occupancy_type and 'school' in facility.occupancy_type.lower():
            try:
                flood_depth = float(facility.flood_depth_m or 0)
                if flood_depth > 0.5:
                    schools_vulnerable += 1
            except (ValueError, TypeError):
                continue
    
    schools_text = str(schools_vulnerable) if schools_vulnerable > 0 else '0'
    
    return [
        ["Vulnerability Assessment"],
        ['Economic Status', economic_status],
        ['Vulnerable Population', vulnerable_population],
        ['Flood Vulnerability Houses', flood_vulnerability_houses],
        ['Erosion Vulnerability Houses', erosion_vulnerability_houses],
        ['Flood Vulnerability Roads', '-'],
        ['Erosion Vulnerability Roads', '-'],
        ['Schools', schools_text],
        ['Livelihood Vulnerability Index', '-'],
        ['Index Interpretation', '-']
    ]


def village_summary(elements,village_id):
    styles = getSampleStyleSheet()
    heading = Paragraph("<b>2  Summary Village Details </b>", blue_heading)
    
    elements.append(heading)
    elements.append(Spacer(1, 12))
    

    table_sections = [
        {"heading": "General Summary Table",
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
             "col_width":[200, 300]
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
        # elements.append(Spacer(1, 12))
    
    # Notes section  
    elements.append(Spacer(1, 12))
    para=Paragraph("Note: While the investment amount mentioned above for mitigation represents the maximum, the Chapter 6 also presents various cost-effective alternatives. There are other possible cost effective solutions as well which can be explored while developing Detailed Project Report.", notes_style)
    elements.append(para)
    
    # Village contacts 
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Important contact details</b>", blue_heading))
    elements.append(Spacer(1, 6))
    imp_contact_details=getDistrictLevelOfficialsData()
    table=create_styled_table(imp_contact_details, [40,150,60,100,150], False, True, [('ALIGN', (0, 1), (0, -1), 'RIGHT'),('ALIGN', (3, 1), (3, -1), 'RIGHT'),('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')], "Village Contacts")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Emergency toll free contact information
    
    elements.append(Paragraph('<u><b>Emergency Toll Free Contact Information</b></u>', underline_heading))

    custom_style=[   ('ALIGN', (0, 1), (0, -1), 'RIGHT'),('ALIGN', (2, 1), (2, -1), 'RIGHT'),('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')]
    
    elements.append(Spacer(1, 6))
    emergency_contact_details=getEmergencyTollFreeContactData()
    table=create_styled_table(emergency_contact_details, [40, 250,210], False, True, custom_style, "Emergency Toll Free Contact")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Important Emergency contact information
    elements.append(Paragraph("<u><b>Important Emergency Contact Information</b></u>", underline_heading))
    elements.append(Spacer(1, 6))
    imp_contact_details=getImportantEmergencyContactData()
    table=create_styled_table(imp_contact_details, [40, 250, 210], False, True, custom_style, "Important Emergency Contact")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
   
    
    
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

