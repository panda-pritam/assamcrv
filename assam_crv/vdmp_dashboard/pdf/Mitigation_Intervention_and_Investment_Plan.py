from reportlab.platypus import Paragraph, Spacer,  ListFlowable, ListItem, Image
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
import os
from .global_styles import  blue_heading,table_sub_title,blue_sub_heading,image_title,notes_style,tb_header_bg,Legend_heading,indented_style,bold_style,normal_style,srNoStyle,non_toc_heading,blue_level3_heading,non_indented_style
from .utils.table import create_styled_table
# from .utils.geoserverLayerImage import get_geoserver_image_path, get_geoserver_legend_path
from task_force.models import *
from village_profile.models import tblVillage
from .dummy_data import getFacilityAccessData
from django.db.models import Sum, Count
import requests
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from .dummy_data import *

styles = getSampleStyleSheet()





def draw_mitigation_intervention_and_investment_plan(elements, village_id):
    styles = getSampleStyleSheet()
    heading = Paragraph("<a name='draw_mitigation_intervention_and_investment_plan'/><b>6	Mitigation Intervention and Investment Plan</b>", blue_heading)
    elements.append(heading)
    elements.append(Spacer(1, 12))
    
    # 6.1 Developmental Issues and Needs
    heading = Paragraph("<b>6.1 Developmental Issues and Needs</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    dev_issues_data = getDevelopmentIssuesTable()
    table = create_styled_table(dev_issues_data, [40, 120, 340], False, True, srNoStyle, "Developmental Issues and Needs")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2 Mitigation Intervention Strategy
    heading = Paragraph("<b>6.2 Mitigation Intervention Strategy</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    strategy_text = "The mitigation intervention should address the vulnerability aspects of the village and improve the resilience. To optimize the investment and sustainability the mitigation interventions should be a mix of structural and non-structural options. Some intervention would be at local level (for instance construction of road, WASH facilities) while some intervention (like construction of embankment) needs to be planned at regional or river basin level. Policy intervention also required to address long term sustainability particularly in sectors like health, education and livelihood. The mitigation intervention for the village is presented below."
    elements.append(Paragraph(strategy_text, non_indented_style))
    elements.append(Spacer(1, 12))
    
    # 6.2.1 Resilient Housing
    heading = Paragraph("<b>6.2.1 Resilient Housing</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    table_heading = Paragraph("<b>Table 6.1: Indicators contributing to residential vulnerability</b>", table_sub_title)
    elements.append(table_heading)
    elements.append(Spacer(1, 6))
    
    residential_vuln_data = getResidentialVulnerabilityTable()
    table = create_styled_table(residential_vuln_data, [60, 300, 140], False, True, srNoStyle, "Residential Vulnerability")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.1.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.1.1 Mitigation intervention</b>", non_toc_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    measures_text = "Measure to adopt:"
    elements.append(Paragraph(measures_text, bold_style))
    elements.append(Spacer(1, 6))
    
    measures_points = [
        "Awareness on maximum flood height and structural safety (various natural hazards) of residential building",
        "Demonstration units for low-cost resilient housing",
        "Training of local masons for constructing low-cost resilient housing",
        "Incremental approach to convert vulnerable housing to resilient housing",
        "Incorporate resilient standards (specific to district) in housing schemes like PMAY."
    ]
    
    measures_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in measures_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(measures_bullet_items)
    elements.append(Spacer(1, 12))
    
    table_heading = Paragraph("<b>Table 6.2: Estimated investment cost for resilient residential buildings</b>", table_sub_title)
    elements.append(table_heading)
    elements.append(Spacer(1, 6))
    
    housing_cost_data = getResilientHousingCostTable()
    table = create_styled_table(housing_cost_data, [40, 150, 80, 60, 80, 90], False, True, srNoStyle, "Housing Cost")
    elements.append(table)
    elements.append(Spacer(1, 6))
    
    note_text = "Note: Renovation cost considers 30% of construction cost. Renovation or retrofitting include appropriate engineering interventions for roof, wall and foundation."
    elements.append(Paragraph(note_text, notes_style))
    elements.append(Spacer(1, 12))
    
    # 6.2.2 Resilient Roads
    heading = Paragraph("<b>6.2.2 Resilient Roads</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    road_text = "The road typology and length of each road type in the village is provided below."
    elements.append(Paragraph(road_text, normal_style))
    elements.append(Spacer(1, 6))
    
    road_typology_data = getRoadTypologyTable()
    table = create_styled_table(road_typology_data, [40, 120, 80, 120, 140], False, True, srNoStyle, "Road Typology")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.2.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.2.1 Mitigation intervention</b>", blue_level3_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    road_intervention_data = getRoadInterventionTable()
    table = create_styled_table(road_intervention_data, [40, 100, 100, 60, 80, 80, 40], False, True, None, "Road Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.3 River Bank Protection
    heading = Paragraph("<b>6.2.3 River Bank Protection</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    river_bank_data = getRiverBankProtectionTable()
    table = create_styled_table(river_bank_data, [40, 80, 80, 80, 220], False, True, srNoStyle, "River Bank Protection")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.3.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.3.1 Mitigation intervention</b>", blue_level3_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    river_intervention_data = getRiverBankInterventionTable()
    table = create_styled_table(river_intervention_data, [40, 80, 120, 60, 80, 80, 40], False, True, None, "River Bank Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.4 Resilient Essential Services (Educational facilities)
    heading = Paragraph("<b>6.2.4 Resilient Essential Services (Educational facilities)</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    edu_text = "The details of educational facilities in the village and its vulnerability are given below"
    elements.append(Paragraph(edu_text, normal_style))
    elements.append(Spacer(1, 6))
    
    edu_facilities_data = getEducationalFacilitiesTable()
    table = create_styled_table(edu_facilities_data, [40, 100, 70, 70, 70, 75, 75], False, True, srNoStyle, "Educational Facilities")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.4.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.4.1 Mitigation intervention</b>", non_toc_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    edu_intervention_data = getEducationalInterventionTable()
    table = create_styled_table(edu_intervention_data, [30, 80, 90, 50, 70, 70, 110], False, True, None, "Educational Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.5 Resilient Essential Services (Health facilities)
    heading = Paragraph("<b>6.2.5 Resilient Essential Services (Health facilities)</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    health_text = "There is no health facility in the village and community use the private clinic nearby. The access road needs flood proofing through providing adequate drainage."
    elements.append(Paragraph(health_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # 6.2.6 Resilient Essential Services (WASH facilities)
    heading = Paragraph("<b>6.2.6 Resilient Essential Services (WASH facilities)</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # 6.2.6.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.6.1 Mitigation intervention</b>", non_toc_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    wash_intervention_data = getWASHInterventionTable()
    table = create_styled_table(wash_intervention_data, [35, 85, 100, 45, 65, 65, 105], False, True, srNoStyle, "WASH Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.7 Resilient Essential Services (Electric infrastructure)
    heading = Paragraph("<b>6.2.7 Resilient Essential Services (Electric infrastructure)</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # 6.2.7.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.7.1 Mitigation intervention</b>", non_toc_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    electric_intervention_data = getElectricInterventionTable()
    table = create_styled_table(electric_intervention_data, [35, 85, 100, 45, 65, 65, 105], False, True, srNoStyle, "Electric Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 6.2.8 Resilient Livelihoods & Economic Security
    heading = Paragraph("<b>6.2.8 Resilient Livelihoods & Economic Security</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # 6.2.8.1 Mitigation intervention
    sub_heading = Paragraph("<b>6.2.8.1 Mitigation intervention</b>", non_toc_heading)
    elements.append(sub_heading)
    elements.append(Spacer(1, 6))
    
    livelihood_intervention_data = getLivelihoodInterventionTable()
    table = create_styled_table(livelihood_intervention_data, [35, 85, 100, 45, 65, 65, 105], False, True, srNoStyle, "Livelihood Intervention")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Program level intervention
    program_text = "A program level intervention which ideally need to implement across district:"
    elements.append(Paragraph(program_text, bold_style))
    elements.append(Spacer(1, 6))
    
    program_points = [
        "Increase in access to flood tolerant paddy seed varieties at Maximum Retail Price (MRP)",
        "Introduction of cash crops like sesame which can provide high return during rabi season",
        "Mechanisation in agriculture activities including paddy transplanting and harvesting.",
        "Demonstration units for skill development for mechanised farming",
        "Livelihood diversification including Solar drier for farm produce processing, AI based selective breeding of livestock, Distribution of Lichi sapling, Sheep wool collection and aggregating"
    ]
    
    program_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in program_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(program_bullet_items)
    elements.append(Spacer(1, 12))
    
    # 6.3 Policy Intervention to Improve Resilience
    heading = Paragraph("<b>6.3 Policy Intervention to Improve Resilience</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    policy_points = [
        "Define rural land use zones, including a ban on residential construction in wetlands (such as paddy fields), and establish a 500-meter no-construction zone along rivers. Where embankments are constructed, this no-development zone can be reduced to 100 meters. Strict regulations should also be enforced for sand and silt mining, with clearly designated mining zones.",
        "Implement Minimum Support Price (MSP) policies and create an enabling environment for agri-based entrepreneurs to invest in the procurement of crops such as potato, maize, tomatoes, and mustard.",
        "Introduce flood zoning based on a 25-year return period to guide land use planning. Industries, large commercial establishments, and similar infrastructure should be located outside this zone. If essential facilities must be built within the flood zone, they should include adequate flood-proofing measures, such as maintaining a plinth height above the high-water level.",
        "High-investment projects should allocate a 10% contingency buffer for structural strengthening and climate-proofing, to mitigate the potential impacts of climate change."
    ]
    
    policy_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in policy_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(policy_bullet_items)
    elements.append(Spacer(1, 12))
    
    return elements