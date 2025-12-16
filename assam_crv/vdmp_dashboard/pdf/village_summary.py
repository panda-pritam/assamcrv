from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

from village_profile.models import tblVillage
from datetime import datetime

from vdmp_dashboard.models import HouseholdSurvey
from collections import Counter


from .dummy_data import  getHazardAssessment,getVulnerabilityAssessment,getMitigationIntervention,getDistrictLevelOfficialsData,getEmergencyTollFreeContactData,getImportantEmergencyContactData

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
        
        return [
            ['General Summary Table'],
            ['Date of Preparation', datetime.now().strftime('%B %Y')],
            ['Village Name', village.name],
            ['Block', village.gram_panchayat.name],
            ['Revenue Circle', village.gram_panchayat.circle.name],
            ['District', village.gram_panchayat.circle.district.name]
        ]
    else:
        return [
            ['General Summary Table'],
            ['Date of Preparation', datetime.now().strftime('%B %Y')],
            ['Village Name', 'N/A'],
            ['Block', 'N/A'],
            ['Revenue Circle', 'N/A'],
            ['District', 'N/A']
        ] 
        
    
    
def generate_socio_economic_summary_table(village_id):
  
    
    households = HouseholdSurvey.objects.filter(village_id=village_id)
    
    # Calculate and update global data
    total_population = 0
    sanitation_counts = Counter()
    
    # Count all sanitation types
    pucca_count = 0
    kachcha_count = 0
    no_toilet_count = 0
    
    for household in households:
        males = int(household.number_of_males_including_children or 0)
        females = int(household.number_of_females_including_children or 0)
        total_population += males + females
        
        # Count sanitation types
        sanitation_type = getattr(household, 'Sanitation_Type', None) or 'No toilet'
        if sanitation_type == 'Pucca':
            pucca_count += 1
        elif sanitation_type == 'Kachcha':
            kachcha_count += 1
        else:
            no_toilet_count += 1
    
    # Find dominant sanitation type (excluding No toilet)
    total_households_count = households.count()
    if pucca_count >= kachcha_count and pucca_count > 0:
        percentage = round((pucca_count / total_households_count) * 100)
        sanitation_text = f"Pucca toilet - {percentage}%"
    elif kachcha_count > 0:
        percentage = round((kachcha_count / total_households_count) * 100)
        sanitation_text = f"Kachcha toilet - {percentage}%"
    else:
        sanitation_text = 'No data available'
    print(sanitation_text,pucca_count,)
    # Update global dictionary
    VILLAGE_SUMMARY_DATA['total_population'] = total_population
    VILLAGE_SUMMARY_DATA['total_households'] = households.count()
    VILLAGE_SUMMARY_DATA['sanitation_facilities'] = sanitation_text
    
    return [
        ['Socio-Economic Summary'],
        ['Total Population', VILLAGE_SUMMARY_DATA['total_population']],
        ['Total Households', VILLAGE_SUMMARY_DATA['total_households']],
        ['Dominant House Type', VILLAGE_SUMMARY_DATA['dominant_house_type']],
        ['Major Land Use', VILLAGE_SUMMARY_DATA['major_land_use']],
        ['Occupational Category', VILLAGE_SUMMARY_DATA['occupational_category']],
        ['Sanitation Facilities', VILLAGE_SUMMARY_DATA['sanitation_facilities']]
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
    
   
    
    
from vdmp_dashboard.models import Risk_Assesment
from village_profile.models import tblVillage

def getRiskAssessment(village_id):
    try:
        # Validate and fetch village safely
        village = tblVillage.objects.filter(id=village_id).first()
        if not village:
            return [
                ['Risk Assessment (excluding content loss in INR Crore)'],
                ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
                ['Residential', '-'],
                ['Commercial', '-'],
                ['Critical Facilities', '-'],
                ['Roads', '-'],
                ['Agriculture', '-'],
                ['Note', '-']
            ]
        
        risk_data = Risk_Assesment.objects.filter(village=village)
        if risk_data.exists():
            # Helper function to safely fetch value
            def get_value(qs, hazard, exposure_filter):
                record = qs.filter(hazard__iexact=hazard, **exposure_filter).first()
                return record.total_exposure_value_inr_crore if record else '-'

            # Residential
            residential_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Residential"})
            residential_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Residential"})
            residential_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Residential"})

            # Commercial
            commercial_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Commercial"})
            commercial_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Commercial"})
            commercial_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Commercial"})

            # Critical Facilities
            critical_facilities_flood = get_value(risk_data, "Flood", {"exposure_type__icontains": "Critical"})
            critical_facilities_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__icontains": "Critical"})
            critical_facilities_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__icontains": "Essential"})

            # Roads
            roads_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Roads"})
            roads_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Roads"})
            roads_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Roads"})

            # Agriculture
            agriculture_flood = get_value(risk_data, "Flood", {"exposure_type__istartswith": "Agriculture"})
            agriculture_earthquake = get_value(risk_data, "Earthquake", {"exposure_type__istartswith": "Agriculture"})
            agriculture_cyclone = get_value(risk_data, "Cyclone", {"exposure_type__istartswith": "Agriculture"})

            return [
                ['Risk Assessment (excluding content loss in INR Crore)'],
                ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
                ['Residential', str(residential_flood), str(residential_earthquake), str(residential_cyclone)],
                ['Commercial', str(commercial_flood), str(commercial_earthquake), str(commercial_cyclone)],
                ['Critical Facilities', str(critical_facilities_flood), str(critical_facilities_earthquake), str(critical_facilities_cyclone)],
                ['Roads', str(roads_flood), str(roads_earthquake), str(roads_cyclone)],
                ['Agriculture', str(agriculture_flood), str(agriculture_earthquake), str(agriculture_cyclone)],
                ['Note', '-', '-', '-']
            ]
        else:
            return [
                ['Risk Assessment (excluding content loss in INR Crore)'],
                ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
                ['Residential', '-'],
                ['Commercial', '-'],
                ['Critical Facilities', '-'],
                ['Roads', '-'],
                ['Agriculture', '-'],
                ['Note', '-']
            ]
    except Exception as e:
        # In case of invalid village_id or unexpected error
        return [
                ['Risk Assessment (excluding content loss in INR Crore)'],
                ['Sector', Paragraph('Flood 2022 Scenario (INR Crore)'), 'Earthquake 475 RP', 'Strong wind 100 RP'],
                ['Residential', '-'],
                ['Commercial', '-'],
                ['Critical Facilities', '-'],
                ['Roads', '-'],
                ['Agriculture', '-'],
                ['Note', '-']
        ]

