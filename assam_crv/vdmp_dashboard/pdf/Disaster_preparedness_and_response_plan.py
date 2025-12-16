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


styles = getSampleStyleSheet()

def getTeamMemberList(village_id, team_type):
    try:
        members = TaskForce.objects.filter(village_id=village_id, team_type=team_type)
        data = [
            [Paragraph("S. No.", bold_style), Paragraph("Name", bold_style), Paragraph("Father's Name", bold_style), 
             Paragraph("Gender", bold_style), Paragraph("Phone number", bold_style), Paragraph("Position/Responsibility", bold_style)]
        ]
        
        for i, member in enumerate(members, 1):
            data.append([
                str(i),
                Paragraph(member.fullname or "N/A", normal_style),
                Paragraph(member.father_name or "N/A", normal_style),
                Paragraph(member.gender or "N/A", normal_style),
                Paragraph(member.mobile_number or "N/A", normal_style),
                Paragraph(member.position_responsibility or "Member", normal_style),
            ])
        
        return data
    except Exception:
        return [
            [Paragraph("S. No.", bold_style), Paragraph("Name", bold_style), Paragraph("Father's Name", bold_style), 
             Paragraph("Gender", bold_style), Paragraph("Phone number", bold_style), Paragraph("Position/Responsibility", bold_style)],
            ['1', Paragraph("Sample Name", normal_style), Paragraph("Sample Father", normal_style),
             Paragraph("Male", normal_style), Paragraph("9876543210", normal_style), Paragraph("Team Leader", normal_style)]
        ]

def getVLCDMCMemberList(village_id):
    try:
        members = TaskForce.objects.filter(village_id=village_id, team_type='VLCDMC')
        data = [
            [Paragraph("S. No.", bold_style), Paragraph("Designation", bold_style), Paragraph("Name", bold_style), 
             Paragraph("Name of Father", bold_style), Paragraph("Sex", bold_style), 
             Paragraph("Contact No", bold_style), Paragraph("Occupation", bold_style)]
        ]
        
        for i, member in enumerate(members, 1):
            designation = "Chairperson" if member.position_responsibility == "Team leader" else "Member"
            data.append([
                str(i),
                Paragraph(designation, normal_style),
                Paragraph(member.fullname or "N/A", normal_style),
                Paragraph(member.father_name or "N/A", normal_style),
                Paragraph(member.gender or "N/A", normal_style),
                Paragraph(member.mobile_number or "N/A", normal_style),
                Paragraph(member.occupation or "N/A", normal_style)
            ])
        
        return data
    except Exception:
        return [
            [Paragraph("S. No.", bold_style), Paragraph("Designation", bold_style), Paragraph("Name", bold_style), 
             Paragraph("Name of Father", bold_style), Paragraph("Sex", bold_style), 
             Paragraph("Contact No", bold_style), Paragraph("Occupation", bold_style)],
            ['1', Paragraph("Chairperson", normal_style), Paragraph("Rafiqul Islam", normal_style),
             Paragraph("Kabel Uddin", normal_style), Paragraph("Male", normal_style), 
             Paragraph("8822987100", normal_style), Paragraph("Ex Teacher", normal_style)],
            ['2', Paragraph("Member", normal_style), Paragraph("Sadek Ali", normal_style),
             Paragraph("Hamed Ali", normal_style), Paragraph("Male", normal_style), 
             Paragraph("9678004732", normal_style), Paragraph("GP Member", normal_style)]
        ]

def getSafeShelterData(village_id):
    try:
        # Assuming SafeShelter model exists - adjust model name as needed
        from shelter.models import SafeShelter  # Adjust import as needed
        shelters = SafeShelter.objects.filter(village_id=village_id)
        
        data = [
            [Paragraph("Type of Shelter", bold_style), Paragraph("Rooms", bold_style), 
             Paragraph("Capacity", bold_style), Paragraph("Contact Persons and Phone No.", bold_style), 
             Paragraph("Remarks", bold_style)]
        ]
        
        for shelter in shelters:
            contact_info = f"{shelter.contact_person or 'N/A'}"
            if shelter.contact_designation:
                contact_info += f"<br/>{shelter.contact_designation}"
            if shelter.contact_phone:
                contact_info += f"<br/>Mobile: {shelter.contact_phone}"
                
            data.append([
                Paragraph(shelter.shelter_name or "N/A", normal_style),
                Paragraph(shelter.rooms or "N/A", normal_style),
                Paragraph(shelter.capacity or "N/A", normal_style),
                Paragraph(contact_info, normal_style),
                Paragraph(shelter.remarks or "N/A", normal_style)
            ])
        
        return data
    except Exception:
        # Fallback data if model doesn't exist or error occurs
        return [
            [Paragraph("Type of Shelter", bold_style), Paragraph("Rooms", bold_style), 
             Paragraph("Capacity", bold_style), Paragraph("Contact Persons and Phone No.", bold_style), 
             Paragraph("Remarks", bold_style)],
            [Paragraph("940 LPS School, Rupakuchi", normal_style), Paragraph("04 & Campus Ground", normal_style), 
             Paragraph("50 HH", normal_style), Paragraph("Mr. Tutu Das<br/>Principal,<br/>Mobile: 7002698428", normal_style),
             Paragraph("Village head should coordinate with School in-charge to make sure the school is open in case of any emergency. Has two toilet, handpump for drinking and grid supply for electricity. Suitable only for moderate flood only.", normal_style)]
        ]

def draw_disaster_preparedness_and_response_plan(elements, village_id):
    styles = getSampleStyleSheet()
    heading = Paragraph("<a name='draw_disaster_preparedness_and_response_plan'/><b>5   Disaster Preparedness and Response Plan</b>", blue_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # 5.1 Existing Preparedness Plan
    heading = Paragraph("<b>5.1 Existing Preparedness Plan</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # Early warning table
    early_warning_data = [
        [Paragraph("Sr. No.", bold_style), Paragraph("Nature of early warning", bold_style), Paragraph("Source", bold_style), Paragraph("Lead time", bold_style)],
        [Paragraph("1", normal_style), Paragraph("Location based service of IMD on heavy rainfall/cloud burst/strong wind forecast", normal_style), Paragraph("IMD to all cell phones in the potential impact location", normal_style), Paragraph("3 hours", normal_style)],
        [Paragraph("2", normal_style), Paragraph("Flood forecast", normal_style), Paragraph("DDMA to Circle Officers, Field Officers and Village head", normal_style), Paragraph("48 hours", normal_style)]
    ]
    
    table = create_styled_table(early_warning_data, [40, 180, 180, 100], False, True, srNoStyle, "Early Warning Systems")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Preparedness activities bullet points
    preparedness_points = [
        "Community level awareness activities: Not adequate",
        "DDMA conduct circle level flood preparedness meeting once a year.",
        "SDRF conduct response training in selected locations in the district as per their annual calendar but Rupakuchi was not covered in last 5 years.",
        "Under AIRBMP CRV project in April-May 2025: Village level pre-monsoon camp conducted. The key line departments (Revenue and Disaster Management Department, Agricultural Department, Health Department, Public Health & Engineering Department (PHED), Veterinary Department) explained the precautions and preparedness community should take before flood and during flood. Also, the Revenue and Disaster Management Department explained the entitlement in case affected by flood."
    ]
    
    bullet_items = ListFlowable(
        [ListItem(Paragraph(text,normal_style )) for text in preparedness_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(bullet_items)
    elements.append(Spacer(1, 12))
    
    # 5.2 Disaster Mitigation and Development Plan
    heading = Paragraph("<b>5.2 Disaster Mitigation and Development Plan</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # Mitigation plan table
    mitigation_data = [
        [Paragraph("Sr. No.", bold_style), Paragraph("Work needs to done before the onset of the rainy season", bold_style), Paragraph("Responsibility", bold_style)],
        [Paragraph("1", normal_style), Paragraph("Repair village roads and arrange boats in case of emergency", normal_style), Paragraph("Village Office", normal_style)],
        [Paragraph("2", normal_style), Paragraph("Prune tree branches that are growing across electric lines", normal_style), Paragraph("Assam Power Generation Corporation Ltd(APGCL)", normal_style)],
        [Paragraph("3", normal_style), Paragraph("Inspect river banks and vulnerable locations and coordinate with DDMA to take protection measures", normal_style), Paragraph("Disaster Management Committee (DMC)", normal_style)],
        [Paragraph("4", normal_style), Paragraph("Arrangement of essential items including first aid kits, kerosene for generator, essential food items, drinking water and sanitation facilities in the shelters", normal_style), Paragraph("DMC in coordination with shelter in-charge", normal_style)],
        [Paragraph("5", normal_style), Paragraph("Awareness program at community level and schools", normal_style), Paragraph("DMC in coordination with Asha workers or any local NGOs and school teachers", normal_style)]
    ]
    
    table = create_styled_table(mitigation_data, [40, 300, 160], False, True, srNoStyle, "Disaster Mitigation Plan")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # 5.2.1 Village Land Conservation & Disaster Management Committee
    heading = Paragraph("<b>5.2.1 Village Land Conservation & Disaster Management Committee</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    committee_text = "The village has Village Land Conservation & Disaster Management Committee (VLCDMC) and will function as DMC and Disaster Management Team (DMT) along with selected community members. The details of the VLCDMC members are given below."
    elements.append(Paragraph(committee_text, non_indented_style))
    elements.append(Spacer(1, 12))
    
    # VLCDMC Members table
    vlcdmc_data = getVLCDMCMemberList(village_id)
    table = create_styled_table(vlcdmc_data, [40, 80, 80, 80, 50, 80, 90], False, True, srNoStyle, "VLCDMC Members")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Note about VLCDMC changes
    note_text = "(Note: There will be changes in the VLCDMC members after the Panchayat election and need to update this.)"
    elements.append(Paragraph(note_text, notes_style))
    elements.append(Spacer(1, 12))
    
    # Roles and Responsibilities
    heading = Paragraph("<b>Roles and Responsibilities:</b>", non_toc_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # Normal condition
    normal_heading = Paragraph("<b>Normal condition</b>", bold_style)
    elements.append(normal_heading)
    elements.append(Spacer(1, 6))
    
    normal_points = [
        "Meet on regular basis (monthly) to discuss about the development issues of the village",
        "Help village head to prepare documentation to send to revenue circle/district for any support for addressing development issues of the village",
        "Visit flood vulnerable locations before the rainy season and communicate to DDMA in case there are issues that needs to be addressed",
        "Maintain the list of contact numbers of team members and owners of resources which can be used during emergency situation",
        "Make inventory of vulnerable population in the community and ensure arrangement for support and means for transporting such people in case of emergency",
        "Sensitise community to maintain stock of essential materials and medicines before the start of rainy season.",
        "Urge community to scan and store important documents online or in digilocker."
    ]
    
    normal_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in normal_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(normal_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Warning phase
    warning_heading = Paragraph("<b>Warning phase</b>", bold_style)
    elements.append(warning_heading)
    elements.append(Spacer(1, 6))
    
    warning_points = [
        "Call an emergency meeting of the DMC",
        "Contact designated shelter buildings and make sure essential facilities are available in case of any emergency",
        "Communicate with DDMA in case any support is needed in case of any emergency",
        "Contact DMT and recapitulate their responsibilities",
        "In case of any flood warning received, coordinate with DMT and other teams for evacuation of vulnerable communities and other response activities"
    ]
    
    warning_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in warning_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(warning_bullet_items)
    elements.append(Spacer(1, 12))
    
    # During event
    during_heading = Paragraph("<b>During event</b>", bold_style)
    elements.append(during_heading)
    elements.append(Spacer(1, 6))
    
    during_points = [
        "Stay in contact with the concerned authorities (DDMA, Field Officers) on a continuous basis.",
        "Coordinate with the DMT to minimize life loss and suffering in the community",
        "Coordinate with the Search and Rescue team for immediate deployment",
        "Ensure that the disabled, aged, women are evacuated and sheltered safely"
    ]
    
    during_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in during_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(during_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Post event
    post_heading = Paragraph("<b>Post event</b>", bold_style)
    elements.append(post_heading)
    elements.append(Spacer(1, 6))
    
    post_points = [
        "Need to coordinate with DMTs and various departments on relief and rescue activities",
        "Prepare situation report and share it with district authorities",
        "Support Revenue officials in damage assessment",
        "Facilitate and support officials to disburse relief funds"
    ]
    
    post_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in post_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(post_bullet_items)
    elements.append(Spacer(1, 6))
    
    # 5.2.2 Communication & Warning Dissemination Plan
    heading = Paragraph("<b>5.2.2 Communication & Warning Dissemination Plan</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    comm_text = "The communication and dissemination of early warning will be coordinated by VLCDMC. There are defined roles for the team during different phases as explained below."
    elements.append(Paragraph(comm_text, non_indented_style))
    elements.append(Spacer(1, 12))
    
    # Identified safe shelter
    shelter_heading = Paragraph("<b>Identified safe shelter </b>", non_toc_heading)
    elements.append(shelter_heading)
    elements.append(Spacer(1, 6))
    
    shelter_data = getSafeShelterData(village_id)
    table = create_styled_table(shelter_data, [100, 60, 50, 120, 170], False, True, srNoStyle, "Identified Safe Shelter")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Note about severe flood
    note_text = "Note: In severe flood, community move to Jania and Barpeta Road for shelter."
    elements.append(Paragraph(note_text, notes_style))
    elements.append(Spacer(1, 12))
    
    # Resource planning
    resource_heading = Paragraph("<b>Resource planning</b>", bold_style)
    elements.append(resource_heading)
    elements.append(Spacer(1, 6))
    
    resource_text = "The DMC should arrange boats and other vehicles to transport the communities in case of an emergency and should keep in touch on regular basis with the DDMA to get updates of flood warning."
    elements.append(Paragraph(resource_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # 5.2.3 Disaster Management Team: Search and Rescue Team
    heading = Paragraph("<b>5.2.3 Disaster Management Team: Search and Rescue Team</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    search_rescue_data = getTeamMemberList(village_id, 'Search & rescue')
    table = create_styled_table(search_rescue_data, [40, 100, 100, 60, 100, 100], False, True, srNoStyle, "Search and Rescue Team")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Roles and Responsibilities for Search and Rescue Team
    roles_heading = Paragraph("<b>Roles and Responsibilities :</b>", non_toc_heading)
    elements.append(roles_heading)
    elements.append(Spacer(1, 6))
    
    # Normal condition
    normal_heading = Paragraph("<b>Normal condition</b>", bold_style)
    elements.append(normal_heading)
    elements.append(Spacer(1, 6))
    
    normal_points = [
        "Create cadre of volunteers and acquire training on rescue operations",
        "Participate in the preparation of VDMP and have a clear understanding of vulnerable areas and people at risk in the village",
        "Keep stock of basic equipment (life jacket, life jackets made of local materials like using 2 litre plastic bottle), first aid box and a list of custodians of rescue instruments",
        "Generate awareness among the villagers about various disasters and how to respond in case of any such event",
        "Organize mock drills with the support of DDMA and engaging local community in the procedures.",
        "Identification of safe places for evacuation and shelter."
    ]
    
    normal_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in normal_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(normal_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Warning phase
    warning_heading = Paragraph("<b>Warning phase</b>", bold_style)
    elements.append(warning_heading)
    elements.append(Spacer(1, 6))
    
    warning_points = [
        "Help in evacuation especially vulnerable people (aged, children, destitute, physically challenged)",
        "Keep rescue equipment ready",
        "Coordinate with the DMC for information"
    ]
    
    warning_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in warning_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(warning_bullet_items)
    elements.append(Spacer(1, 12))
    
    # During event
    during_heading = Paragraph("<b>During event</b>", bold_style)
    elements.append(during_heading)
    elements.append(Spacer(1, 6))
    
    during_points = [
        "Give priority to save life over material",
        "Utilize equipment and tools for rescue operations",
        "Operate in a calm and coordinated manner. Don't venture into flood waters without safety guards and equipment",
        "Involve in rescue operations immediately and coordinate with civil defence and SDRF teams"
    ]
    
    during_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in during_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(during_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Post event
    post_heading = Paragraph("<b>Post event</b>", bold_style)
    elements.append(post_heading)
    elements.append(Spacer(1, 6))
    
    post_points = [
        "Try to reach the flood affected locations as quickly as possible to save lives.",
        "Make proper arrangements to shift sick people health centres/hospitals and affected people to designated shelter",
        "Support government and para-medical staff",
        "Support government/ outside (NGO) medical teams to attend sick people and inform them in case affected people needs medical support",
        "Stay connected with other teams",
        "Help people to get back to their homes once it is declared as safe",
        "Establish proper road communication to facilitate the movement of vehicles bringing medicines and relief.",
        "Help other teams in restoring normalcy",
        "Help DMC and Village head in updating the VDMP, if required, based on experience."
    ]
    
    post_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in post_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(post_bullet_items)
    elements.append(Spacer(1, 12))
    
    # 5.2.4 Relief Management Team
    heading = Paragraph("<b>5.2.4 Disaster Management Team: Relief Management Team</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    relief_data = getTeamMemberList(village_id, 'Relief management team')
    table = create_styled_table(relief_data, [40, 100, 100, 60, 100, 100], False, True, srNoStyle, "Relief Management Team")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Relief Management Team Description
    relief_desc = "The Relief Management team comprises both men and women. The team collect relief materials including food supplies, utensils, clothes, kerosene, and diesel. The team coordinate all relief requirements for other teams. Women team members should inquire about the specific needs of the affected women. Gender-sensitive clothes and materials should be distributed to women only by women member in the team. Team members should keep track of all government provisions related to gratuitous relief efforts to prevent starvation, deterioration, and migration. The team should also ensure health and sanitation measures for both people and livestock. Ensures that people do not miss out on their relief entitlements."
    elements.append(Paragraph(relief_desc, normal_style))
    elements.append(Spacer(1, 12))
    
    # Roles and Responsibilities for Relief Management Team
    roles_heading = Paragraph("<b>Roles and Responsibilities</b>", non_toc_heading)
    elements.append(roles_heading)
    elements.append(Spacer(1, 6))
    
    # Normal condition
    normal_heading = Paragraph("<b>Normal condition</b>", bold_style)
    elements.append(normal_heading)
    elements.append(Spacer(1, 6))
    
    normal_points = [
        "Work with VLCDMC to develop comprehensive disaster preparedness and response plans for the community",
        "Identify and organize necessary resources, such as food, water, shelter materials, and medical supplies",
        "Conduct training sessions for volunteers on disaster response and management.",
        "Disseminate information to the community about potential hazards and ways to mitigate risks",
        "Verify and update the household master list for the total number of adults and children. If possible, carry out advance stocking of relief material according to the master list.",
        "Store dry food in accordance with the VLCDMC policy (from government or purchased from community funds)."
    ]
    
    normal_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in normal_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(normal_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Warning phase
    warning_heading = Paragraph("<b>Warning phase</b>", bold_style)
    elements.append(warning_heading)
    elements.append(Spacer(1, 6))
    
    warning_points = [
        "Quickly assess the situation and implement the disaster response plan",
        "Move relief supplies to the respective shelters",
        "Work closely with local authorities, emergency services, and other organizations to ensure a coordinated response",
        "Monitor stocks and make a list of items to be replenished",
        "Coordinate collection of relief supplies from government and NGOs"
    ]
    
    warning_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in warning_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(warning_bullet_items)
    elements.append(Spacer(1, 12))
    
    # During disaster
    during_heading = Paragraph("<b>During disaster</b>", bold_style)
    elements.append(during_heading)
    elements.append(Spacer(1, 6))
    
    during_points = [
        "Conduct needs assessment and ask NGOs and line department as per the requirements of affected community",
        "Ensure timely and equitable distribution of relief materials to affected individuals",
        "Keep track of the ongoing situation and report to higher authorities for further support",
        "Supervise the distribution of safe drinking water and dry food. If possible, organize the cooking and distribution of hot food",
        "Establish contact with block officials/Circle Office by telephone for earliest provisioning of food and relief material, as per the relief entitlement."
    ]
    
    during_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in during_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(during_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Post event
    post_heading = Paragraph("<b>Post event</b>", bold_style)
    elements.append(post_heading)
    elements.append(Spacer(1, 6))
    
    post_points = [
        "Receive and distribute relief material",
        "Replenish stocks that are running low",
        "Collect relief from all sources and distribute to affected people",
        "Ensure officials start the enumeration procedure immediately, so that relief can be arranged through revenue authorities.",
        "Ensure all households receive dry food, relief material, and cattle fodder as per the entitlement.Obtain signatures from household heads in the presence of community leaders",
        "Conduct a social audit through Gram Sabha/VLCDMC regarding distribution of relief materials as soon as possible and document the same."
    ]
    
    post_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in post_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(post_bullet_items)
    elements.append(Spacer(1, 12))
    
    # ------------------------ 5.2.5 Shelter Management Team -----------------------
    heading = Paragraph("<b>5.2.5 Disaster Management Team: Shelter Management Team</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    shelter_mgmt_data = getTeamMemberList(village_id, 'Shelter Management team')
    table = create_styled_table(shelter_mgmt_data, [40, 100, 100, 60, 100, 100], False, True, srNoStyle, "Shelter Management Team")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Roles and Responsibilities for Shelter Management Team
    roles_heading = Paragraph("<b>Roles and Responsibilities</b>", non_toc_heading)
    elements.append(roles_heading)
    elements.append(Spacer(1, 6))
    
    # Normal condition
    normal_heading = Paragraph("<b>Normal condition</b>", bold_style)
    elements.append(normal_heading)
    elements.append(Spacer(1, 6))
    
    normal_points = [
        "Update the list of pregnant women, children, sick people, old and disabled in the village",
        "Educate people on how to use disinfectants/water purifiers to get purified water and maintain good hygiene",
        "Make necessary arrangements to keep proper health and sanitation in the shelters",
        "Visit shelters to ensure that the shelters are in a good condition and have essential facilities including toilet and safe drinking water",
        "Arrange mobile toilet if needed before the rainy season starts",
        "In case temporary toilet are required they need to be made separately for men and women. Special arrangements should be made for pregnant and ailing women",
        "Before the onset of rainy season check the identified shelters in the community, and custodian of the keys for the buildings. Emphasis should be given to see whether the building is in good condition, with electricity, toilets, and safe drinking water."
    ]
    
    normal_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in normal_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(normal_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Warning phase
    warning_heading = Paragraph("<b>Warning phase</b>", bold_style)
    elements.append(warning_heading)
    elements.append(Spacer(1, 6))
    
    warning_points = [
        "Maintain records of available food grains in ration shops and civil supplies outlet",
        "Arrange dry rations, water, medicines, candles, kerosene, and utensils",
        "Arrange for prepositioning of the required items in the shelters and coordinate with the authorities regarding the same",
        "Allocate space for evacuees in the shelters on the basis of gender and special needs",
        "Ensure availability of basic materials including food/water/candles/match boxes and other day to day requirements at least for three days for affected people and livestock coming to shelters"
    ]
    
    warning_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in warning_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(warning_bullet_items)
    elements.append(Spacer(1, 12))
    
    # During event
    during_heading = Paragraph("<b>During event</b>", bold_style)
    elements.append(during_heading)
    elements.append(Spacer(1, 6))
    
    during_points = [
        "Try to accompany rescue teams in getting the victims/sick and ailing people to the shelters",
        "Instruct evacuees to take proper food and safe drinking water",
        "Assure them not to panic. Steps should be taken to console them and counsel affected to be prepared to face the adverse situation",
        "Register the names of the evacuees. If anyone is found missing inform the Search and Rescue Team immediately. Make special arrangements for pregnant women and sick people",
        "The team should strictly maintain health/hygiene in the shelters",
        "Evacuees should be asked to use their own foodstuff first. Ensure there is safe drinking water",
        "Organise community kitchen to provide food and safe drinking water for the evacuees",
        "Emphasis should be given to maintain peace in the shelters, especially people should be motivated /persuaded not to pay heed to any rumours",
        "Rely on authentic media source to know the current situation and future possible threats",
        "Establish contact with other teams and committee"
    ]
    
    during_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in during_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(during_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Post Event
    post_heading = Paragraph("<b>Post Event</b>", bold_style)
    elements.append(post_heading)
    elements.append(Spacer(1, 6))
    
    post_points = [
        "Take proper care to avoid outbreak of epidemics in the community. If any outbreak is noticed, inform the health authority immediately with accurate information regarding the number of affected people and their symptoms",
        "Take proper precaution while support people in the epidemic outbreak area",
        "Provide all the support to affected people in shelter locations till they go back to their homes",
        "Arrange/collect relief items from different sources to maintain buffer stocks",
        "Maintain cleanliness inside and outside the shelters",
        "Make necessary arrangements to provide food and safe drinking water to the people in the shelters",
        "Make necessary arrangements to immediately repair shelters if got damaged during the event",
        "Submit expenditure report, if any, to the Village Panchayat",
        "In case of any casualties dispose the dead body in a safe manner following government procedure, collect details of number of deaths, and coordinate with the DMC to provide victims family with eligible compensation."
    ]
    
    post_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in post_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(post_bullet_items)
    elements.append(Spacer(1, 12))
    
    # --------------------------------- 5.2.6 First Aid Team -----------------------------
    heading = Paragraph("<b>5.2.6 Disaster Management Team: First Aid Team</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    first_aid_data = getTeamMemberList(village_id, 'First Aid team')
    table = create_styled_table(first_aid_data, [40, 100, 100, 60, 100, 100], False, True, srNoStyle, "First Aid Team")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Roles and Responsibilities for First Aid Team
    roles_heading = Paragraph("<b>Roles and Responsibilities</b>", non_toc_heading)
    elements.append(roles_heading)
    elements.append(Spacer(1, 6))
    
    # Normal condition
    normal_heading = Paragraph("<b>Normal condition</b>", bold_style)
    elements.append(normal_heading)
    elements.append(Spacer(1, 6))
    
    normal_points = [
        "Conduct regular training and awareness sessions for the community on basic first aid techniques and emergency response.",
        "Ensure the availability of first aid kits, medical supplies, and emergency equipment.",
        "Organize health awareness camps and mock drills (e.g., CPR, snake bite first aid, etc.) to educate the community on disaster preparedness.",
        "Establish coordination mechanisms with local healthcare personals",
        "Special care to address the needs of vulnerable populations, including children, the elderly, and individuals with disabilities.",
        "Identify and understand the procedure for referral services",
        "Keep contact details of ambulance and boat services for the transportation of ill or injured patients",
        "Ensure the availability of first aid kits (cotton,bandages, and other first aid materials, etc.)."
    ]
    
    normal_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in normal_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(normal_bullet_items)
    elements.append(Spacer(1, 12))
    
    # During event
    during_heading = Paragraph("<b>During event</b>", bold_style)
    elements.append(during_heading)
    elements.append(Spacer(1, 6))
    
    during_points = [
        "Provide immediate first aid and medical assistance to injured individuals",
        "Assess the severity of injuries and stabilize patients for further medical treatment",
        "Assist in the safe evacuation of injured individuals to nearby healthcare facilities",
        "Maintain clear communication with local authorities, healthcare personals, and emergency services for a coordinated response",
        "Continuously monitor the health status of affected individuals and provide necessary relief measures",
        "Move medicine stocks and first aid kits to shelters",
        "Attend to the medical needs of the evacuees",
        "The team must remain indoors when the disaster strikes and ensure that no one leaves the shelter during a disaster, such as a cyclone or flood, under any pretext",
        "Provide medical and counselling support for evacuees, and special care and medical services for vulnerable groups, including women, children, the elderly, and individuals with special needs."
    ]
    
    during_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in during_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(during_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Post event
    post_heading = Paragraph("<b>Post event</b>", bold_style)
    elements.append(post_heading)
    elements.append(Spacer(1, 6))
    
    post_points = [
        "Aid in the rehabilitation of disaster affected individuals by providing follow-up medical care and support",
        "Monitor the community for potential disease outbreaks",
        "Document medical cases and report to health department",
        "Provide psychological support and, counselling to disaster survivors",
        "Collect feedback from the community to improve preparedness and response plans",
        "Attend to the injuries of rescued individuals",
        "Inform the relief group about medical supplies that are running low",
        "Assist doctors and paramedics in transporting the sick and injured to hospitals",
        "Isolate cases with infectious diseases and prevent them from spreading after providing primary care",
        "Provide preventive medication if there is a risk of an epidemic outbreak (such as cholera, dysentery or malaria)."
    ]
    
    post_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in post_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(post_bullet_items)
    elements.append(Spacer(1, 12))
    
    # Individual & Household Preparedness Plan
    preparedness_text = "Each phase requires careful planning, coordination, and execution to ensure the safety and well-being of the community. Below is the Individual & Household Preparedness Plan after the First Warning until the Third Warning:"
    elements.append(Paragraph(preparedness_text, normal_style))
    elements.append(Spacer(1, 6))
    
    preparedness_points = [
        "Ensure each household has a well-equipped first aid kit. Include essential items such as bandages, antiseptics, tweezers, pain relievers, and any prescribed medications",
        "Regularly check and replenish supplies",
        "Store important medical documents, valuables, and cash in a safe container with a lock and key",
        "Keep food items for all household members for 3 days",
        "Ensure safe drinking water is available for 3 days",
        "Have necessary medications available in case of any sick people at home",
        "Pack clothing and undergarments for 3 days",
        "Gather required utensils",
        "Have a radio, torch, sticks, lanterns, matchboxes, and mosquito nets ready",
        "Strengthen the roof and structure of the house",
        "Pack and safely store all household goods (in case the house is likely to be submerged, pack for moving to a safe place)."
    ]
    
    preparedness_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in preparedness_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(preparedness_bullet_items)
    elements.append(Spacer(1, 12))
    
    # --------------------------- 5.2.7 Standard Operating Procedures (SOP) for VLCDMC ----------------------------
    heading = Paragraph("<b>5.2.7 Standard Operating Procedures (SOP) for VLCDMC</b>", blue_level3_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    sop_intro = "Get into action immediately on receiving a flood warning or information about emergency from DDMA. In case the warning came from any other sources, as a first step, call the DDMA/DEOC to confirm the information. Following are the SOPs to follow:"
    elements.append(Paragraph(sop_intro, normal_style))
    elements.append(Spacer(1, 6))
    
    sop_points = [
        "Call an emergency meeting with DMC",
        "Check the early warning system and its dissemination mechanism. Address the identified gaps and ensure effective dissemination of information",
        "Check the shelters and availability of keys of the buildings and ensure essentials are available in the shelters to accommodate affected people and for rescue operation",
        "Inform the DMT and particularly the early warning team to alert the villagers",
        "Hire generators, store kerosene/diesel/petrol for running the generator at the shelter location",
        "Keep a radio with new batteries and smart phones with full charge",
        "Arrange flash lights/torch lights and keep extra batteries for them",
        "Inform the fishermen not to venture for fishing in the river or ponds",
        "Check the flood shelter and store dry food/baby food, safe drinking water, etc.",
        "Check with PHC and other medical institutions in the village to stock medicines, bleaching powder, and halogen tablets. Inform them regarding the warning and request them to be prepared with essential medicines and first aid items.",
        "Keep a copy of the VDMP map ready",
        "Inform ration shops and civil supplies shops about the warning and request them to stock food items",
        "DMC will need to coordinate with respective DMT and ensure that all the team members are alerted and aware of their roles and responsibilities in case of an emergency.",
        "Establish a coordination mechanism with local authorities."
    ]
    
    sop_bullet_items = ListFlowable(
        [ListItem(Paragraph(text, normal_style)) for text in sop_points],
        bulletType='bullet',
        start='•',
        leftIndent=20,
        bulletFontName='Helvetica',
        bulletFontSize=10
    )
    elements.append(sop_bullet_items)
    elements.append(Spacer(1, 12))
    
    # 5.3 Safe Shelter
    heading = Paragraph("<b>5.3 Safe Shelter</b>", blue_sub_heading)
    elements.append(heading)
    elements.append(Spacer(1, 6))
    
    # safe_shelter_data = [
    #     [Paragraph("Shelter", bold_style), Paragraph("Single/Multi stories/Room", bold_style), 
    #      Paragraph("Capacity", bold_style), Paragraph("Contact Persons and Phone No.", bold_style), 
    #      Paragraph("Remarks", bold_style)],
    #     [Paragraph("940, LPS School, Rupakuchi", normal_style), Paragraph("Single/04 Rooms and Campus Space", normal_style),
    #      Paragraph("50 HH", normal_style), Paragraph("Mr. Tutu Das<br/>Principal,<br/>Mobile: 7002698428", normal_style),
    #      Paragraph("Only suitable for moderate flood. Community move to Jania and Barpeta Road for shelter.", normal_style)]
    # ]
    safe_shelter_data = [
        [Paragraph("Shelter", bold_style), Paragraph("Single/Multi stories/Room", bold_style), 
         Paragraph("Capacity", bold_style), Paragraph("Contact Persons and Phone No.", bold_style), 
         Paragraph("Remarks", bold_style)],
        [Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style), Paragraph("-", normal_style),
         Paragraph("-", normal_style)]
    ]
    table = create_styled_table(safe_shelter_data, [100, 80, 50, 120, 150], False, True, srNoStyle, "Safe Shelter")
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    return elements